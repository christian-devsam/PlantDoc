import streamlit as st
from groq import Groq
import json
import urllib.parse
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Jardín de Sama - PlantaDoc AI",
    page_icon="🧚",
    layout="centered"
)

# --- 2. ESTILO PERSONALIZADO (Diseño Premium Original) ---
st.markdown("""
    <style>
    /* Fondo y tipografía general */
    .stApp {
        background-color: #f0f7f4;
    }
    
    /* Contenedor principal estilizado */
    .main-card {
        background-color: white;
        padding: 2.5rem;
        border-radius: 20px;
        border-left: 8px solid #33c1ba;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Títulos con color del logo */
    h1, h2, h3 {
        color: #2a9d8f !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Botón de análisis con degradado turquesa */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #33c1ba 0%, #2a9d8f 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 50px;
        font-weight: bold;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(51, 193, 186, 0.4);
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(51, 193, 186, 0.6);
    }

    /* Caja de resultados con diseño suave */
    .result-box {
        background-color: #e6f4f1;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #33c1ba;
        margin-bottom: 20px;
    }

    /* Estilo para la encuesta obligatoria */
    .survey-section {
        border: 2px dashed #33c1ba;
        padding: 20px;
        border-radius: 15px;
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIÓN DE ESTADO (MÁQUINA DE PASOS) ---
if 'step' not in st.session_state:
    st.session_state.step = "input"  # Pasos: input -> survey -> final
if 'result_data' not in st.session_state:
    st.session_state.result_data = None

# --- 4. FUNCIONES HELPER ---
def get_plant_diagnosis(plant_type, symptoms, conditions):
    client = Groq(api_key=st.secrets["API_KEY"])
    system_prompt = """
    Eres "PlantaDoc", el experto del Jardín de Sama. 
    Responde en JSON estricto con:
    {"probable_cause": "...", "explanation": "...", "action_plan": ["..."], "suggested_tools": ["..."]}
    """
    user_text = f"Planta: {plant_type}, Síntomas: {symptoms}, Condiciones: {conditions}"
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_text}],
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    return json.loads(chat_completion.choices[0].message.content)

# --- 5. INTERFAZ DE USUARIO ---

# Encabezado
col_logo, col_text = st.columns([1, 3])
with col_logo:
    st.image("jadindesama.jpg", width=120) 
with col_text:
    st.markdown("<h1>Jardín de Sama</h1>", unsafe_allow_html=True)
    st.subheader("PlantaDoc AI: Tu experto botánico")

st.markdown("---")

# PASO 1: Formulario de Diagnóstico
if st.session_state.step == "input":
    with st.container():
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown("### 🌿 Cuéntanos sobre tu planta")
        
        col1, col2 = st.columns(2)
        with col1:
            plant_type = st.text_input("¿Qué planta es?", placeholder="Ej. Orquídea...")
        with col2:
            conditions = st.text_input("¿Dónde vive?", placeholder="Ej. Balcón soleado...")

        symptoms = st.text_area("¿Qué síntomas notas?", placeholder="Describe lo que ves...", height=100)
        
        if st.button("✨ Iniciar Diagnóstico Mágico"):
            if symptoms:
                with st.spinner("Consultando con los espíritus del jardín..."):
                    try:
                        st.session_state.result_data = get_plant_diagnosis(plant_type, symptoms, conditions)
                        st.session_state.step = "survey"
                        st.rerun()
                    except:
                        st.error("🧚 Hubo un problema con la magia. Inténtalo de nuevo.")
            else:
                st.warning("Por favor, describe los síntomas para poder ayudarte.")
        st.markdown('</div>', unsafe_allow_html=True)

# PASO 2: Encuesta Obligatoria (Diseño Integrado)
elif st.session_state.step == "survey":
    res = st.session_state.result_data
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.success("✨ ¡Diagnóstico generado con éxito!")
    st.markdown(f"**Causa detectada inicialmente:** {res.get('probable_cause')}")
    st.write("---")
    
    st.markdown("### 📝 Encuesta Obligatoria")
    st.info("Para desbloquear el **Plan de Acción detallado** y los productos necesarios, ayúdanos con tu opinión:")
    
    with st.form("mandatory_survey"):
        st.markdown('<div class="survey-section">', unsafe_allow_html=True)
        q1 = st.select_slider("¿Qué tan útil te parece la información inicial?", 
                              options=["Poco", "Regular", "Buena", "Muy Buena", "Excelente"])
        q2 = st.radio("¿Comprarías los productos recomendados en nuestra tienda?", ("Sí", "Tal vez", "No"))
        q3 = st.text_input("¿Tienes alguna sugerencia para mejorar PlantaDoc?")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.form_submit_button("Enviar y Ver Solución Completa ✅"):
            st.session_state.step = "final"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# PASO 3: Resultado Final y Plan de Acción
elif st.session_state.step == "final":
    res = st.session_state.result_data
    st.balloons()
    
    with st.container():
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="result-box">
            <h3>🔍 Causa: {res.get('probable_cause')}</h3>
            <p>{res.get('explanation')}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🚑 Plan de acción")
        for step in res.get('action_plan', []):
            st.markdown(f"✅ {step}")

        st.divider()
        
        # Productos y WhatsApp
        tools = res.get('suggested_tools', [])
        tools_str = ', '.join(tools)
        phone = "56931495038"
        msg = f"¡Hola Camila! En PlantaDoc me diagnosticaron {res.get('probable_cause')}. Necesito: {tools_str}."
        url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
        
        st.info(f"**Necesitarás para curarla:** {tools_str}")
        st.markdown(f"""
            <a href="{url}" target="_blank" style="text-decoration: none;">
                <div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold; font-size:1.2rem;">
                    📲 Pedir productos a Camila por WhatsApp
                </div>
            </a>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Realizar otra consulta"):
            st.session_state.step = "input"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
