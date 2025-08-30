import streamlit as st
import folium
import requests
import geopy.distance
import math
import pandas as pd
import altair as alt

# ==============
# CONFIG INICIAL
# ==============
st.set_page_config(page_title="Rotas por Distância – Angola", layout="wide")
st.title("🌍 Rotas por Distância, Clima e Consumo – Angola")

OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "eca1cf11f4133927c8483a28e4ae7a6d")

# =========================
# DADOS DE PROVÍNCIAS (lat/lon)
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

# ===========
# UTILIDADES
# ===========
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def dist_provincias(p1, p2):
    a = provincas[p1]; b = provincas[p2]
    return haversine(a["lat"], a["lon"], b["lat"], b["lon"])

def rota_dist_total(rota):
    total = 0.0
    for i in range(len(rota) - 1):
        total += dist_provincias(rota[i], rota[i+1])
    return total

@st.cache_data(show_spinner=False)
def obter_clima(provincia):
    lat, lon = provincas[provincia]["lat"], provincas[provincia]["lon"]
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt_br"
    try:
        r = requests.get(url, timeout=10).json()
        if r.get("cod") != 200: return None
        clima = r['weather'][0]['description']
        temperatura = r['main']['temp']
        umidade = r['main']['humidity']
        vento = r['wind']['speed']
        icon = r['weather'][0]['icon']
        clima_icon = f"http://openweathermap.org/img/wn/{icon}.png"
        return temperatura, clima, umidade, vento, clima_icon
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def obter_previsao(provincia, pontos=8):
    lat, lon = provincas[provincia]["lat"], provincas[provincia]["lon"]
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt_br"
    try:
        r = requests.get(url, timeout=10).json()
        if 'list' not in r: return None
        previsao = [(item['dt_txt'], item['main']['temp'], item['weather'][0]['description']) for item in r['list'][:pontos]]
        return previsao
    except Exception:
        return None

def estimar_tempo(dist_km, velocidade_kmh):
    h = dist_km / max(velocidade_kmh, 1e-6)
    horas = int(h)
    minutos = int(round((h - horas) * 60))
    return horas, minutos

def estimar_consumo(dist_km, consumo_km_por_l):
    return dist_km / max(consumo_km_por_l, 0.1)

def melhores_rotas_por_distancia(origem, destino, k=3):
    if origem == destino:
        return []
    rotas = [[origem, destino]]
    candidatos_1 = [(rota_dist_total([origem, x, destino]), [origem, x, destino]) for x in provincas.keys() if x not in (origem,destino)]
    if candidatos_1: rotas.append(sorted(candidatos_1,key=lambda t:t[0])[0][1])
    candidatos_2 = [(rota_dist_total([origem,x,y,destino]), [origem,x,y,destino])
                    for x in provincas.keys() if x not in (origem,destino)
                    for y in provincas.keys() if y not in (origem,destino,x)]
    if candidatos_2: rotas.append(sorted(candidatos_2,key=lambda t:t[0])[0][1])
    uniq=[]
    seen=set()
    for r in sorted(rotas,key=lambda rr:rota_dist_total(rr)):
        tup=tuple(r)
        if tup not in seen:
            uniq.append(r)
            seen.add(tup)
        if len(uniq)>=k: break
    return uniq

def desenhar_rota_no_mapa(mapa, rota, cor="blue"):
    pontos = [(provincas[p]["lat"], provincas[p]["lon"]) for p in rota]
    folium.PolyLine(pontos, color=cor, weight=4, opacity=0.9).add_to(mapa)
    for i, p in enumerate(rota):
        cor_m = "green" if i==0 else ("red" if i==len(rota)-1 else "orange")
        folium.Marker([provincas[p]["lat"], provincas[p]["lon"]],
                      popup=f"{'Origem' if i==0 else ('Destino' if i==len(rota)-1 else 'Paragem')} – {p}",
                      icon=folium.Icon(color=cor_m)).add_to(mapa)

# =========
# SIDEBAR
# =========
with st.sidebar:
    st.header("⚙️ Parâmetros")
    velocidade_kmh = st.slider("Velocidade média (km/h)", 30,120,80,5)
    consumo_km_l = st.slider("Consumo do veículo (km/L)",5,20,12,1)
    pontos_previsao = st.slider("Pontos de previsão (3h cada)",4,10,6,1)
    mostrar_3_rotas = st.checkbox("Mostrar até 3 rotas", True)

# ======================
# SELEÇÃO DE PROVÍNCIAS
# ======================
col1, col2 = st.columns(2)
with col1: origem = st.selectbox("Escolha a origem", list(provincas.keys()), index=0)
with col2: destino = st.selectbox("Escolha o destino", list(provincas.keys()), index=1)
if origem==destino: st.error("Selecione províncias diferentes."); st.stop()

# ======================
# CÁLCULO DE ROTAS
# ======================
rotas = melhores_rotas_por_distancia(origem, destino, k=3 if mostrar_3_rotas else 1)

dados_rotas=[]
for idx, rota in enumerate(rotas,start=1):
    d=rota_dist_total(rota)
    h,m=estimar_tempo(d,velocidade_kmh)
    litros=estimar_consumo(d,consumo_km_l)
    dados_rotas.append({"Rota":f"R{idx}: "+" → ".join(rota),
                        "Paragens":len(rota)-2 if len(rota)>2 else 0,
                        "Distância (km)":round(d,1),
                        "Tempo":f"{h}h {m}min",
                        "Consumo (L)":round(litros,1)})
st.subheader("🛣️ Rotas sugeridas por distância total")
st.dataframe(pd.DataFrame(dados_rotas),use_container_width=True)

# ======================
# MAPA COM AS ROTAS
# ======================
st.subheader("🗺️ Mapa das rotas (baseado apenas em distância)")
lat_c = (provincas[origem]["lat"]+provincas[destino]["lat"])/2
lon_c = (provincas[origem]["lon"]+provincas[destino]["lon"])/2
m=folium.Map(location=[lat_c, lon_c], zoom_start=6, control_scale=True)
cores=["blue","green","purple"]
for i, rota in enumerate(rotas): desenhar_rota_no_mapa(m,rota,cor=cores[i%len(cores)])
st.components.v1.html(m._repr_html_(),height=520)

# ======================
# CLIMA + ALERTAS
# ======================
st.subheader("🌦️ Clima atual")
cl1, cl2 = st.columns(2)
for c, prov in zip([cl1, cl2],[origem,destino]):
    with c:
        clima=obter_clima(prov)
        if clima:
            t, desc, um, ven, ic = clima
            st.markdown(f"**{prov}**")
            st.image(ic,width=40)
            st.write(f"Temperatura: {t}°C  •  Clima: {desc}")
            st.write(f"Humidade: {um}%  •  Vento: {ven} m/s")
        else: st.warning(f"Não foi possível obter clima para **{prov}**.")

alertas=[]
for prov in [origem,destino]:
    prev=obter_previsao(prov,pontos=pontos_previsao)
    if prev:
        vai_chover=any(("chuva" in d.lower()) or ("rain" in d.lower()) for _,_,d in prev)
        if vai_chover: alertas.append(f"⚠️ Chuva prevista em **{prov}**. Ajuste sua rota/tempo.")
for a in alertas: st.warning(a)

# ======================
# GRÁFICOS DE PREVISÃO
# ======================
st.subheader("📈 Previsão de temperatura (próximas horas)")
gcol1,gcol2 = st.columns(2)
for c, prov in zip([gcol1,gcol2],[origem,destino]):
    prev=obter_previsao(prov,pontos=pontos_previsao)
    if prev:
        df=pd.DataFrame(prev,columns=["Dia","Temperatura","Descrição"])
        chart=(alt.Chart(df)
               .mark_line(point=True)
               .encode(x=alt.X("Dia:N",title="Hora"),
                       y=alt.Y("Temperatura:Q",title="°C"),
                       tooltip=["Dia","Temperatura","Descrição"])
               .properties(title=f"Temperatura em {prov}"))
        c.altair_chart(chart,use_container_width=True)
    else:
        c.info(f"Sem previsão disponível para **{prov}** no momento.")

st.caption("Rotas calculadas **apenas pela soma das distâncias Haversine** entre paragens. Não representa condições reais de estrada/tráfego.")
