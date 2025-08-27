import streamlit as st
import math

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
    "Bengo": {"lat": -9.283, "lon": 14.059},
    "Cuanza Norte": {"lat": -9.117, "lon": 14.905},
    "Cuanza Sul": {"lat": -11.453, "lon": 14.348},
    "Zaire": {"lat": -6.271, "lon": 12.380},
    "Uíge": {"lat": -7.622, "lon": 15.061},
    "Moxico": {"lat": -12.622, "lon": 18.501},
    "Namibe": {"lat": -15.195, "lon": 12.150},
    "Bie": {"lat": -12.575, "lon": 17.712},
    "Kwanza": {"lat": -9.560, "lon": 14.145},
    "Cuando Cubango": {"lat": -15.393, "lon": 18.518},
    "Cunene": {"lat": -17.130, "lon": 14.896},
    "Cuanza Sul": {"lat": -11.452, "lon": 14.288},
}

# Função para pegar clima (dados fictícios ou de um banco de dados)
def obter_clima(provincia):
    # Aqui você pode integrar com um banco de dados de clima
    return "Clima: Ensolarado, Temperatura: 28°C"

# Início do aplicativo Streamlit
st.title("Cálculo de Distâncias Interprovinciais de Angola e Clima")

# Escolha das províncias
provincia1 = st.selectbox("Escolha a primeira província", list(provincas.keys()))
provincia2 = st.selectbox("Escolha a segunda província", list(provincas.keys()))

# Coordenadas das províncias
lat1, lon1 = provincas[provincia1]["lat"], provincas[provincia1]["lon"]
lat2, lon2 = provincas[provincia2]["lat"], provincas[provincia2]["lon"]

# Calcular distância
distancia = haversine(lat1, lon1, lat2, lon2)

# Mostrar a distância
st.write(f"A distância entre {provincia1} e {provincia2} é {distancia:.2f} km.")

# Mostrar clima (dados fictícios por enquanto)
clima = obter_clima(provincia1)
st.write(f"O clima atual em {provincia1}: {clima}")

