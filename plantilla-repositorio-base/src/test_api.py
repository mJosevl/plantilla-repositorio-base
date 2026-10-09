import os
from dotenv import load_dotenv
from google import genai

# Carga las variables definidas en el archivo .env
load_dotenv()

# Usa genai.Client directamente (SIN "google.")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Realiza una petición de prueba al modelo
response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Hola, confirma con un mensaje corto que mi entorno Python está bien configurado."
)

print("Respuesta de Gemini:\n")
print(response.text)