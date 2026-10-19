import os

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors

# Carga las variables definidas en el archivo .env
load_dotenv()

MODELO_POR_DEFECTO = "gemini-3.8-flash"


def crear_cliente():
    """Crea el cliente de Gemini validando que exista la credencial."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta GEMINI_API_KEY. Revisa que tu archivo .env esté en la raíz "
            "del proyecto y que la variable se llame exactamente así."
        )
    return genai.Client(api_key=api_key)


def validar_pregunta(pregunta):
    """Detiene la ejecución si la pregunta viene vacía."""
    if not pregunta or not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía")
    return pregunta.strip()


def enviar_peticion(cliente, pregunta, modelo=None):
    """Envía la pregunta al modelo y devuelve la respuesta cruda del SDK."""
    modelo = modelo or os.getenv("GEMINI_MODEL", MODELO_POR_DEFECTO)
    try:
        return cliente.models.generate_content(model=modelo, contents=pregunta)
    except errors.ClientError as e:
        raise RuntimeError(
            f"El servicio rechazó la petición (código {e.code}): {e.message}. "
            "Revisa tu API key y el nombre del modelo."
        ) from e
    except errors.ServerError as e:
        raise RuntimeError(
            f"El servicio tuvo un error interno (código {e.code}). "
            "Intenta de nuevo en unos segundos."
        ) from e
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise RuntimeError(
            "No se pudo conectar con el servicio. Intenta de nuevo en unos segundos."
        ) from e


def extraer_texto(respuesta):
    """Obtiene el texto generado; falla con un mensaje claro si no viene."""
    texto = getattr(respuesta, "text", None)
    if not texto:
        raise RuntimeError(
            "La respuesta no trae el texto generado en el lugar esperado."
        )
    return texto


def calcular_costo_entero(respuesta, precio_entrada_millones, precio_salida_millones):
    """Calcula el costo total devolviendo un valor entero (en unidades escaladas)."""
    uso = getattr(respuesta, "usage_metadata", None)
    if not uso:
        return 0
    
    tokens_prompt = getattr(uso, "prompt_token_count", 0)
    tokens_respuesta = getattr(uso, "candidates_token_count", 0)
    
    # Realiza el cálculo multiplicando correctamente tokens por sus tarifas escaladas
    costo_total = (tokens_prompt * precio_entrada_millones) + (tokens_respuesta * precio_salida_millones)
    return int(costo_total)


if __name__ == "__main__":
    pregunta = (
        "Hola, confirma con un mensaje corto que mi entorno Python está "
        "bien configurado."
    )
    try:
        cliente = crear_cliente()
        pregunta_validada = validar_pregunta(pregunta)
        
        # Obtenemos la respuesta cruda para poder evaluar tanto el texto como los metadatos
        respuesta = enviar_peticion(cliente, pregunta_validada)
        
        # Mostramos la respuesta generada
        print("Respuesta del modelo:")
        print(extraer_texto(respuesta))
        
        # Calculamos el costo entero utilizando factores de escala
        PRECIO_ENTRADA_ESCALADO = 150
        PRECIO_SALIDA_ESCALADO = 600
        
        costo_entero = calcular_costo_entero(respuesta, PRECIO_ENTRADA_ESCALADO, PRECIO_SALIDA_ESCALADO)
        print(f"\n[Costo interno calculado (valor entero): {costo_entero}]")
        
    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la operación:", error)