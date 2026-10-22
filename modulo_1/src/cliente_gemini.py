import json
import os
import re
import statistics
import time

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

# Carga las variables definidas en el archivo .env
load_dotenv()

MODELO_POR_DEFECTO = "gemini-3.6-flash"

# Precios oficiales, nivel de pago, Standard.
# Unidad: nanodólares por token (USD por millón de tokens × 1.000).
# Fuente: https://ai.google.dev/gemini-api/docs/pricing (consultado el 2026-10-20).
# El precio de salida incluye los tokens de razonamiento.
# gemini-3.8-flash y gemini-3.6-flash: precio vigente hasta el 2026-12-31;
# desde el 2027-01-01 suben a (1500, 7500).
PRECIOS = {
    "gemini-3.8-flash": (750, 3750),
    "gemini-3.6-flash": (750, 3750),
    "gemini-3.5-flash-lite": (300, 2500),
    "gemini-3.1-flash-lite": (250, 1500),
}
MODELOS_A_COMPARAR = list(PRECIOS)
CICLOS_POR_MODELO = 5
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
    """Detiene la ejecución si la pregunta no es texto o viene vacía."""
    if not isinstance(pregunta, str):
        raise ValueError("La pregunta debe ser una cadena de texto")
    if not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía")
    return pregunta.strip()


def enviar_peticion(cliente, pregunta, modelo=None,
                    system_instruction=None, response_schema=None):
    """Envía la pregunta al modelo y devuelve la respuesta cruda del SDK.

    system_instruction: instrucción de comportamiento, separada de la pregunta.
    response_schema: forma exacta que debe tener el JSON de la respuesta.
    Los dos son opcionales: si no se pasan, funciona como antes.
    """
    modelo = modelo or os.getenv("GEMINI_MODEL", MODELO_POR_DEFECTO)

    # Armamos las opciones solo con lo que nos pasaron
    opciones = {}
    if system_instruction:
        opciones["system_instruction"] = system_instruction
    if response_schema:
        opciones["response_mime_type"] = "application/json"
        opciones["response_schema"] = response_schema
    config = types.GenerateContentConfig(**opciones)

    try:
        return cliente.models.generate_content(
            model=modelo, contents=pregunta, config=config
        )
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


def parsear_respuesta_json(texto, claves_esperadas):
    """Convierte el texto del modelo en un diccionario y revisa sus claves."""
    # 1. Limpiar: quitar espacios y las marcas ```json ... ``` si el modelo las puso
    limpio = texto.strip()
    limpio = re.sub(r"^```(?:json)?\s*", "", limpio)  # borra ```json del inicio
    limpio = re.sub(r"\s*```$", "", limpio)           # borra ``` del final

    # 2. Convertir el texto en un diccionario de Python
    try:
        datos = json.loads(limpio)
    except json.JSONDecodeError as e:
        raise ValueError("La respuesta del modelo no es JSON válido.") from e

    # 3. Revisar que sea un diccionario y que traiga todas las claves
    if not isinstance(datos, dict):
        raise ValueError("La respuesta JSON no es un objeto.")
    for clave in claves_esperadas:
        if clave not in datos:
            raise ValueError(f"Falta la clave '{clave}' en la respuesta.")

    # 4. Todo bien
    return datos


def obtener_precios(modelo):
    """Devuelve (precio_entrada, precio_salida) del modelo, o falla con un mensaje claro."""
    precios = PRECIOS.get(modelo)
    if precios is None:
        raise RuntimeError(
            f"No hay precios cargados para el modelo '{modelo}'. "
            "Agrégalo al diccionario PRECIOS."
        )
    return precios


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


def medir_latencia(cliente, pregunta, modelo, ciclos=CICLOS_POR_MODELO):
    """Mide cuánto tarda enviar_peticion, repetida varias veces, y resume los tiempos."""
    if ciclos < 1:
        raise ValueError("Los ciclos deben ser al menos 1")

    tiempos = []
    respuesta = None
    for _ in range(ciclos):
        inicio = time.perf_counter()
        respuesta = enviar_peticion(cliente, pregunta, modelo)
        fin = time.perf_counter()
        tiempos.append(fin - inicio)

    return {
        "modelo": modelo,
        "ciclos": ciclos,
        "tiempos": tiempos,
        "promedio": sum(tiempos) / len(tiempos),
        "mediana": statistics.median(tiempos),
        "minimo": min(tiempos),
        "maximo": max(tiempos),
        # Se conserva la última respuesta para calcular tokens y costo
        "ultima_respuesta": respuesta,
    }
#obtener_dato_de_prueba
def obtener_dato_de_prueba(pregunta, system_instruction=None, response_schema=None):
    """Valida, envía, extrae y, si hay esquema, convierte la respuesta en diccionario.
    Devuelve el resultado, o None si algo falla."""
    try:
        pregunta = validar_pregunta(pregunta)
        cliente = crear_cliente()
        respuesta = enviar_peticion(
            cliente, pregunta,
            system_instruction=system_instruction,
            response_schema=response_schema,
        )
        texto = extraer_texto(respuesta)
        if response_schema:
            # Las claves esperadas son las que el esquema marca como "required"
            return parsear_respuesta_json(texto, response_schema.get("required", []))
        return texto
    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la operación:", error)
        return None
    
if __name__ == "__main__":
    pregunta = (
        "Hola, confirma con un mensaje corto que mi entorno Python está "
        "bien configurado."
    )
    try:
        cliente = crear_cliente()
        pregunta_validada = validar_pregunta(pregunta)

        # Petición principal, con el modelo explícito para buscar su precio
        modelo_principal = os.getenv("GEMINI_MODEL", MODELO_POR_DEFECTO)
        respuesta = enviar_peticion(cliente, pregunta_validada, modelo_principal)

        print("Respuesta del modelo:")
        print(extraer_texto(respuesta))

        precio_entrada, precio_salida = obtener_precios(modelo_principal)
        uso = calcular_costo(respuesta, precio_entrada, precio_salida)
        costo_usd = uso["costo_nanodolares"] / NANODOLARES_POR_DOLAR

        print(f"\nModelo: {modelo_principal}")
        print(f"Tokens de entrada: {uso['tokens_entrada']}")
        print(f"Tokens de salida: {uso['tokens_salida']}")
        print(f"Costo estimado (precio oficial): US$ {costo_usd:.6f}")

        # Comparación: misma pregunta corta para todos los modelos
        pregunta_latencia = validar_pregunta(
            "Cuánto es 2 + 2? Dame solo el resultado"
        )
        print(f"\nComparación ({CICLOS_POR_MODELO} ciclos por modelo):")
        for modelo in MODELOS_A_COMPARAR:
            # Si un modelo falla, se omite y se sigue con el siguiente
            try:
                resultado = medir_latencia(cliente, pregunta_latencia, modelo)
                p_entrada, p_salida = obtener_precios(modelo)
                uso_modelo = calcular_costo(
                    resultado["ultima_respuesta"], p_entrada, p_salida
                )
            except RuntimeError as error:
                print(f"{modelo}: se omite ({error})")
                continue

            costo_modelo = uso_modelo["costo_nanodolares"] / NANODOLARES_POR_DOLAR
            print(
                f"{modelo}: "
                f"prom {resultado['promedio']:.2f} s | "
                f"mediana {resultado['mediana']:.2f} s | "
                f"mín {resultado['minimo']:.2f} s | "
                f"máx {resultado['maximo']:.2f} s | "
                f"tokens {uso_modelo['tokens_entrada']}/{uso_modelo['tokens_salida']} | "
                f"costo US$ {costo_modelo:.6f}"
            )

    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la operación:", error)