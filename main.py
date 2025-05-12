
from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import os
import requests

load_dotenv()

AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

app = FastAPI()

# Estados de sesión simples (en producción usar una base de datos o Redis)
user_states = {}

@app.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    Body: str = Form(...),
    From: str = Form(...)
):
    user_id = From
    user_input = Body.strip().lower()

    # Inicializa sesión del usuario si no existe
    if user_id not in user_states:
        user_states[user_id] = {"step": "menu", "data": {}}

    session = user_states[user_id]
    step = session["step"]
    data = session["data"]

    if user_input in ["menu", "inicio", "salir"]:
        session["step"] = "menu"
        session["data"] = {}
        reply = (
            "Hola 👋 ¿En qué te puedo ayudar hoy?\n"
            "1. Conocer nuestros servicios\n"
            "2. Agendar asesoría gratuita\n"
            "3. Ver promociones\n"
            "4. Descargar contenidos útiles\n"
            "5. Hablar con un asesor humano"
        )
    elif step == "menu":
        if user_input == "1":
            reply = (
                "Ofrecemos:\n- Campañas en Meta, Google, TikTok, X\n- Branding y posicionamiento\n"
                "- Diseño web (SEO/SEM)\n- Foto y video profesional\n- COFEPRIS (salud)\n"
                "- Consultoría comercial\n\n¿Deseas agendar asesoría gratuita? (Escribe '2')"
            )
        elif user_input == "2":
            session["step"] = "nombre"
            reply = "Perfecto. ¿Cuál es tu nombre completo?"
        elif user_input == "3":
            reply = "🎁 Promociones activas:\n- 2x1 en campañas publicitarias durante mayo\n- 25% en páginas web hasta este viernes."
        elif user_input == "4":
            reply = "📄 Descarga aquí nuestro catálogo: https://example.com/catalogo.pdf"
        elif user_input == "5":
            reply = "📞 Un asesor humano se comunicará contigo vía WhatsApp."
        else:
            reply = "Opción no válida. Escribe 'menu' para ver opciones."
    elif step == "nombre":
        data["Nombre"] = user_input
        session["step"] = "telefono"
        reply = "¿Cuál es tu número de teléfono?"
    elif step == "telefono":
        data["Telefono"] = user_input
        session["step"] = "email"
        reply = "¿Cuál es tu correo electrónico?"
    elif step == "email":
        data["Email"] = user_input
        session["step"] = "especialidad"
        reply = "¿Cuál es tu especialidad o giro?"
    elif step == "especialidad":
        data["Especialidad"] = user_input
        session["step"] = "fecha"
        reply = "¿Qué fecha y hora (dd/mm/yyyy hh:mm) prefieres para tu asesoría?"
    elif step == "fecha":
        try:
            fecha, hora = user_input.split()
            data["Fecha"] = fecha
            data["Hora"] = hora

            payload = {"records": [{"fields": data}]}
            response = requests.post(AIRTABLE_URL, headers=HEADERS, json=payload)

            if response.status_code in [200, 201]:
                reply = "✅ ¡Gracias! Hemos registrado tu asesoría. Escribe 'menu' para volver a empezar."
            else:
                reply = "❌ Error al guardar los datos. Intenta más tarde."

        except ValueError:
            reply = "❌ Por favor, ingresa la fecha y hora en el formato correcto: dd/mm/yyyy hh:mm"

        except Exception as e:
            reply = f"❌ Error inesperado: {e}"

        session["step"] = "menu"
        session["data"] = {}
    else:
        reply = "No entendí tu mensaje. Escribe 'menu' para ver las opciones."

    return PlainTextResponse(reply)
