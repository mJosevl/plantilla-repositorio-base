import os

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors

# Carga las variables definidas en el archivo .env
load_dotenv()

MODELO_POR_DEFECTO = "gemini-3.8-flash"

# Tarifa FICTICIA, solo para el ejercicio.
# Unidad: nanodólares por token (precio por millón × 1.000).
# US$1 por millón de entrada = 1000; US$4 por millón de salida = 4000.
PRECIO_ENTRADA_ESCALADO = 1000
PRECIO_SALIDA_ESCALADO = 4000
NANODOLARES_POR_DOLAR = 1_000_000_000


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


def calcular_costo(respuesta, precio_entrada, precio_salida):
    """Devuelve tokens y costo (en nanodólares enteros) a partir de usage_metadata."""
    uso = getattr(respuesta, "usage_metadata", None)
    if not uso:
        raise RuntimeError(
            "La respuesta no trae usage_metadata, no se puede calcular el costo."
        )

    # "or 0" cubre tanto el atributo ausente como el valor None
    tokens_entrada = getattr(uso, "prompt_token_count", None) or 0
    tokens_respuesta = getattr(uso, "candidates_token_count", None) or 0
    tokens_razonamiento = getattr(uso, "thoughts_token_count", None) or 0

    # Los tokens de razonamiento se cobran como salida
    tokens_salida = tokens_respuesta + tokens_razonamiento

    costo = tokens_entrada * precio_entrada + tokens_salida * precio_salida
    return {
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "costo_nanodolares": costo,
    }


if __name__ == "__main__":
    pregunta = (
        "Hola, confirma con un mensaje corto que mi entorno Python está "
        "bien configurado."
    )
    try:
        cliente = crear_cliente()
        pregunta_validada = validar_pregunta(pregunta)
        respuesta = enviar_peticion(cliente, pregunta_validada)

        print("Respuesta del modelo:")
        print(extraer_texto(respuesta))

        uso = calcular_costo(
            respuesta, PRECIO_ENTRADA_ESCALADO, PRECIO_SALIDA_ESCALADO
        )
        costo_usd = uso["costo_nanodolares"] / NANODOLARES_POR_DOLAR

        print(f"\nTokens de entrada: {uso['tokens_entrada']}")
        print(f"Tokens de salida: {uso['tokens_salida']}")
        print(f"Costo estimado (tarifa ficticia): US$ {costo_usd:.6f}")

    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la operación:", error)