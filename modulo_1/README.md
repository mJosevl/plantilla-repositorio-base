# Proyecto: Miniaplicación con Gemini (Módulo 1)

Este repositorio contiene el avance del proyecto para el programa de Especialización en Desarrollo con IA Generativa (Accenture). Actualmente incluye un módulo de conexión a la API de Google Gemini, análisis de rendimiento y un banco de pruebas para validar la consistencia de los prompts.

## Estructura del proyecto

- `modulo_1/src/` : Código fuente del módulo 1.
  - `cliente_gemini.py` : Motor de conexión a la API. Incluye validación de respuestas JSON, manejo de errores (429/503) y cálculo de costos por tokens.
  - `banco.py` : Banco de 3 prompts de prueba con sus esquemas de validación (`response_schema`).
  - `test_consistencia.py` : Script evaluador que ejecuta los prompts del banco 3 veces cada uno y genera evidencia en JSON.
  - `registro_resultados.json` : Evidencia de la última ejecución exitosa (9/9 pruebas superadas).
- `modulo_1/docs/` : Documentación técnica.
  - `decision-arquitectura.md` : Justificación de la elección del modelo (`gemini-3.6-flash`) basada en pruebas de latencia y costo.
- `modulo_1/requirements.txt` : Dependencias del proyecto.
- `.env.example` : Plantilla de variables de entorno (la API Key real va en `.env`, el cual no se sube al repositorio).

## ¿Cómo ejecutar el proyecto?

1. Asegúrate de tener tu entorno virtual activado y las dependencias instaladas:
   ```bash
   pip install -r modulo_1/requirements.txt
Crea un archivo .env en la raíz (basado en .env.example) y agrega tu llave:

env
GEMINI_API_KEY=tu_api_key_aqui
Para probar la conexión básica y ver el benchmark de modelos:

bash
cd modulo_1
python src/cliente_gemini.py
Para ejecutar el test de consistencia de los prompts (genera el archivo registro_resultados.json):

bash
python src/test_consistencia.py
Decisiones de arquitectura y estado actual
Modelo elegido: gemini-3.6-flash por su equilibrio entre capacidad y latencia (ver docs/decision-arquitectura.md).

Manejo de errores: El cliente y el test están preparados para distinguir entre fallos de la API (límite de cuota 429, error interno 503) y fallos en la estructura de los prompts.

Consistencia: Las 3 pruebas del banco (capital_pais, es_par, colores_primarios) han demostrado un 100% de consistencia en formato y contenido en la última ejecución.



