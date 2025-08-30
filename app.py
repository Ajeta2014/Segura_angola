import streamlit as st
import folium
import requests
import math
import pandas as pd
import altair as alt
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np

# =======================
# CONFIGURAÇÃO INICIAL
# =======================
st.set_page_config(page_title="Rotas Inteligentes – Angola", layout="wide")
st.title("🌍 Rotas Inteligentes: Distância, Clima e Consumo – Angola")

OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "eca1cf11f4133927c8483a28e4ae7a6d")

# =======================
# DADOS DE PROVÍNCIAS
# =======================
provincas = {
    "Luanda": {"lat": -8.839, "lon": 13.234},
    "Benguela": {"lat": -12.649, "lon": 13.421},
    "Lubango": {"lat": -14.917, "lon": 13.499},
    "Huambo": {"lat": -12.783, "lon": 15.741},
    "Malanje": {"lat": -9.525, "lon": 16.340},
    "Lunda Norte": {"lat": -7.406, "lon": 20.391},
    "Lunda Sul": {"lat": -9.310, "lon": 20.462},
    "Cabinda": {"lat": -5.571, "lon": 12.209},
    "Caxito": {"lat": -9.283, "lon": 14.059},
    "Ndalatando": {"lat": -9.117, "lon": 14.905},
    "Sumbe": {"lat": -11.453, "lon": 14.348},
    "Zaire": {"lat": -6.271, "lon": 12.380},
    "Uíge": {"lat": -7.622, "lon": 15.061},
    "Moxico": {"lat": -12.622, "lon": 18.501},
    "Namibe": {"lat": -15.195, "lon": 12.150},
    "Cuito": {"lat": -12.575, "lon": 17.712},
    "Kwanza": {"lat": -9.560, "lon": 14.145},
    "Menongue": {"lat": -15.393, "lon": 18.518},
    "Ondjiva": {"lat": -17.130, "lon": 14.896},
}

# =======================
# FUNÇÕES UTILITÁRIAS
# =======================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2-lat1, lon2-lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2*math.atan2(math.sqrt(a), math.sqrt(1-a))

def dist_provincias(p1, p2):
    a, b = provincas[p1], provincas[p2]
    return haversine(a["lat"], a["lon"], b["lat"], b["lon"])

@st.cache_data
def obter_clima(prov):
    lat, lon = provincas[prov]["lat"], provincas[prov]["lon"]
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt_br"
    r = requests.get(url, timeout=10).json()
    if r.get("cod") != 200: return None
    temp = r['main']['temp']
    desc = r['weather'][0]['description']
    um = r['main']['humidity']
    vento = r['wind']['speed']
    ic = f"http://openweathermap.org/img/wn/{r['weather'][0]['icon']}.png"
    return temp, desc, um, vento, ic

@st.cache_data
def obter_previsao(prov, pontos=6):
    lat, lon = provincas[prov]["lat"], provincas[prov]["lon"]
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt_br"
    r = requests.get(url, timeout=10).json()
    if 'list' not in r: return None
    previsao = [(i['dt_txt'], i['main']['temp'], i['weather'][0]['description']) for i in r['list'][:pontos]]
    return previsao

def estimar_tempo(dist_km, vel_kmh, chuva=False, vento=0):
    h = dist_km / vel_kmh
    # Ajusta tempo se chover ou vento > 10 m/s
    if chuva: h *= 1.2
    if vento > 10: h *= 1.1
    horas = int(h)
    minutos = int(round((h-horas)*60))
    return horas, minutos

def estimar_consumo(dist_km, consumo_km_l, temp=25, vento=0, chuva=False):
    base = dist_km / consumo_km_l
    # Ajusta consumo por clima
    if temp > 30: base *= 1.05
    if chuva: base *= 1.1
    if vento > 10: base *= 1.05
    return round(base,1)

# ======================
# SIDEBAR
# ======================
with st.sidebar:
    st.header("⚙️ Parâmetros")
    vel_media = st.slider("Velocidade média (km/h)", 30, 120, 80, 5)
    consumo_km_l = st.slider("Consumo do veículo (km/L)", 5, 20, 12, 1)
    pontos_prev = st.slider("Pontos de previsão (3h)", 4, 10, 6, 1)

# ======================
# SELEÇÃO DE ORIGEM/DESTINO
# ======================
col1, col2 = st.columns(2)
with col1:
    origem = st.selectbox("Origem", list(provincas.keys()), index=0)
with col2:
    destino = st.selectbox("Destino", list(provincas.keys()), index=1)
if origem==destino: st.error("Selecione províncias diferentes."); st.stop()

# ======================
# ROTAS SIMPLES (baseadas em distância)
# ======================
rotas = [[origem, destino]]

# ======================
# CRIAÇÃO DE TABELA COM DADOS + ML
# ======================
dados = []
for r in rotas:
    dist = dist_provincias(r[0], r[1])
    clima_o = obter_clima(r[0])
    clima_d = obter_clima(r[1])
    chuva = False
    vento = 0
    if clima_o: chuva = "chuva" in clima_o[1].lower(); vento = clima_o[3]
    if clima_d: chuva = chuva or ("chuva" in clima_d[1].lower()); vento = max(vento, clima_d[3])
    h,m = estimar_tempo(dist, vel_media, chuva=chuva, vento=vento)
    litros = estimar_consumo(dist, consumo_km_l, temp=clima_o[0] if clima_o else 25, vento=vento, chuva=chuva)
    dados.append({"Rota": " → ".join(r), "Distância": dist, "Tempo": f"{h}h {m}min", "Consumo(L)": litros, "Chuva": chuva})

df = pd.DataFrame(dados)

st.subheader("🛣️ Rotas e estimativas")
st.dataframe(df, use_container_width=True)

# ======================
# DASHBOARD INTERATIVO
# ======================
st.subheader("📊 Comparação de rotas (Gráficos)")
fig1 = px.bar(df, x="Rota", y="Distância", text="Distância", title="Distância das rotas")
fig2 = px.bar(df, x="Rota", y="Consumo(L)", text="Consumo(L)", title="Consumo estimado")
fig3 = px.bar(df, x="Rota", y="Chuva", text="Chuva", title="Possibilidade de Chuva (0/1)")
st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)

# ======================
# MAPA INTERATIVO
# ======================
st.subheader("🗺️ Mapa")
lat_c = (provincas[origem]["lat"]+provincas[destino]["lat"])/2
lon_c = (provincas[origem]["lon"]+provincas[destino]["lon"])/2
m = folium.Map(location=[lat_c, lon_c], zoom_start=6)
for r in rotas:
    folium.PolyLine([(provincas[p]["lat"], provincas[p]["lon"]) for p in r],
                    color="blue", weight=4, opacity=0.7).add_to(m)
    for i,p in enumerate(r):
        cor = "green" if i==0 else ("red" if i==len(r)-1 else "orange")
        folium.Marker([provincas[p]["lat"], provincas[p]["lon"]],
                      popup=f"{p}", icon=folium.Icon(color=cor)).add_to(m)
st.components.v1.html(m._repr_html_(), height=500)

# ======================
# GRÁFICOS DE PREVISÃO DE TEMPERATURA
# ======================
st.subheader("🌡️ Previsão de temperatura")
col1, col2 = st.columns(2)
for c, prov in zip([col1,col2], [origem,destino]):
    previsao = obter_previsao(prov, pontos=pontos_prev)
    if previsao:
        df_prev = pd.DataFrame(previsao, columns=["Hora","Temp","Desc"])
        chart = alt.Chart(df_prev).mark_line(point=True).encode(
            x="Hora:N", y="Temp:Q", tooltip=["Hora","Temp","Desc"]
        ).properties(title=f"Temperatura em {prov}")
        c.altair_chart(chart, use_container_width=True)
    else:
        c.info(f"Sem previsão para {prov}")
