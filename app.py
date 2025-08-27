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
