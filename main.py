import streamlit as st
from groq import Groq
import json
import urllib.parse # Para crear el enlace de WhatsApp
import base64 # IMPORTANTE: Necesario para procesar imágenes

# --- 1. Configuración de la página ---
st.set_page_config(
    page_title="PlantaDoc AI - Diagnóstico Visual",
    page_icon="🌿",
    layout="centered"
)

# --- 2. Configuración de la API Key ---
try:
    # Asegúrate de tener esto en .streamlit/secrets.toml
    api_key = st.secrets["API_KEY"]
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"Error de configuración: {e}")
    stop = True
    client = None

# --- FUNCIÓN HELPER PARA IMÁGENES ---
def encode_image(uploaded_file):
    """Codifica el archivo subido a base64 para la API."""
    if uploaded_file is not None:
        try:
            return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        except Exception as e:
            st.error(f"Error al procesar la imagen: {e}")
            return None
    return None

# --- 3. Lógica del Diagnóstico 
def get_plant_diagnosis(plant_type, symptoms, conditions, image_base64=None):
    """
    Función blindada contra prompt injection, enfocada en ventas, con soporte visual.
    """
    
    # 1. Selección del Modelo
    # Si hay imagen, usamos el modelo de visión (Llama 3.2 11B).
    # Si NO hay imagen, usamos el modelo de texto más potente (Llama 3.3 70B) para mejor razonamiento.
    if image_base64:
        model_id = "llama-3.2-11b-vision-preview" 
    else:
        model_id = "llama-3.3-70b-versatile"

    # SYSTEM PROMPT
    system_prompt = """
    Eres "PlantaDoc", una IA experta en botánica.
    TUS REGLAS:
    1. Si el input (texto o imagen) NO es sobre plantas, devuelve {"is_plant_related": false}.
    2. Diagnostica el problema y sugiere una solución.
    3. Responde SIEMPRE en formato JSON estricto.
    
    FORMATO JSON:
    {
        "is_plant_related": true,
        "probable_cause": "Causa",
        "explanation": "Explicación breve",
        "action_plan": ["Paso 1", "Paso 2"],
        "suggested_tools": ["Producto A", "Herramienta B"]
    }
    """
    
    # USER PROMPT
    user_text = f"""
    Planta: {plant_type}
    Síntomas: {symptoms}
    Condiciones: {conditions}
    """

    # Construcción del mensaje según si hay imagen o no
    messages_payload = [{"role": "system", "content": system_prompt}]

    if image_base64:
        # Estructura para Modelo de Visión
        messages_payload.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                }
            ]
        })
    else:
        # Estructura para Modelo de Texto Normal
        messages_payload.append({
            "role": "user", 
            "content": user_text
        })

    try:
        chat_completion = client.chat.completions.create(
            messages=messages_payload,
            model=model_id, # Usamos el modelo seleccionado dinámicamente
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"},
            stop=None,
        )
        
        return json.loads(chat_completion.choices[0].message.content)

    except Exception as e:
        return {"error": f"Error de API ({model_id}): {str(e)}"}


# --- 4. Interfaz de Usuario ---
st.title("🌿 PlantaDoc AI + Visión")
st.markdown("Sube una foto y describe el problema para un diagnóstico experto.")

with st.form("diagnosis_form"):
    col1, col2 = st.columns(2)
    with col1:
        plant_type = st.text_input("Tipo de planta (Opcional)", placeholder="Ej. Ficus, Rosa...")
    with col2:
        conditions = st.text_input("Condiciones (Opcional)", placeholder="Ej. Interior, poca luz...")
    
    # --- NUEVO: Cargador de imágenes ---
    st.markdown("### 📸 Sube una foto de la planta (Opcional pero recomendado)")
    uploaded_file = st.file_uploader("Elige una imagen...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Mostrar la imagen que el usuario acaba de subir
        st.image(uploaded_file, caption="Imagen cargada para análisis", use_column_width=True)

    symptoms = st.text_area("Describe los síntomas (Obligatorio si no hay foto)", placeholder="Ej. Hojas negras, bichos blancos...", height=100)
    
    submitted = st.form_submit_button("🔍 Analizar Planta")


# --- 5. Procesamiento y Resultados ---
if submitted:
    # Validaciones básicas
    if not client:
        st.error("Falta configurar la API Key en los secrets.")
        st.stop()
        
    # Validar que haya al menos descripción O imagen
    if not symptoms and not uploaded_file:
        st.warning("⚠️ Por favor, describe los síntomas por escrito o sube una imagen de la planta.")
    else:
        with st.spinner("Analizando imagen y texto con protocolos de seguridad..."):
            # 1. Procesar imagen si existe
            image_base64_data = None
            if uploaded_file:
                image_base64_data = encode_image(uploaded_file)
                if image_base64_data is None:
                    st.stop() # Hubo un error al codificar

            # 2. Llamar a la IA (pasando la imagen si la hay)
            result = get_plant_diagnosis(plant_type, symptoms, conditions, image_base64=image_base64_data)

            # A. Manejo de Errores Técnicos
            if "error" in result:
                st.error(result["error"])
            
            # B. Manejo de Bloqueo de Seguridad (Prompt Injection detectado o imagen no válida)
            elif result.get("is_plant_related") is False:
                st.error("🚫 Solicitud rechazada.")
                st.markdown("PlantaDoc ha detectado que el texto o la imagen proporcionada **no parecen estar relacionados con plantas**.")
                st.info("Por favor, asegúrate de subir una foto clara de una planta o reformula tu pregunta enfocándote en botánica.")

            # C. Diagnóstico Exitoso
            else:
                st.success("✅ Diagnóstico completado exitosamente")
                st.divider()
                
                # Mostrar Diagnóstico Principal
                st.subheader(f"🔍 Causa probable: {result.get('probable_cause', 'No especificada')}")
                st.write(result.get('explanation', 'Sin explicación detallada.'))
                
                # Plan de Acción
                st.markdown("### 🚑 Plan de Tratamiento")
                action_plan = result.get('action_plan', [])
                if action_plan:
                    for step in action_plan:
                        st.markdown(f"- {step}")
                else:
                    st.info("No se generó un plan de acción específico.")

                # Sección de Productos Sugeridos y Venta
                tools = result.get('suggested_tools', [])
                if tools:
                    st.divider()
                    st.markdown("### 🛠️ Herramientas y Productos Recomendados")
                    tools_str = ', '.join(tools)
                    st.info(f"Para este tratamiento, PlantaDoc sugiere utilizar: **{tools_str}**.")
                    
                    # --- Integración con WhatsApp de Camila ---
                    phone_number = "56931495038" 
                    
                    # Creamos el mensaje prellenado (incluyendo mención a la foto si la hubo)
                    base_msg = f"Hola Camila, mi planta tiene *{result.get('probable_cause')}*."
                    if uploaded_file:
                        base_msg += " (Tengo una foto del problema)."
                    base_msg += f" PlantaDoc me recomendó comprar: {tools_str}. ¿Me puedes orientar para la compra?"
                    
                    msg_encoded = urllib.parse.quote(base_msg)
                    whatsapp_url = f"https://wa.me/{phone_number}?text={msg_encoded}"
                    
                    st.markdown(f"""
                    <a href="{whatsapp_url}" target="_blank" style="text-decoration: none;">
                        <button style="
                            background-color:#25D366; 
                            color:white; 
                            border:none; 
                            padding:12px 24px; 
                            border-radius:8px; 
                            font-weight:bold; 
                            font-size:18px; 
                            cursor:pointer;
                            width:100%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 10px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            transition: background-color 0.3s;">
                            <span>📲</span> Contactar a Camila (Comprar utensilios)
                        </button>
                    </a>
                    """, unsafe_allow_html=True)
                    st.caption("Al hacer clic, se abrirá WhatsApp con tu diagnóstico listo para enviar.")
