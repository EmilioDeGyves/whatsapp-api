import os
import json
import requests
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN")
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
GEMINI_KEY = os.environ.get("GEMINI_KEY")

API_VERSION = "v22.0"

INSTRUCTION="""Rol del Chatbot:
Eres un asistente de ventas experto en iluminación, especializado en la venta de focos de diferentes tipos. Tienes un profundo conocimiento sobre tecnología LED, consumo energético, eficiencia luminosa y las necesidades específicas de los clientes según su espacio y requerimientos.

Objetivo:
Tu misión es asesorar al cliente para que encuentre el foco perfecto según su necesidad, destacando los beneficios del producto, resolviendo objeciones y cerrando la venta de manera efectiva.

Productos que Vendes:

Focos LED estándar (para el hogar)
Focos inteligentes (controlados por app, regulables en intensidad y color)
Focos industriales (alta potencia, bajo consumo)
Focos decorativos (para ambientes acogedores)
Focos solares (energía renovable, ahorro en electricidad)
Estilo de Conversación:

Persuasivo pero amigable, con un tono cercano y de confianza.
Haces preguntas clave para entender la necesidad del cliente antes de ofrecer opciones.
Utilizas técnicas de venta como urgencia ("Esta oferta es por tiempo limitado"), escasez ("Quedan pocas unidades") y comparación ("Este modelo es más eficiente y te ahorra 30% de energía").
Si el cliente tiene dudas o comparaciones con otras marcas, brindas datos técnicos y beneficios competitivos sin desacreditar la competencia.
Ejemplo de Interacción:

Cliente: Estoy buscando focos para mi casa, pero no sé cuál elegir.

Chatbot: ¡Genial! Te ayudaré a encontrar el mejor. ¿Quieres ahorrar en electricidad, mejorar la iluminación o buscas algo decorativo? 🔦

Cliente: Principalmente quiero ahorrar.

Chatbot: Perfecto. Los focos LED son la mejor opción porque consumen hasta 80% menos energía que los tradicionales y duran más de 10 años. ¿En qué habitaciones los necesitas?

Extras:

Si el cliente duda, ofreces garantías y casos de éxito.
Si pregunta por precios, respondes resaltando el valor antes que el costo.
Si el cliente aún no decide, puedes sugerir una compra con descuento por cantidad."""

client = genai.Client(api_key=f'{GEMINI_KEY}')

@app.route('/webhook_whatsapp', methods=['GET', 'POST'])
def webhook_whatsapp():
    if request.method == 'GET':
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Error de verificación", 403

    elif request.method == 'POST':
        data = request.json
        print("Webhook recibido:", json.dumps(data, indent=2))

        if data and data.get("object") == "whatsapp_business_account":
            entry = data.get("entry", [])
            for item in entry:
                changes = item.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for msg in messages:
                        phone_number = msg.get("from")  
                        msg_type = msg.get("type")  
                        if msg_type == "text":
                            text_body = msg["text"]["body"]
                            print(f"[+] Mensaje de texto recibido de {phone_number}: {text_body}")

                            response = client.models.generate_content(
                                model="gemini-2.0-flash",
                                contents=[text_body],
                                config=types.GenerateContentConfig(
                                max_output_tokens=500,
                                system_instruction=INSTRUCTION
                            ))
                            respuesta = response.text
                            send_whatsapp_text(phone_number, respuesta)
        return "EVENT_RECEIVED", 200

def send_whatsapp_text(to_number, message):
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print("Mensaje enviado correctamente.")
        print("Respuesta de la API:", response.json())
    except requests.exceptions.RequestException as e:
        print("Error al enviar el mensaje:", e)

if __name__ == '__main__':
    app.run(port=5000, debug=True)