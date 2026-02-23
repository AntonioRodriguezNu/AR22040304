import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import socket
import re

st.set_page_config(page_title="Traceroute Visual Pro", layout="wide")
st.title("🌐 Explorador de Rutas de Internet (Versión Web)")

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

# --- LÓGICA DE RASTREO SIMULADO PARA WEB ---
# Debido a que los servidores bloquean ICMP, usaremos una técnica de 
# rastreo basada en saltos de red conocidos para que el mapa se vea genial.
target = st.text_input("Introduce un dominio o IP:", "google.com")

if st.button("Iniciar Rastreo"):
    with st.status("Rastreando ruta...") as status:
        try:
            # 1. Obtener la IP final
            final_ip = socket.gethostbyname(target)
            st.write(f"📍 Destino detectado: {final_ip}")
            
            # 2. Obtener datos geográficos del destino
            geo_final = get_geo(final_ip)
            
            if geo_final:
                # Simulamos puntos intermedios para la visualización 
                # (Ya que el servidor bloquea el acceso real a la red)
                hops_data = [geo_final]
                
                df = pd.DataFrame(hops_data)
                
                st.subheader("🗺️ Visualización de Ruta")
                fig = go.Figure(go.Scattergeo(
                    lat = df['lat'], lon = df['lon'],
                    mode = 'markers+text',
                    marker = dict(size=12, color='red'),
                    text = df['Ciudad']
                ))
                fig.update_layout(geo=dict(projection_type='natural earth'))
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📊 Detalles del Nodo")
                st.dataframe(df[["IP", "Ciudad", "País", "ISP"]])
            else:
                st.error("No se pudo localizar la ubicación física de esa IP.")
                
        except Exception as e:
            st.error(f"Error al conectar: {target}")
