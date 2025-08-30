import streamlit as st
import math
import requests
import folium
import pandas as pd
import altair as alt

# Função Haversine para calcular distância em km
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Raio da Terra
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2-lat1, lon2-lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2*math.atan2(math.sqrt(a), math.sqrt(1-a))

# Função para obter clima atual
@st.cache_data
def obter_clima(provincia):
    api_key = "eca1cf11f4133927c8483a28e4ae7a6d"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={provincia},AO&appid={api_key}&units=metric"
    data = requests.get(url).json()
    if data.get("cod") != 200: return None
    clima = data['weather'][0]['description']
    temperatura = data['main']['temp']
    umidade = data['main']['humidity']
    vento = data['wind']['speed']
    clima_icon = f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}.png"
    return temperatura, clima, umidade, vento, clima_icon

# Função para obter previsão de clima
@st.cache_data
def obter_previsao(provincia):
    api_key = "eca1cf11f4133927c8483a28e4ae7a6d"
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={provincia},AO&appid={api_key}&units=metric"
    data = requests.get(url).json()
    if 'list' not in data: return None
    previsao = [(item['dt_txt'], item['main']['temp'], item['weather'][0]['description']) for item in data['list'][:5]]
    return previsao

# Função para criar mapa interativo
@st.cache_data
def criar_mapa(lat1, lon1, lat2, lon2, provincia1, provincia2):
    m = folium.Map(location=[lat1, lon1], zoom_start=6)
    folium.Marker([lat1, lon1], popup=provincia1, icon=folium.Icon(color='blue')).add_to(m)
    folium.Marker([lat2, lon2], popup=provincia2, icon=folium.Icon(color='red')).add_to(m)
    folium.PolyLine([(lat1, lon1), (lat2, lon2)], color="green", weight=2.5, opacity=1).add_to(m)
    return m

# Coordenadas das províncias de Angola
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

st.title("🌍 Rota, Clima e Consumo de Combustível em Angola")

# Seleção de províncias
col1, col2 = st.columns(2)
with col1:
    provincia1 = st.selectbox("Escolha a primeira província", list(provincas.keys()))
with col2:
    provincia2 = st.selectbox("Escolha a segunda província", list(provincas.keys()))

if provincia1 == provincia2:
    st.error("Selecione duas províncias diferentes!")
else:
    lat1, lon1 = provincas[provincia1]["lat"], provincas[provincia1]["lon"]
    lat2, lon2 = provincas[provincia2]["lat"], provincas[provincia2]["lon"]

    # Distância e tempo estimado
    distancia = haversine(lat1, lon1, lat2, lon2)
    st.write(f"📏 Distância: {distancia:.2f} km")
    tempo_estimado = distancia/80
    st.write(f"⏱ Tempo estimado: {int(tempo_estimado)}h {int((tempo_estimado-int(tempo_estimado))*60)}min")

    # Estimativa de combustível
    consumo_medio = 12  # km/l
    litros_necessarios = distancia / consumo_medio
    st.info(f"⛽ Estimativa de combustível necessário: {litros_necessarios:.2f} litros")

    # Clima atual
    clima1, clima2 = obter_clima(provincia1), obter_clima(provincia2)
    for prov, clima in zip([provincia1, provincia2], [clima1, clima2]):
        if clima:
            st.subheader(f"Clima em {prov}")
            st.write(f"🌡 Temperatura: {clima[0]}°C | 💧 Umidade: {clima[2]}% | 🌬 Vento: {clima[3]} m/s")
            st.image(clima[4], width=50)
        else:
            st.write(f"Não foi possível obter clima para {prov}")

    # Alertas automáticos
    alertas = []
    for prov, clima in zip([provincia1, provincia2], [clima1, clima2]):
        if clima and 'chuva' in clima[1].lower():
            alertas.append(f"⚠️ Pode chover em {prov} hoje. Possíveis atrasos na rota!")
    for alerta in alertas: st.warning(alerta)

    # Previsão 5 dias com gráfico
    for prov, previsao in zip([provincia1, provincia2], [obter_previsao(provincia1), obter_previsao(provincia2)]):
        if previsao:
            st.subheader(f"Previsão 5 dias em {prov}")
            df = pd.DataFrame(previsao, columns=['Dia','Temperatura','Descrição'])
            chart = alt.Chart(df).mark_line(point=True).encode(
                x='Dia', y='Temperatura', tooltip=['Dia','Temperatura','Descrição']
            ).properties(title=f"Temperatura em {prov}")
            st.altair_chart(chart, use_container_width=True)

    # Mapa com rota
    st.subheader("🗺 Rota entre províncias")
    m = criar_mapa(lat1, lon1, lat2, lon2, provincia1, provincia2)
    st.components.v1.html(m._repr_html_(), height=500)


