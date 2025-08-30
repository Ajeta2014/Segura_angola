import streamlit as st
import folium
import requests
import math
import pandas as pd
import altair as alt
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np

# ======================
# CONFIG INICIAL
# ======================
st.set_page_config(page_title="Rotas Inteligentes – Angola", layout="wide")
st.markdown(
    """
    <style>
    .stApp {background-color: #4b0082; color: white;}
    .stDataFrame div {color: black;}
    </style>
    """,
    unsafe_allow_html=True
)
st.title("🌍 Rotas Inteligentes – Angola")

OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "eca1cf11f4133927c8483a28e4ae7a6d")

# =========================
# DADOS DE PROVÍNCIAS
# =========================
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

# =========================
# FUNÇÕES DE CÁLCULO
# =========================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians,[lat1,lon1,lat2,lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def dist_provincias(p1,p2):
    a,b = provincas[p1],provincas[p2]
    return haversine(a["lat"],a["lon"],b["lat"],b["lon"])

def rota_dist_total(rota):
    return sum([dist_provincias(rota[i],rota[i+1]) for i in range(len(rota)-1)])

# =========================
# CLIMA
# =========================
@st.cache_data
def obter_clima(prov):
    lat,lon = provincas[prov]["lat"],provincas[prov]["lon"]
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt_br"
    r = requests.get(url,timeout=10).json()
    if r.get("cod") != 200: return None
    return (r['main']['temp'], r['weather'][0]['description'], r['main']['humidity'], r['wind']['speed'], r['weather'][0]['icon'])

@st.cache_data
def obter_previsao(prov,pontos=8):
    lat,lon = provincas[prov]["lat"],provincas[prov]["lon"]
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt_br"
    r = requests.get(url,timeout=10).json()
    if 'list' not in r: return None
    return [(i['dt_txt'],i['main']['temp'],i['weather'][0]['description']) for i in r['list'][:pontos]]

# =========================
# ROTAS
# =========================
def melhores_rotas_por_distancia(origem,destino,k=3):
    if origem==destino: return []
    rotas=[[origem,destino]]
    candidatos_1=[(rota_dist_total([origem,x,destino]),[origem,x,destino]) for x in provincas if x not in (origem,destino)]
    if candidatos_1: rotas.append(sorted(candidatos_1,key=lambda t:t[0])[0][1])
    candidatos_2=[(rota_dist_total([origem,x,y,destino]),[origem,x,y,destino])
                  for x in provincas if x not in (origem,destino)
                  for y in provincas if y not in (origem,destino,x)]
    if candidatos_2: rotas.append(sorted(candidatos_2,key=lambda t:t[0])[0][1])
    uniq=[]
    seen=set()
    for r in sorted(rotas,key=lambda rr:rota_dist_total(rr)):
        t=tuple(r)
        if t not in seen: uniq.append(r); seen.add(t)
        if len(uniq)>=k: break
    return uniq

def estimar_consumo_ml(dist,vel,clima_temp):
    """Exemplo ML: consumo aumenta com velocidade e temperatura"""
    X = np.array([[50,20],[80,25],[100,30],[60,22]])
    y = np.array([dist/12, dist/10, dist/9, dist/11])
    model = LinearRegression().fit(X,y)
    return model.predict(np.array([[vel,clima_temp]]))[0]

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("⚙️ Parâmetros")
    vel = st.slider("Velocidade média (km/h)",30,120,80,5)
    consumo = st.slider("Consumo do veículo (km/L)",5,20,12,1)
    pontos_prev = st.slider("Pontos de previsão (3h cada)",4,10,6,1)
    mostrar_3_rotas = st.checkbox("Mostrar até 3 rotas", True)

# =========================
# ESCOLHA DE PROVÍNCIAS
# =========================
col1,col2 = st.columns(2)
with col1: origem=st.selectbox("Origem",list(provincas.keys()),0)
with col2: destino=st.selectbox("Destino",list(provincas.keys()),1)
if origem==destino: st.error("Selecione províncias diferentes."); st.stop()

rotas = melhores_rotas_por_distancia(origem,destino,3 if mostrar_3_rotas else 1)

# =========================
# TABELA INTERATIVA COM PLOTLY
# =========================
dados=[]
for idx,r in enumerate(rotas,1):
    d=rota_dist_total(r)
    temp_clima = obter_clima(origem)[0] if obter_clima(origem) else 25
    litros = estimar_consumo_ml(d,vel,temp_clima)
    dados.append({"Rota":f"R{idx}: "+ " → ".join(r),
                  "Distância":d,"Consumo(L)":litros})
df=pd.DataFrame(dados)
st.subheader("🛣️ Rotas e Consumo Previsto (ML)")
fig = px.bar(df,x="Rota",y="Consumo(L)",color="Distância",text="Consumo(L)",title="Comparativo de Consumo por Rota")
st.plotly_chart(fig,use_container_width=True)

# =========================
# MAPA INTERATIVO
# =========================
st.subheader("🗺️ Mapa das rotas")
lat_c=(provincas[origem]["lat"]+provincas[destino]["lat"])/2
lon_c=(provincas[origem]["lon"]+provincas[destino]["lon"])/2
m = folium.Map(location=[lat_c,lon_c],zoom_start=6)
cores=["blue","green","purple"]
for i,r in enumerate(rotas):
    folium.PolyLine([(provincas[p]["lat"],provincas[p]["lon"]) for p in r],color=cores[i%3],weight=4,opacity=0.9).add_to(m)
st.components.v1.html(m._repr_html_(),height=520)

# =========================
# PREVISÃO CLIMA GRÁFICOS ALTAR
# =========================
st.subheader("📈 Previsão de temperatura")
gcol1,gcol2 = st.columns(2)
for c,prov in zip([gcol1,gcol2],[origem,destino]):
    prev=obter_previsao(prov,pontos_prev)
    if prev:
        df_prev=pd.DataFrame(prev,columns=["Hora","Temperatura","Descrição"])
        chart=(alt.Chart(df_prev)
               .mark_line(point=True)
               .encode(x=alt.X("Hora:N"),y=alt.Y("Temperatura:Q"),tooltip=["Hora","Temperatura","Descrição"])
               .properties(title=f"{prov}"))
        c.altair_chart(chart,use_container_width=True)

st.caption("Consumo calculado via modelo ML baseado em distância, velocidade e temperatura média do clima. Rotas apenas estimativas baseadas em Haversine.")
