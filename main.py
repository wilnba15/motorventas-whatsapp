
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
user_states = {}

@app.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    Body: str = Form(...),
    From: str = Form(...)
):
    print(f"📥 Mensaje recibido: {Body} de {From}")

    user_id = From
    user_input = Body.strip().lower()

    if user_id not in user_states:
        user_states[user_id] = {"step": "menu", "data": {}}

    session = user_states[user_id]
    step = session["step"]
    data = session["data"]

    try:
        if user_input in ["menu", "inicio", "salir"]:
            print("🔄 Reiniciando menú")
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
            print(f"🧭 Menú activo - opción recibida: {user_input}")
            if user_input == "1":
                reply = "Ofrecemos: campañas, branding, SEO/SEM, video, COFEPRIS, consultoría..."
            elif user_input == "2":
                session["step"] = "nombre"
                reply = "Perfecto. ¿Cuál es tu nombre completo?"
            elif user_input == "3":
                reply = "🎁 Promos: 2x1 en campañas y 25% en webs hasta el viernes"
            elif user_input == "4":
                reply = "📄 Catálogo: https://example.com/catalogo.pdf"
            elif user_input == "5":
                print("📤 Redirigiendo a WhatsApp asesor")
                enlace = "https://wa.me/593987654321?text=Hola%2C%20necesito%20ayuda%20con%20mi%20asesor%C3%ADa"
                reply = (
                    "👤 Te transfiero con un asesor humano.\n"
                    "🕘 Lunes a Viernes, 9:00 am a 6:00 pm\n"
                    f"👉 Haz clic: {enlace}"
                )
                session["step"] = "menu"
                session["data"] = {}
            else:
                reply = "Opción no válida. Escribe 'menu' para ver opciones."
        elif step == "nombre":
            print("📝 Guardando nombre")
            data["Nombre"] = user_input
            session["step"] = "telefono"
            reply = "¿Cuál es tu número de teléfono?"
        elif step == "telefono":
            print("📞 Guardando teléfono")
            data["Telefono"] = user_input
            session["step"] = "email"
            reply = "¿Cuál es tu correo electrónico?"
        elif step == "email":
            print("📧 Guardando email")
            data["Email"] = user_input
            session["step"] = "especialidad"
            reply = "¿Cuál es tu especialidad o giro?"
        elif step == "especialidad":
            print("🏷️ Guardando especialidad")
            data["Especialidad"] = user_input
            session["step"] = "fecha"
            reply = "¿Qué fecha y hora (dd/mm/yyyy hh:mm) prefieres para tu asesoría?"
        elif step == "fecha":
            try:
                print("📅 Procesando fecha")
                fecha, hora = user_input.split()
                data["Fecha"] = fecha
                data["Hora"] = hora

                payload = {"records": [{"fields": data}]}
                response = requests.post(AIRTABLE_URL, headers=HEADERS, json=payload)
                print(f"📤 Airtable response: {response.status_code}")

                if response.status_code in [200, 201]:
                    reply = "✅ ¡Gracias! Hemos registrado tu asesoría. Escribe 'menu' para volver."
                else:
                    reply = "❌ Error al guardar. Intenta más tarde."
            except ValueError:
                reply = "❌ Formato inválido. Usa: dd/mm/yyyy hh:mm"
            except Exception as e:
                reply = f"❌ Error inesperado: {e}"

            session["step"] = "menu"
            session["data"] = {}
        else:
            print("⚠️ Paso desconocido")
            reply = "❌ No entendí tu mensaje. Escribe 'menu' para comenzar de nuevo."
    except Exception as e:
        print(f"💥 Error global: {e}")
        reply = f"❌ Error inesperado en el servidor: {e}"
        session["step"] = "menu"
        session["data"] = {}

    print(f"✅ Respuesta enviada: {reply}")
    return PlainTextResponse(reply)
