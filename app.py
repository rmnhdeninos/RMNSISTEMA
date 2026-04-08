import streamlit as st
from supabase import create_client, Client
import pandas as pd
import requests
import base64

st.set_page_config(page_title="Sistema RMN", page_icon="🏥", layout="centered")

# ==========================================
# ⚠️ PUENTE DE ARCHIVOS DRIVE
# ==========================================
URL_WEB_APP = "https://script.google.com/macros/s/AKfycbxLVv7aH5gtbnURifmmnZE6kfWCYkzsXeab52h0vve0J9LPmuPIuPQEvuYoE_sNeOzH/exec"
# ==========================================

@st.cache_resource
def iniciar_conexion():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = iniciar_conexion()
    # Traemos todos los registros de la tabla pacientes al instante
    respuesta = supabase.table("pacientes").select("*").execute()
    df = pd.DataFrame(respuesta.data)
except Exception as e:
    st.error(f"Error técnico al conectar a la base de datos: {e}")
    st.stop()

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3004/3004451.png", width=100)
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Seleccione el módulo:", ["Buscador Administrativo", "Carga de Informes (Médicos)"])

# ==========================================
# MÓDULO 1: BUSCADOR ADMINISTRATIVO
# ==========================================
if opcion == "Buscador Administrativo":
    st.title("🏥 Buscador de Pacientes")
    st.markdown("---")
    
    dni_input = st.text_input("Ingrese el DNI del paciente:")

    if st.button("Buscar Paciente"):
        if dni_input:
            resultado = df[df['DNI / Documento'].astype(str).str.strip() == str(dni_input).strip()]
            
            if not resultado.empty:
                st.success("✅ Paciente encontrado")
                paciente = resultado.iloc[0]
                
                st.info(f"**Nombre y apellido:** {paciente.get('Nombre y apellido del paciente', 'No registrado')}")
                st.write(f"**DNI / Documento:** {paciente.get('DNI / Documento', '')}")
                st.write(f"**Edad:** {paciente.get('Edad:', '')}")
                st.write(f"**Peso (kg):** {paciente.get('Peso (kg)', '')}")
                st.write(f"**Altura:** {paciente.get('Altura', '')}")
                st.write(f"**Teléfonos:** {paciente.get('Teléfonos de contacto (familiar del paciente)', '')}")
                
                st.divider()
                st.subheader("👨‍⚕️ Datos de la Solicitud")
                st.write(f"**Solicitado como:** {paciente.get('Solicitado como', '')}")
                st.write(f"**Profesional:** {paciente.get('Nombre del Profesional', '')}")
                st.write(f"**Especialidad:** {paciente.get('Especialidad', '')}")
                st.write(f"**Fecha de carga:** {paciente.get('Marca temporal', '')}")
                
                st.divider()
                st.subheader("🏥 Detalles del Estudio Clínico")
                st.write(f"**Tipo de RMN:** {paciente.get('Tipo de RMN CON ANESTESIA requerida', '')}")
                st.write(f"**Requiere contraste:** {paciente.get('¿Requiere contraste?', '')}")
                st.write(f"**Reacción a contraste:** {paciente.get('¿Antecedentes de reacción a contraste?', '')}")
                st.write(f"**Motivo anestesia:** {paciente.get('MOTIVO DE ANESTESIA', '')}")
                st.write(f"**Diagnóstico:** {paciente.get('DIAGNÓSTICO PRESUNTIVO', '')}")
                st.write(f"**Dispositivos médicos:** {paciente.get('¿Dispositivos médicos?', '')}")
                
                informe = paciente.get('Informe Médico PDF', '')
                if pd.notna(informe) and str(informe).startswith('http'):
                    st.divider()
                    st.success("📄 Este paciente ya cuenta con un informe subido.")
                    st.markdown(f"[Haga clic aquí para ver/descargar el Informe PDF]({informe})")
                
            else:
                st.error("❌ No se encontró ningún paciente con el DNI ingresado.")
        else:
            st.warning("⚠️ Por favor, ingrese un DNI válido.")

# ==========================================
# MÓDULO 2: CARGA DE INFORMES (MÉDICOS)
# ==========================================
elif opcion == "Carga de Informes (Médicos)":
    st.title("🩺 Carga de Informes Médicos")
    st.markdown("---")
    
    dni_medico = st.text_input("Ingrese el DNI del paciente para adjuntar informe:")
    
    if dni_medico:
        resultado = df[df['DNI / Documento'].astype(str).str.strip() == str(dni_medico).strip()]
        
        if not resultado.empty:
            paciente = resultado.iloc[0]
            st.success(f"Paciente seleccionado: **{paciente.get('Nombre y apellido del paciente', 'Desconocido')}**")
            
            archivo_pdf = st.file_uploader("Seleccione el informe en PDF", type=["pdf"])
            
            if archivo_pdf is not None:
                if st.button("Subir y Guardar Informe"):
                    with st.spinner("Subiendo el archivo y vinculando a la base de datos..."):
                        try:
                            # 1. Convertir y enviar al puente (Drive)
                            bytes_pdf = archivo_pdf.getvalue()
                            b64_pdf = base64.b64encode(bytes_pdf).decode('utf-8')
                            nombre_archivo = f"INFORME_{paciente['DNI / Documento']}_{paciente.get('Nombre y apellido del paciente', '')}.pdf"
                            
                            payload = {
                                "fileName": nombre_archivo,
                                "mimeType": "application/pdf",
                                "fileData": b64_pdf
                            }
                            
                            respuesta = requests.post(URL_WEB_APP, data=payload)
                            resultado_json = respuesta.json()
                            
                            if resultado_json.get("status") == "success":
                                link_pdf = resultado_json.get("url")
                                
                                # 2. Actualizar Supabase (La magia SQL)
                                dni_str = str(paciente['DNI / Documento']).strip()
                                supabase.table("pacientes").update({"Informe Médico PDF": link_pdf}).eq("DNI / Documento", dni_str).execute()
                                
                                st.success("✅ ¡Informe guardado en su Drive y vinculado al paciente con éxito!")
                                st.markdown(f"[Ver archivo subido]({link_pdf})")
                            else:
                                st.error(f"Error devuelto por el puente: {resultado_json.get('message')}")
                                
                        except Exception as e:
                            st.error(f"Ocurrió un error general: {e}")
        else:
            st.error("No hay registros para este DNI.")
