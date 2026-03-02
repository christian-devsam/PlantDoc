import streamlit as st
from groq import Groq
import json
import urllib.parse
import base64

# --- 1. Configuración de la página ---
st.set_page_config(
    page_title="Jardín de Sama - PlantaDoc AI",
    page_icon="🧚",
    layout="centered"
)

# --- 2. Estilo Personalizado (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f7f4; }
    .main-card {
        background-color: white;
        padding: 2rem;
        border-radius: 20px;
        border-left: 8px solid #33c1ba;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
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
    /* Estilo para la encuesta */
    .survey-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border: 1px dashed #2a9d8f;
        margin-top: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Configuración de la API Key ---
try:
    api_key = st.secrets["API_KEY"]
    client = Groq(api_key=api_key)
except Exception as e:
    st.error("Error: No se encontró la API_KEY en secrets.")
    client = None

# --- FUNCIONES HELPER ---
def encode_image(uploaded_file):
    if uploaded_file is not None:
        try:
            return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        except Exception as e:
            st.error(f"Error al procesar la imagen: {e}")
            return None
    return None

def get_plant_diagnosis(plant_type, symptoms, conditions, image_base64=None):
    VISION_MODEL_ID = "llama-3.2-90b-vision-preview"
    TEXT_MODEL_ID = "llama-3.3-70b-versatile"

    system_prompt = """
    Eres "PlantaDoc", el asistente experto del 'Jardín de Sama'. 
    Tu tono es amable, mágico y profesional.
    Responde en JSON estricto:
    {
        "is_plant_related": true,
        "probable_cause": "Causa breve",
        "explanation": "Explicación detallada",
        "action_plan": ["Paso 1", "Paso 2"],
        "suggested_tools": ["Producto A", "Herramienta B"]
    }
    """
    user_text = f"Planta: {plant_type}, Síntomas: {symptoms}, Condiciones: {conditions}"
    
    if image_base64:
        try:
            messages_vision = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]}
            ]
            chat_completion = client.chat.completions.create(
                messages=messages_vision, model=VISION_MODEL_ID,
                temperature=0.2, response_format={"type": "json_object"}
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception:
            pass

    messages_text = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]
    chat_completion = client.chat.completions.create(
        messages=messages_text, model=TEXT_MODEL_ID,
        temperature=0.2, response_format={"type": "json_object"}
    )
    return json.loads(chat_completion.choices[0].message.content)

# --- 4. Interfaz de Usuario ---
col_logo, col_text = st.columns([1, 2])
with col_logo:
    st.image("jadindesama.jpg", width=150) 
with col_text:
    st.title("Jardín de Sama")
    st.subheader("PlantaDoc AI: Tu experto botánico")

st.markdown("---")

# Inicializar estado para controlar si se mostró el resultado
if 'diagnosis_ready' not in st.session_state:
    st.session_state.diagnosis_ready = False
    st.session_state.result_data = None

with st.container():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown("### 🌿 Cuéntanos sobre tu planta")
    
    col1, col2 = st.columns(2)
    with col1:
        plant_type = st.text_input("¿Qué planta es?", placeholder="Ej. Orquídea...")
    with col2:
        conditions = st.text_input("¿Dónde vive?", placeholder="Ej. Balcón...")

    st.markdown("#### 📸 Sube una foto (Recomendado)")
    uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Imagen para análisis", width=300)

    symptoms = st.text_area("¿Qué síntomas notas?", placeholder="Ej. Manchas amarillas...", height=100)
    
    submitted = st.button("✨ Iniciar Diagnóstico Mágico")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. Procesamiento y Resultados ---
if submitted:
    if not symptoms and not uploaded_file:
        st.warning("🧚 Por favor, describe el problema o sube una foto.")
    else:
        with st.spinner("Consultando con los espíritus del jardín..."):
            img_data = encode_image(uploaded_file)
            result = get_plant_diagnosis(plant_type, symptoms, conditions, image_base64=img_data)
            
            if result.get("is_plant_related") is False:
                st.error("🚫 Lo siento, solo puedo ayudarte con plantas.")
            else:
                st.session_state.diagnosis_ready = True
                st.session_state.result_data = result

# Mostrar Resultados y Encuesta si el diagnóstico está listo
if st.session_state.diagnosis_ready:
    res = st.session_state.result_data
    st.balloons()
    
    st.markdown(f"""
    <div class="result-box">
        <h3>🔍 Causa: {res.get('probable_cause')}</h3>
        <p>{res.get('explanation')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🚑 Plan de acción")
    for step in res.get('action_plan', []):
        st.markdown(f"✅ {step}")

    # WhatsApp Link
    tools = res.get('suggested_tools', [])
    tools_str = ', '.join(tools)
    phone = "56931495038"
    msg = f"¡Hola Camila! En PlantaDoc diagnosticaron {res.get('probable_cause')}. Necesito: {tools_str}."
    url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
    
    st.markdown(f'<br><a href="{url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:15px; border-radius:12px; text-align:center; font-weight:bold;">📲 Pedir productos por WhatsApp</div></a>', unsafe_allow_html=True)

    # --- NUEVA SECCIÓN: ENCUESTA DE SATISFACCIÓN ---
    st.markdown('<div class="survey-box">', unsafe_allow_html=True)
    st.markdown("### 📝 Ayúdanos a mejorar")
    st.write("Tu opinión es mágica para nosotros. ¿Qué te pareció el diagnóstico?")
    
    with st.form("satisfaction_survey"):
        rating = st.select_slider("Califica la precisión del diagnóstico:", options=["Pobre", "Regular", "Buena", "Muy Buena", "Excelente"], value="Muy Buena")
        useful = st.radio("¿Te resultó útil la recomendación de productos?", ("Sí, mucho", "Algo", "No realmente"))
        feedback = st.text_input("¿Algún comentario adicional?")
        
        submit_survey = st.form_submit_button("Enviar Comentarios")
        
        if submit_survey:
            # Aquí podrías guardar las respuestas en una base de datos o enviarlas por correo
            st.success("¡Gracias! Tus respuestas han sido enviadas con éxito. 🌸")
            # Log de respuestas para el desarrollador (se ve en la consola de Streamlit)
            print(f"ENCUESTA: Rating: {rating}, Útil: {useful}, Comentario: {feedback}")
    
    st.markdown('</div>', unsafe_allow_html=True)
