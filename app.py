import streamlit as st
import folium
import requests
import math
import pandas as pd
import altair as alt
from streamlit_folium import st_folium

# =========================
# CONFIG INICIAL
# =========================
st.set_page_config(page_title="Rotas por Distância – Angola", layout="wide")

# Fundo escuro violeta
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a40;
        color: #f0f0f5;
    }
    .stDataFrame tbody tr th, .stDataFrame tbody tr td {
        color: #f0f0f5;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌍 Rotas por Distância, Clima e Consumo – Angola")

OPENWEATHER_API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "eca1cf11f4133927c8483a28e4ae7a6d")

# =========================
# PROVÍNCIAS
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
# FUNÇÕES
# =========================
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
    for i in range(len(rota)-1):
        total += dist_provincias(rota[i], rota[i+1])
    return total

@st.cache_data
def obter_clima(prov):
    lat, lon = provincas[prov]["lat"], provincas[prov]["lon"]
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt_br"
    try:
        r = requests.get(url, timeout=10).json()
        if r.get("cod") != 200: return None
        clima = r['weather'][0]['description']
        temp = r['main']['temp']
        um = r['main']['humidity']
        vento = r['wind']['speed']
        ic = f"http://openweathermap.org/img/wn/{r['weather'][0]['icon']}.png"
        return temp, clima, um, vento, ic
    except:
        return None

@st.cache_data
def obter_previsao(prov, pontos=8):
    lat, lon = provincas[prov]["lat"], provincas[prov]["lon"]
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=pt_br"
    try:
        r = requests.get(url, timeout=10).json()
        if 'list' not in r: return None
        previsao = [(item['dt_txt'], item['main']['temp'], item['weather'][0]['description']) for item in r['list'][:pontos]]
        return previsao
    except:
        return None

def estimar_tempo(dist_km, vel_kmh):
    h = dist_km / max(vel_kmh, 1e-6)
    return int(h), int(round((h-int(h))*60))

def estimar_consumo(dist_km, cons_km_l):
    return dist_km / max(cons_km_l, 0.1)

def melhores_rotas(origem, destino, k=3):
    if origem==destino: return []
    rotas=[[origem,destino]]
    # 1 paragem
    cand1=[([origem,x,destino], rota_dist_total([origem,x,destino])) for x in provincas.keys() if x not in (origem,destino)]
    if cand1: rotas.append(sorted(cand1,key=lambda t:t[1])[0][0])
    # 2 paragens
    cand2=[([origem,x,y,destino], rota_dist_total([origem,x,y,destino])) for x in provincas.keys() if x not in (origem,destino) for y in provincas.keys() if y not in (origem,destino,x)]
    if cand2: rotas.append(sorted(cand2,key=lambda t:t[1])[0][0])
    uniq=[]
    seen=set()
    for r in sorted(rotas,key=lambda rr:rota_dist_total(rr)):
        tup=tuple(r)
        if tup not in seen:
            uniq.append(r)
            seen.add(tup)
        if len(uniq)>=k: break
    return uniq

def desenhar_rota(mapa, rota, cor="cyan"):
    pontos = [(provincas[p]["lat"], provincas[p]["lon"]) for p in rota]
    folium.PolyLine(pontos, color=cor, weight=6, opacity=0.8).add_to(mapa)
    for i,p in enumerate(rota):
        if i==0:
            ic = "play"  # ícone partida
            col = "green"
        elif i==len(rota)-1:
            ic = "flag"  # ícone destino
            col = "red"
        else:
            ic = "map-marker"
            col = "orange"
        folium.Marker(
            [provincas[p]["lat"], provincas[p]["lon"]],
            popup=f"{p}",
            icon=folium.Icon(icon=ic, prefix="fa", color=col)
        ).add_to(mapa)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("⚙️ Parâmetros")
    vel_media = st.slider("Velocidade média (km/h)",30,120,80,5)
    cons_veic = st.slider("Consumo do veículo (km/L)",5,20,12,1)
    pontos_prev = st.slider("Pontos previsão (3h cada)",4,10,6,1)
    mostrar_3 = st.checkbox("Mostrar até 3 rotas",True)

# =========================
# SELEÇÃO
# =========================
col1,col2 = st.columns(2)
with col1: origem = st.selectbox("Origem",list(provincas.keys()))
with col2: destino = st.selectbox("Destino",list(provincas.keys()))
if origem==destino: st.error("Escolha províncias diferentes."); st.stop()

# =========================
# ROTAS
# =========================
rotas = melhores_rotas(origem,destino,3 if mostrar_3 else 1)
dados=[]
for idx,rota in enumerate(rotas,start=1):
    d = rota_dist_total(rota)
    h,m = estimar_tempo(d,vel_media)
    litros = estimar_consumo(d,cons_veic)
    dados.append({"Rota":f"R{idx}: "+" → ".join(rota),
                  "Paragens":len(rota)-2 if len(rota)>2 else 0,
                  "Distância (km)":round(d,1),
                  "Tempo":f"{h}h {m}min",
                  "Consumo (L)":round(litros,1)})

st.subheader("🛣️ Rotas sugeridas")
st.dataframe(pd.DataFrame(dados),use_container_width=True)

# =========================
# MAPA INTERATIVO
# =========================
st.subheader("🗺️ Mapa interativo das rotas")
lat_c = (provincas[origem]["lat"]+provincas[destino]["lat"])/2
lon_c = (provincas[origem]["lon"]+provincas[destino]["lon"])/2
m = folium.Map(location=[lat_c, lon_c], zoom_start=6, tiles="CartoDB Positron", control_scale=True)  # fundo claro
cores = ["cyan","magenta","orange"]
for i,rota in enumerate(rotas): desenhar_rota(m,rota,cor=cores[i%len(cores)])
st_folium(m,width=800,height=520)

# =========================
# CLIMA
# =========================
st.subheader("🌦️ Clima atual")
cl1,cl2=st.columns(2)
for c,prov in zip([cl1,cl2],[origem,destino]):
    with c:
        clima=obter_clima(prov)
        if clima:
            t,d,um,ven,ic=clima
            st.markdown(f"**{prov}**")
            st.image(ic,width=40)
            st.write(f"Temp: {t}°C • Clima: {d}")
            st.write(f"Humidade: {um}% • Vento: {ven} m/s")
        else:
            st.warning(f"Sem clima para {prov}")

# =========================
# ALERTAS CHUVA
# =========================
alertas=[]
for prov in [origem,destino]:
    prev = obter_previsao(prov,pontos_prev)
    if prev:
        if any("chuva" in d.lower() or "rain" in d.lower() for _,_,d in prev):
            alertas.append(f"⚠️ Chuva prevista em {prov}. Ajuste sua rota/tempo.")
for a in alertas: st.warning(a)

# =========================
# GRÁFICOS
# =========================
st.subheader("📈 Previsão de temperatura")
gcol1,gcol2=st.columns(2)
for c,prov in zip([gcol1,gcol2],[origem,destino]):
    prev=obter_previsao(prov,pontos_prev)
    if prev:
        df=pd.DataFrame(prev,columns=["Hora","Temperatura","Descrição"])
        chart=(alt.Chart(df)
               .mark_line(point=True)
               .encode(x=alt.X("Hora:N",title="Hora"),
                       y=alt.Y("Temperatura:Q",title="°C"),
                       tooltip=["Hora","Temperatura","Descrição"])
               .properties(title=f"Temperatura em {prov}"))
        c.altair_chart(chart,use_container_width=True)
    else:
        c.info(f"Sem previsão disponível para {prov}")

st.caption("Rotas calculadas apenas pela soma das distâncias Haversine. Não representa condições reais de estrada/tráfego.")
