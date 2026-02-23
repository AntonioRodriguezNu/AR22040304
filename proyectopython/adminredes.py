import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import subprocess
import re
import platform

# Configuración visual
st.set_page_config(page_title="Traceroute Visual Pro", layout="wide")
st.title("🌐 Explorador de Rutas de Internet")
st.markdown("Analiza los saltos de red y visualiza el viaje de tus datos por el mundo.")

# --- FUNCIÓN DE GEOLOCALIZACIÓN ---
def get_geo(ip):
    try:
        # Ignorar IPs privadas (locales) que no tienen mapa
        if re.match(r"^(192\.168\.|10\.|172\.|127\.)", ip):
            return None
        
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=3).json()
        if r['status'] == 'success':
            return {
                "IP": ip,
                "Ciudad": r.get('city', 'Desconocida'),
                "País": r.get('country', 'Desconocido'),
                "ISP": r.get('isp', 'Desconocido'),
                "lat": r.get('lat'),
                "lon": r.get('lon')
            }
    except:
        return None
    return None

# --- ENTRADA DE USUARIO ---
target = st.text_input("Introduce un dominio (ej. bbc.com, u-tokyo.ac.jp):", "1.1.1.1")

if st.button("Iniciar Rastreo"):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📡 Consola de Red")
        consola = st.empty()
        texto_consola = ""
        
        # Parámetros optimizados para Windows:
        # -d: no resuelve nombres (más rápido)
        # -h 15: máximo 15 saltos
        # -w 200: espera 200ms por respuesta
        cmd = ["tracert", "-d", "-h", "15", "-w", "200", target]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
        
        hops_data = []
        ip_vistas = set()

        for line in process.stdout:
            texto_consola += line
            consola.code(texto_consola) # Muestra el avance en tiempo real
            
            # Buscar IP en la línea
            match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
            if match:
                ip = match.group(1)
                if ip not in ip_vistas:
                    geo = get_geo(ip)
                    if geo:
                        hops_data.append(geo)
                    ip_vistas.add(ip)

    with col2:
        if hops_data:
            df = pd.DataFrame(hops_data)
            
            st.subheader("🗺️ Visualización de Ruta")
            
            # Crear mapa con Plotly Graph Objects para mejor control de líneas
            fig = go.Figure()

            # Añadir las líneas que conectan los puntos
            fig.add_trace(go.Scattergeo(
                lat = df['lat'],
                lon = df['lon'],
                mode = 'lines+markers',
                line = dict(width=2, color='red'),
                marker = dict(size=8, color='blue'),
                text = df['IP'] + " (" + df['Ciudad'] + ")",
                hoverinfo = 'text'
            ))

            fig.update_layout(
                geo = dict(
                    showland = True,
                    landcolor = "rgb(243, 243, 243)",
                    countrycolor = "rgb(204, 204, 204)",
                    projection_type = 'natural earth',
                    showcountries = True
                ),
                margin={"r":0,"t":30,"l":0,"b":0}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📊 Tabla de Detalles")
            st.dataframe(df[["IP", "Ciudad", "País", "ISP"]], use_container_width=True)
        else:
            st.warning("No se detectaron saltos públicos geolocalizables aún.")

# --- PIE DE PÁGINA ---
st.info("Nota: Los saltos que muestran '*' son routers que bloquean paquetes de rastreo por seguridad.")