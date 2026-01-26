import os
import openai # Importamos la librería de OpenAI
from flask import Flask, render_template, request, jsonify
import json # Importamos json para procesar la respuesta del modelo

# --- Configuración de la API de OpenAI ---
# La librería buscará automáticamente la variable de entorno 'OPENAI_API_KEY'.
# Asegúrate de haberla configurado en tu terminal.
try:
    client = openai.OpenAI()
except openai.OpenAIError as e:
    print(f"Error al inicializar el cliente de OpenAI. Asegúrate de que tu API key está configurada como una variable de entorno.")
    print(f"Error: {e}")
    client = None

# Inicialización de la aplicación Flask
app = Flask(__name__)

@app.route('/')
def index():
    """Renderiza la página principal con el formulario de diagnóstico."""
    return render_template('index.html')

def get_plant_diagnosis(plant_type, symptoms, conditions):
    """
    Función que llama a la API de OpenAI para obtener un diagnóstico.
    """
    if not client:
        return {
            "error": "El cliente de OpenAI no está configurado correctamente. Revisa tu API key."
        }

    # --- Creación del Prompt para el LLM ---
    # Este es el "cerebro" de la operación. Le damos instrucciones claras al modelo.
    system_prompt = """
    Eres "PlantaDoc", un experto botánico y fitopatólogo de IA. 
    Tu objetivo es diagnosticar problemas en plantas basándote en la descripción del usuario.
    Proporciona una respuesta estructurada en formato JSON con las siguientes claves:
    1. "probable_cause": Un título corto y claro del diagnóstico (ej. "Ataque de Pulgón y Deficiencia de Magnesio").
    2. "explanation": Una explicación detallada pero fácil de entender sobre por qué llegaste a ese diagnóstico, relacionando los síntomas descritos.
    3. "action_plan": Una lista de strings, donde cada string es un paso claro y accionable del plan de tratamiento. Numera los pasos principales y usa un lenguaje sencillo.
    """
    
    user_prompt = f"""
    Necesito un diagnóstico para mi planta. Aquí están los detalles:
    - Tipo de planta: {plant_type}
    - Síntomas observados: {symptoms}
    - Condiciones de cultivo: {conditions}
    """

    try:
        #Llamada a la API de OpenAI
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}, # Forzamos la salida a ser un JSON válido.
            temperature=0.5, # Un valor bajo para respuestas más consistentes y menos "creativas".
            max_tokens=1000
        )
        
        # Extraemos el contenido JSON de la respuesta
        diagnosis_json = response.choices[0].message.content
        return json.loads(diagnosis_json)

    except openai.APIError as e:
        print(f"Ocurrió un error con la API de OpenAI: {e}")
        return {
            "error": "Hubo un problema al comunicarse con la API de OpenAI. Inténtalo de nuevo más tarde."
        }
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        return {
            "error": "Ocurrió un error inesperado al procesar tu solicitud."
        }


@app.route('/diagnose', methods=['POST'])
def diagnose():
    """
    Endpoint que recibe la descripción del problema de la planta y devuelve un diagnóstico.
    """
    # Obtener datos del JSON enviado desde el frontend
    plant_type = request.json.get('plant_type')
    symptoms = request.json.get('symptoms')
    conditions = request.json.get('conditions')

    if not all([plant_type, symptoms, conditions]):
        return jsonify({"error": "Faltan datos en la solicitud."}), 400

    # Llamamos a nuestra nueva función para obtener el diagnóstico del LLM
    diagnosis_result = get_plant_diagnosis(plant_type, symptoms, conditions)
    
    if "error" in diagnosis_result:
        return jsonify(diagnosis_result), 500

    return jsonify(diagnosis_result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)