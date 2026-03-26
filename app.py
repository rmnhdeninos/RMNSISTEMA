import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. Configuración de la interfaz
st.set_page_config(page_title="Buscador RMN", page_icon="🏥", layout="centered")

st.title("🏥 Buscador de Pacientes")
st.subheader("Servicio de Diagnóstico por Imágenes - RMN")
st.markdown("---")

# 2. Conexión a la base de datos (Google Sheets)
@st.cache_resource
def conectar_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    skey = st.secrets["gcp_service_account"]
    credentials = Credentials.from_service_account_info(skey, scopes=scopes)
    client = gspread.authorize(credentials)
    return client

# 3. Traer los datos
try:
    cliente = conectar_sheets()
    
    # Reemplaza el texto entre comillas por el link de tu hoja de cálculo
    url_hoja = "https://docs.google.com/spreadsheets/d/1gT3RbP6uZB2buAedGGlTHpVCr600LRzXooZrVOH8Bjs/edit?gid=993245309#gid=993245309"
    
    hoja = cliente.open_by_url(url_hoja).worksheet("Respuestas de formulario 1")
    datos = hoja.get_all_records()
    df = pd.DataFrame(datos)
except Exception as e:
    # Ahora sí veremos el error técnico real si algo falla
    st.error(f"Error técnico al conectar: {e}")
    st.stop()

# 4. Motor de búsqueda
dni_input = st.text_input("Ingrese el DNI del paciente:")

if st.button("Buscar"):
    if dni_input:
        resultado = df[df['DNI / Documento'].astype(str).str.strip() == str(dni_input).strip()]
        
        if not resultado.empty:
            st.success("✅ Paciente encontrado")
            paciente = resultado.iloc[0]
            
            st.info(f"**Nombre y apellido:** {paciente['Nombre y apellido del paciente']}")
            st.write(f"**DNI:** {paciente['DNI / Documento']}")
            st.write(f"**Edad:** {paciente['Edad:']}")
            st.write(f"**Tipo de RMN con anestesia:** {paciente['Tipo de RMN CON ANESTESIA requerida']}")
            st.write(f"**¿Requiere contraste?:** {paciente['¿Requiere contraste?']}")
            st.write(f"**Motivo de anestesia:** {paciente['MOTIVO DE ANESTESIA']}")
        else:
            st.error("❌ No se encontró ningún paciente con el DNI ingresado.")
    else:
        st.warning("⚠️ Por favor, ingrese un DNI válido.")
