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
        # Ignorar IPs privadas (locales) que no tienen ubicación física real
        if re.match(r"^(192\.168\.|10\.|172\.|127\.|169\.254\.)", ip):
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
target = st.text_input("Introduce un dominio o IP (ej. google.com, 1.1.1.1):", "8.8.8.8")

if st.button("Iniciar Rastreo"):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📡 Consola de Red")
        consola = st.empty()
        texto_consola = ""
        
        # DETECCIÓN DE SISTEMA OPERATIVO
        sistema = platform.system()
        
        if sistema == "Windows":
            # Comando optimizado para Windows
            cmd = ["tracert", "-d", "-h", "15", "-w", "200", target]
        else:
            # Comando optimizado para Linux (Streamlit Cloud)
            # -n: sin DNS, -m: saltos máx, -w: espera, -q: 1 intento por salto para rapidez
            cmd = ["traceroute", "-n", "-m", "15", "-w", "1", "-q", "1", target]
        
        try:
            # Ejecutamos el subproceso
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                shell=(sistema == "Windows")
            )
            
            hops_data = []
            ip_vistas = set()

            # Leemos la salida línea por línea en tiempo real
            for line in process.stdout:
                texto_consola += line
                consola.code(texto_consola) 
                
                # Extraer IP usando expresiones regulares
                match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                if match:
                    ip = match.group(1)
                    if ip not in ip_vistas:
                        geo = get_geo(ip)
                        if geo:
                            hops_data.append(geo)
                        ip_vistas.add(ip)
                        
        except Exception as e:
            st.error(f"Error al ejecutar el comando: {e}")

    with col2:
        if hops_data:
            df = pd.DataFrame(hops_data)
            
            st.subheader("🗺️ Visualización de Ruta")
            
            fig = go.Figure()

            # Dibujar líneas y marcadores
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
            st.warning("No se detectaron saltos públicos para el mapa. Prueba con un sitio internacional como 'www.ox.ac.uk'.")

st.info("Nota: En la nube (Linux), si el comando 'traceroute' no está instalado en el servidor, verás un error de 'not found'.")
