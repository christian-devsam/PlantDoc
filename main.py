import streamlit as st
from groq import Groq # Importamos el cliente nativo de Groq
import json

# --- 1. Configuración de la página ---
st.set_page_config(
    page_title="PlantaDoc AI (vía Groq)",
    page_icon="🌿",
    layout="centered"
)

# --- 2. Configuración de la API Key desde Secrets ---
# Streamlit busca automáticamente en .streamlit/secrets.toml
try:
    api_key = st.secrets["API_KEY"]
    client = Groq(api_key=api_key)
except FileNotFoundError:
    st.error("No se encontró el archivo de secretos (.streamlit/secrets.toml).")
    client = None
except KeyError:
    st.error("La clave 'GROQ_API_KEY' no está definida en los secrets.")
    client = None
except Exception as e:
    st.error(f"Error al conectar con Groq: {e}")
    client = None

# --- 3. Lógica del Diagnóstico ---
def get_plant_diagnosis(plant_type, symptoms, conditions):
    """
    Función que llama a la API de Groq para obtener un diagnóstico.
    """
    system_prompt = """
    Eres "PlantaDoc", un experto botánico y fitopatólogo de IA. 
    Tu objetivo es diagnosticar problemas en plantas basándote en la descripción del usuario.
    
    IMPORTANTE: Debes responder EXCLUSIVAMENTE en formato JSON válido.
    
    Estructura del JSON:
    1. "probable_cause": Un título corto y claro del diagnóstico.
    2. "explanation": Una explicación detallada sobre por qué llegaste a ese diagnóstico.
    3. "action_plan": Una lista de strings con los pasos del tratamiento.
    """
    
    user_prompt = f"""
    Diagnostica esta planta en formato JSON:
    - Tipo de planta: {plant_type}
    - Síntomas observados: {symptoms}
    - Condiciones de cultivo: {conditions}
    """

    try:
        # Llamada a la API de Groq
        # CAMBIO: Usamos el modelo 'llama-3.3-70b-versatile' que es el actual y más potente
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile", # <--- AQUÍ ESTÁ EL CAMBIO
            temperature=0.5,
            max_tokens=1024,
            response_format={"type": "json_object"}, 
            stop=None,
        )
        
        diagnosis_json = chat_completion.choices[0].message.content
        return json.loads(diagnosis_json)

    except json.JSONDecodeError:
        return {"error": "El modelo no generó un JSON válido. Inténtalo de nuevo."}
    except Exception as e:
        return {"error": str(e)}

# --- 4. Interfaz de Usuario (Frontend) ---
st.title("🌿 PlantaDoc: Diagnóstico Ultra Rápido")
st.caption("Powered by Groq & Llama 3")

st.markdown("Describe el problema de tu planta y recibirás un diagnóstico instantáneo.")

with st.form("diagnosis_form"):
    col1, col2 = st.columns(2)
    with col1:
        plant_type = st.text_input("Tipo de planta", placeholder="Ej. Ficus Lyrata")
    with col2:
        conditions = st.text_input("Condiciones de cultivo", placeholder="Ej. Interior, poca luz")
    
    symptoms = st.text_area("Síntomas observados", placeholder="Ej. Caída de hojas, manchas blancas...", height=100)
    
    submitted = st.form_submit_button("Diagnosticar Planta")

# --- 5. Procesamiento ---
if submitted:
    if not client:
        st.error("Error de configuración: API Key de Groq no disponible.")
    elif not plant_type or not symptoms:
        st.warning("Por favor, completa al menos el tipo de planta y los síntomas.")
    else:
        with st.spinner("Consultando a Llama 3 en Groq..."):
            result = get_plant_diagnosis(plant_type, symptoms, conditions)

            if "error" in result:
                st.error(f"Ocurrió un error: {result['error']}")
            else:
                st.success("¡Diagnóstico completado!")
                st.divider()
                
                st.subheader(f"🔍 Diagnóstico: {result.get('probable_cause')}")
                
                st.markdown("### 📝 Explicación")
                st.write(result.get('explanation'))
                
                st.markdown("### 🚑 Plan de Acción")
                action_plan = result.get('action_plan', [])
                for step in action_plan:
                    st.markdown(f"- {step}")
