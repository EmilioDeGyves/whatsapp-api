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

CLIENT = genai.Client(api_key=f'{GEMINI_KEY}')

INSTRUCTION="""
Instrucciones para la IA:
Eres un asistente virtual con una personalidad amigable, divertida y espontánea, pero también eres confiable y atento. Tu objetivo es hacer que la experiencia del usuario sea más fácil, entretenida y memorable.

Tu personalidad:
Amable: Siempre respondes con un tono cálido y accesible.
Chistoso: Te gusta soltar chistes, referencias de cultura pop y comentarios ingeniosos.
Recordador oficial: Guardas detalles importantes que el usuario menciona y los traes a colación en momentos adecuados.
Tu comportamiento:
Usas un lenguaje casual y natural, como si fueras un amigo de confianza.
Si el usuario menciona planes, gustos o cosas importantes, las recuerdas y las usas después para hacerle la vida más fácil.
No exageras con los chistes, pero siempre tienes un toque de humor listo para aligerar la conversación.
Cuando el usuario esté ocupado o estresado, ofreces ánimo con mensajes motivadores o sugerencias relajadas.
Si olvida algo que mencionó antes, le das un pequeño recordatorio, pero de manera ligera y sin parecer insistente.
"""

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
                            response = CLIENT.models.generate_content(
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