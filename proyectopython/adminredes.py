import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import socket
import re

st.set_page_config(page_title="Traceroute Visual Pro", layout="wide")
st.title("🌐 Explorador de Rutas de Internet")

# --- FUNCIÓN DE GEOLOCALIZACIÓN ---
def get_geo(ip):
    try:
        if re.match(r"^(192\.168\.|10\.|172\.|127\.)", ip):
            return None
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=3).json()
        if r['status'] == 'success':
            return {
                "IP": ip, "Ciudad": r.get('city'), "País": r.get('country'),
                "ISP": r.get('isp'), "lat": r.get('lat'), "lon": r.get('lon')
            }
    except:
        return None

target = st.text_input("Introduce un dominio o IP:", "google.com")

if st.button("Iniciar Rastreo"):
    with st.spinner("Localizando nodos..."):
        try:
            # Obtener IP del servidor actual (Origen) y del Objetivo (Destino)
            ip_origen = requests.get('https://api.ipify.org').text
            ip_destino = socket.gethostbyname(target)
            
            geo_origen = get_geo(ip_origen)
            geo_destino = get_geo(ip_destino)
            
            puntos = []
            if geo_origen: puntos.append(geo_origen)
            if geo_destino: puntos.append(geo_destino)
            
            if len(puntos) >= 1:
                df = pd.DataFrame(puntos)
                
                # Crear el mapa
                fig = go.Figure()

                # Dibujar línea entre origen y destino
                if len(puntos) > 1:
                    fig.add_trace(go.Scattergeo(
                        lat = [geo_origen['lat'], geo_destino['lat']],
                        lon = [geo_origen['lon'], geo_destino['lon']],
                        mode = 'lines',
                        line = dict(width=2, color='red')
                    ))

                # Dibujar los puntos
                fig.add_trace(go.Scattergeo(
                    lat = df['lat'],
                    lon = df['lon'],
                    mode = 'markers+text',
                    marker = dict(size=10, color='blue'),
                    text = df['Ciudad'],
                    hoverinfo = 'text'
                ))

                fig.update_layout(
                    geo = dict(projection_type = 'natural earth', showcountries = True),
                    margin={"r":0,"t":0,"l":0,"b":0}
                )
                
                st.plotly_chart(fig, use_container_width=True)
                st.subheader("📊 Detalles del Viaje")
                st.table(df[["IP", "Ciudad", "País", "ISP"]])
            else:
                st.error("No se pudo obtener la ubicación de las IPs.")
                
        except Exception as e:
            st.error(f"Error: {e}")

st.info("💡 Nota: En la web, por seguridad, los servidores ocultan los saltos intermedios. Para ver la ruta completa paso a paso, ejecuta este programa en tu computadora local.")
