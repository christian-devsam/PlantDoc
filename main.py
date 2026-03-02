import streamlit as st
from groq import Groq
import json
import urllib.parse
import base64

# --- 1. Configuración de la página ---
st.set_page_config(page_title="Jardín de Sama - PlantaDoc AI", page_icon="🧚")

# --- 2. Estilo Personalizado ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f7f4; }
    .main-card { background: white; padding: 2rem; border-radius: 20px; border-left: 8px solid #33c1ba; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
    .result-box { background-color: #e6f4f1; padding: 20px; border-radius: 15px; border: 1px solid #33c1ba; margin-bottom: 20px; }
    .mandatory-survey { background-color: #fff9e6; padding: 20px; border-radius: 15px; border: 2px dashed #ffcc00; margin-top: 20px; }
    div.stButton > button:first-child { background: linear-gradient(135deg, #33c1ba 0%, #2a9d8f 100%); color: white; border-radius: 50px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Inicialización de Estados ---
if 'step' not in st.session_state:
    st.session_state.step = "input" # Pasos: input -> survey -> final
if 'result_data' not in st.session_state:
    st.session_state.result_data = None

# --- FUNCIONES (Simplificadas para el ejemplo) ---
def get_plant_diagnosis(plant_type, symptoms, conditions):
    # Simulación de llamada a Groq (mantén tu función original aquí)
    client = Groq(api_key=st.secrets["API_KEY"])
    prompt = f"Planta: {plant_type}, Síntomas: {symptoms}. Responde en JSON con probable_cause, explanation, action_plan (lista) y suggested_tools (lista)."
    chat = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    return json.loads(chat.choices[0].message.content)

# --- 4. Interfaz de Usuario ---
st.title("🧚 Jardín de Sama: PlantaDoc")

# PASO 1: Formulario de Entrada
if st.session_state.step == "input":
    with st.container():
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        plant_type = st.text_input("¿Qué planta es?")
        conditions = st.text_input("¿Dónde vive?")
        symptoms = st.text_area("Describe los síntomas")
        if st.button("✨ Analizar Planta"):
            if symptoms:
                with st.spinner("Analizando..."):
                    st.session_state.result_data = get_plant_diagnosis(plant_type, symptoms, conditions)
                    st.session_state.step = "survey"
                    st.rerun()
            else:
                st.warning("Cuéntale al hada qué le pasa a tu planta.")
        st.markdown('</div>', unsafe_allow_html=True)

# PASO 2: Encuesta Obligatoria
elif st.session_state.step == "survey":
    res = st.session_state.result_data
    st.warning("⚠️ **¡Diagnóstico generado!** Para ver los pasos a seguir y contactar a Camila, por favor completa esta breve encuesta.")
    
    # Vista previa limitada
    st.markdown(f"""
    <div class="result-box">
        <h3>🔍 Causa detectada: {res.get('probable_cause')}</h3>
        <p><i>El análisis detallado se desbloqueará al enviar la encuesta.</i></p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("mandatory_survey"):
        st.markdown("### 📝 Encuesta de Satisfacción")
        q1 = st.select_slider("¿Qué tan preciso te parece el diagnóstico inicial?", options=["1", "2", "3", "4", "5"])
        q2 = st.radio("¿Es la primera vez que usas PlantaDoc?", ["Sí", "No"])
        q3 = st.text_area("¿Cómo podemos mejorar?")
        
        if st.form_submit_button("Enviar y Ver Tratamiento ✅"):
            # Aquí guardarías los datos (q1, q2, q3)
            st.session_state.step = "final"
            st.rerun()

# PASO 3: Resultado Completo
elif st.session_state.step == "final":
    res = st.session_state.result_data
    st.balloons()
    st.success("¡Gracias por tu feedback! Aquí tienes el plan completo:")
    
    st.markdown(f"""
    <div class="result-box">
        <h3>🔍 Causa: {res.get('probable_cause')}</h3>
        <p>{res.get('explanation')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🚑 Plan de acción")
    for step in res.get('action_plan', []):
        st.markdown(f"✅ {step}")

    # WhatsApp y Herramientas
    tools_str = ', '.join(res.get('suggested_tools', []))
    phone = "56931495038"
    msg = f"Hola Camila! Mi planta tiene {res.get('probable_cause')}. Necesito: {tools_str}."
    url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
    
    st.info(f"**Necesitarás:** {tools_str}")
    st.markdown(f'<a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">📲 Pedir productos a Camila</div></a>', unsafe_allow_html=True)
    
    if st.button("🔄 Realizar nueva consulta"):
        st.session_state.step = "input"
        st.rerun()
