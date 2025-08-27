import streamlit as st
import math
import requests
import folium
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random

# Função de Haversine para calcular a distância em quilômetros
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Raio da Terra em km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])  # Convertendo de graus para radianos

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distância em km
    return R * c

# Função para pegar clima da API OpenWeatherMap
@st.cache_data
def obter_clima(provincia):
    api_key = "eca1cf11f4133927c8483a28e4ae7a6d"  # Substitua com a sua chave da OpenWeatherMap
    url = f"http://api.openweathermap.org/data/2.5/weather?q={provincia},AO&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()

    if data.get("cod") != 200:
        return None
    clima = data['weather'][0]['description']
    temperatura = data['main']['temp']
    umidade = data['main']['humidity']
    vento = data['wind']['speed']
    clima_icon = f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}.png"  # Icon do clima
    return temperatura, clima, umidade, vento, clima_icon

# Função para criar o mapa interativo
@st.cache_data
def criar_mapa(lat1, lon1, lat2, lon2, provincia1, provincia2):
    m = folium.Map(location=[lat1, lon1], zoom_start=6)
    folium.Marker([lat1, lon1], popup=provincia1, icon=folium.Icon(color='blue')).add_to(m)
    folium.Marker([lat2, lon2], popup=provincia2, icon=folium.Icon(color='red')).add_to(m)
    folium.PolyLine([(lat1, lon1), (lat2, lon2)], color="green", weight=2.5, opacity=1).add_to(m)
    return m

# Simulação de um banco de dados para eventos
eventos_reportados = []

# Função para reportar um evento
def reportar_evento(tipo, provincia, descricao):
    evento = {
        'id': random.randint(1000, 9999),
        'tipo': tipo,
        'provincia': provincia,
        'descricao': descricao,
        'data': datetime.now(),
        'resolvido': False,
    }
    eventos_reportados.append(evento)
    st.success(f"Evento {tipo} reportado com sucesso!")

# Função para exibir eventos
def exibir_eventos():
    for evento in eventos_reportados:
        if not evento['resolvido']:
            st.write(f"**{evento['tipo']}** em {evento['provincia']}")
            st.write(f"Descrição: {evento['descricao']}")
            st.write(f"Data do evento: {evento['data'].strftime('%d/%m/%Y %H:%M')}")
            st.write("----")

# Função para resolver um evento
def resolver_evento(id_evento, senha_admin):
    if senha_admin == "admin123":  # Palavra-passe para resolver
        for evento in eventos_reportados:
            if evento['id'] == id_evento:
                evento['resolvido'] = True
                st.success(f"Evento {id_evento} resolvido com sucesso!")
                break
    else:
        st.error("Senha incorreta! Não é possível resolver o evento.")

# Exibição de eventos expirados
def remover_eventos_expirados():
    global eventos_reportados
    agora = datetime.now()
    eventos_reportados = [evento for evento in eventos_reportados if agora - evento['data'] < timedelta(hours=72)]

# Dicionário de coordenadas das províncias de Angola
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

# Início do aplicativo Streamlit
st.title("Cálculo de Distâncias e Clima em Angola")

# Painel de relatórios
st.sidebar.header("Relatar Evento")
evento_tipo = st.sidebar.selectbox("Tipo de evento", ["Acidente", "Buraco", "Congestionamento", "Outro"])
evento_provincia = st.sidebar.selectbox("Escolha a província", list(provincas.keys()))
evento_descricao = st.sidebar.text_area("Descrição do evento", "")

if st.sidebar.button("Reportar Evento"):
    if evento_descricao:
        reportar_evento(evento_tipo, evento_provincia, evento_descricao)
    else:
        st.error("Por favor, insira uma descrição para o evento.")

# Painel Administrativo
st.sidebar.header("Administração")
senha_admin = st.sidebar.text_input("Senha Administrador", type="password")
id_evento_resolver = st.sidebar.number_input("ID do Evento para Resolver", min_value=1000, max_value=9999, step=1)
if st.sidebar.button("Resolver Evento"):
    resolver_evento(id_evento_resolver, senha_admin)

# Remover eventos expirados (após 72 horas)
remover_eventos_expirados()

# Exibir eventos reportados
st.subheader("Eventos Reportados")
exibir_eventos()

# O resto do seu código original...
# Escolha das províncias (usando colunas para tornar a interface mais organizada)
col1, col2 = st.columns(2)
with col1:
    provincia1 = st.selectbox("Escolha a primeira província", list(provincas.keys()))
with col2:
    provincia2 = st.selectbox("Escolha a segunda província", list(provincas.keys()))

# Validação: Não pode escolher a mesma província
if provincia1 == provincia2:
    st.error("Por favor, selecione duas províncias diferentes.")
else:
    # Coordenadas das províncias
    lat1, lon1 = provincas[provincia1]["lat"], provincas[provincia1]["lon"]
    lat2, lon2 = provincas[provincia2]["lat"], provincas[provincia2]["lon"]

    # Calcular distância
    distancia = haversine(lat1, lon1, lat2, lon2)

    # Exibir distância
    st.write(f"A distância entre {provincia1} e {provincia2} é {distancia:.2f} km.")

    # Estimativa de tempo de viagem (considerando uma velocidade média de 80 km/h)
    tempo_estimado = distancia / 80
    horas = int(tempo_estimado)
    minutos = int((tempo_estimado - horas) * 60)
    st.write(f"Tempo estimado de viagem: {horas} horas e {minutos} minutos.")

    # Obter as condições climáticas para as províncias
    clima1 = obter_clima(provincia1)
    clima2 = obter_clima(provincia2)

    # Exibir clima de cada província
    if clima1:
        st.subheader(f"Clima atual em {provincia1}")
        st.write(f"Temperatura: {clima1[0]}°C")
        st.write(f"Clima: {clima1[1]}")
        st.write(f"Umidade: {clima1[2]}%")
        st.write(f"Velocidade do vento: {clima1[3]} m/s")
        st.image(clima1[4], width=50)  # Exibir o ícone do clima
    else:
        st.write(f"Não foi possível obter as condições climáticas para {provincia1}")

    if clima2:
        st.subheader(f"Clima atual em {provincia2}")
        st.write(f"Temperatura: {clima2[0]}°C")
        st.write(f"Clima: {clima2[1]}")
        st.write(f"Umidade: {clima2[2]}%")
        st.write(f"Velocidade do vento: {clima2[3]} m/s")
        st.image(clima2[4], width=50)  # Exibir o ícone do clima
    else:
        st.write(f"Não foi possível obter as condições climáticas para {provincia2}")

    # Obter previsões para os próximos 5 dias
    previsao1 = obter_previsao(provincia1)
    previsao2 = obter_previsao(provincia2)

    if previsao1:
        st.subheader(f"Previsão de clima para os próximos 5 dias em {provincia1}")
        for dia, temp, descricao in previsao1:
            st.write(f"{dia}: {temp}°C - {descricao}")
    else:
        st.write(f"Não foi possível obter a previsão para {provincia1}")

    if previsao2:
        st.subheader(f"Previsão de clima para os próximos 5 dias em {provincia2}")
        for dia, temp, descricao in previsao2:
            st.write(f"{dia}: {temp}°C - {descricao}")
    else:
        st.write(f"Não foi possível obter a previsão para {provincia2}")

    # Criar o mapa com a rota entre as províncias
    m = criar_mapa(lat1, lon1, lat2, lon2, provincia1, provincia2)

    # Exibir o mapa no Streamlit
    st.subheader("Rota entre as províncias:")
    st.components.v1.html(m._repr_html_(), height=500)
