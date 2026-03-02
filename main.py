import streamlit as st
from groq import Groq
import json
import urllib.parse
import base64
import pandas as pd
from datetime import datetime
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Jardín de Sama - PlantaDoc AI",
    page_icon="🧚",
    layout="centered"
)

# --- 2. ESTILO PERSONALIZADO (Diseño Premium) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f7f4; }
    .main-card {
        background-color: white;
        padding: 2.5rem;
        border-radius: 20px;
        border-left: 8px solid #33c1ba;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #2a9d8f !important; font-family: 'Helvetica Neue', sans-serif; }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #33c1ba 0%, #2a9d8f 100%);
        color: white; border: none; padding: 15px 30px;
        border-radius: 50px; font-weight: bold; width: 100%;
        transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(51, 193, 186, 0.4);
    }
    .result-box {
        background-color: #e6f4f1;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #33c1ba;
        margin-bottom: 20px;
    }
    .survey-section {
        border: 2px dashed #33c1ba;
        padding: 20px;
        border-radius: 15px;
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIÓN DE ESTADO Y ARCHIVOS ---
if 'step' not in st.session_state:
    st.session_state.step = "input"
if 'result_data' not in st.session_state:
    st.session_state.result_data = None

def guardar_datos_encuesta(p_type, rating, useful, comment):
    """Guarda las respuestas en un archivo CSV local"""
    file_path = 'reporte_encuestas.csv'
    nueva_fila = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Planta": p_type,
        "Calificacion": rating,
        "Interes_Compra": useful,
        "Comentario": comment
    }
    df = pd.DataFrame([nueva_fila])
    if not os.path.isfile(file_path):
        df.to_csv(file_path, index=False)
    else:
        df.to_csv(file_path, mode='a', header=False, index=False)

# --- 4. FUNCIÓN DE DIAGNÓSTICO ---
def get_plant_diagnosis(plant_type, symptoms, conditions):
    client = Groq(api_key=st.secrets["API_KEY"])
    system_prompt = 'Eres "PlantaDoc". Responde en JSON: {"probable_cause": "...", "explanation": "...", "action_plan": ["..."], "suggested_tools": ["..."]}'
    user_text = f"Planta: {plant_type}, Síntomas: {symptoms}, Condiciones: {conditions}"
    
    chat = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    return json.loads(chat.choices[0].message.content)

# --- 5. INTERFAZ DE USUARIO ---

# Encabezado
st.markdown("<h1>🧚 Jardín de Sama</h1>", unsafe_allow_html=True)
st.subheader("PlantaDoc AI: Tu experto botánico")

# PASO 1: Formulario
if st.session_state.step == "input":
    with st.container():
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 🌿 Cuéntanos sobre tu planta")
        col1, col2 = st.columns(2)
        with col1:
            p_name = st.text_input("¿Qué planta es?", key="p_name")
        with col2:
            p_cond = st.text_input("¿Dónde vive?", key="p_cond")
        p_symp = st.text_area("¿Qué síntomas notas?", height=100)
        
        if st.button("✨ Iniciar Diagnóstico Mágico"):
            if p_symp:
                with st.spinner("Consultando con los espíritus del jardín..."):
                    st.session_state.result_data = get_plant_diagnosis(p_name, p_symp, p_cond)
                    st.session_state.current_plant = p_name
                    st.session_state.step = "survey"
                    st.rerun()
            else:
                st.warning("Describe los síntomas para continuar.")
        st.markdown('</div>', unsafe_allow_html=True)

# PASO 2: Encuesta Obligatoria
elif st.session_state.step == "survey":
    res = st.session_state.result_data
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.success("✨ ¡Diagnóstico generado!")
    st.markdown(f"**Análisis preliminar:** {res.get('probable_cause')}")
    st.divider()
    
    st.markdown("### 📝 Encuesta de Satisfacción")
    st.info("Completa esto para desbloquear el plan de acción detallado:")
    
    with st.form("survey_form"):
        st.markdown('<div class="survey-section">', unsafe_allow_html=True)
        q1 = st.select_slider("¿Qué tan preciso parece el diagnóstico?", options=["1", "2", "3", "4", "5"])
        q2 = st.radio("¿Comprarías los productos recomendados aquí?", ("Sí", "Tal vez", "No"))
        q3 = st.text_input("¿Cómo podemos mejorar?")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.form_submit_button("Enviar y Desbloquear Solución ✅"):
            guardar_datos_encuesta(st.session_state.current_plant, q1, q2, q3)
            st.session_state.step = "final"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# PASO 3: Resultado Final
elif st.session_state.step == "final":
    res = st.session_state.result_data
    st.balloons()
    with st.container():
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="result-box"><h3>🔍 Causa: {res.get("probable_cause")}</h3><p>{res.get("explanation")}</p></div>', unsafe_allow_html=True)
        
        st.markdown("### 🚑 Plan de acción")
        for step in res.get('action_plan', []):
            st.markdown(f"✅ {step}")
        
        tools_str = ', '.join(res.get('suggested_tools', []))
        url = f"https://wa.me/56931495038?text=Hola%20Camila!%20En%20PlantaDoc%20mi%20planta%20tiene%20{res.get('probable_cause')}.%20Necesito:%20{tools_str}"
        
        st.info(f"**Necesitarás:** {tools_str}")
        st.markdown(f'<br><a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">📲 Pedir productos a Camila</div></a>', unsafe_allow_html=True)
        
        if st.button("🔄 Nueva Consulta"):
            st.session_state.step = "input"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
