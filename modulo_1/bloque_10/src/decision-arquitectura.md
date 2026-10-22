## Decisión de arquitectura: elección de modelo

## Modelo elegido

gemini-3.5-flash-lite

## Diagrama de arquitectura

El diagrama muestra el flujo completo del módulo: validación de la pregunta, lectura de GEMINI_API_KEY desde .env, envío dentro de un try, y el cálculo de costo a partir de usage_metadata.

## Comparación de candidatos

Condiciones de la prueba (20 de octubre de 2026):

Misma pregunta para todos los modelos: "Cuánto es 2 + 2? Dame solo el resultado".
5 ciclos por modelo, medidos con time.perf_counter() alrededor de enviar_peticion.
Tokens y costo calculados con la última petición de cada modelo, usando usage_metadata.
Precios del nivel de pago, Standard, por millón de tokens, tomados de Gemini Developer API pricing el 20 de octubre de 2026. El precio de salida incluye los tokens de razonamiento.

| Criterio | gemini-3.8-flash | gemini-3.6-flash | gemini-3.5-flash-lite | gemini-3.1-flash-lite |
| :--- | :--- | :--- | :--- | :--- |
| Precio de entrada (US$ / 1M tokens) | 0,75 * | 0,75 * | **0,30** | 0,25 |
| Precio de salida (US$ / 1M tokens) | 3,75 * | 3,75 * | **2,50** | 1,50 |
| Latencia promedio (s) | 8,34 | 3,82 † | **0,80** | sin datos (error 503) |
| Latencia mediana (s) | 6,41 | pendiente | **0,75** | sin datos |
| Rango mín–máx (s) | 4,38 – 19,04 | 1,36 – 12,43 † | **0,53 – 1,27** | sin datos |
| Tokens entrada / salida | 13 / 121 | pendiente | **13 / 1** | sin datos |
| Costo por petición (US$) | 0,000463 | pendiente | **0,000006** | sin datos |

* Precio vigente hasta el 31 de diciembre de 2026. Desde el 1 de enero de 2027, gemini-3.8-flash y gemini-3.6-flash pasan a US$1,50 de entrada y US$7,50 de salida.
† Medido con el nombre gemini-3.5-flash. Ese modelo está deprecado y Google redirige sus peticiones a gemini-3.6-flash, por lo que esta medición corresponde muy probablemente a gemini-3.6-flash. Queda pendiente repetirla con el nombre correcto.

## Notas sobre los datos:

- gemini-3.1-flash-lite devolvió un error 503 (error interno del servicio) durante la corrida y se omitió, así que no tiene mediciones.
- gemini-3-flash-preview se midió en una corrida anterior (1,05 s de promedio, US$0,000237 por petición) y se dejó fuera de la tabla porque Google lo clasifica como un modelo anterior en versión preview.
- Con 5 ciclos, un solo valor atípico mueve mucho el promedio. En gemini-3.8-flash, el máximo de 19,04 s eleva el promedio por sobre la mediana.
- Los tokens de salida cambian entre corridas. En la petición principal, gemini-3.8-flash generó 331 tokens de salida, y en la comparación 121.

## Para qué sirve cada modelo

# Las descripciones vienen de la documentación oficial de Google; las observaciones salen de esta prueba.

**gemini-3.8-flash**. Google lo presenta como su modelo Flash más inteligente, pensado para ingeniería de software de largo aliento, agentes autónomos y flujos de trabajo empresariales complejos. En la prueba fue el más lento. Sirve cuando la calidad del razonamiento importa más que la velocidad.

**gemini-3.6-flash**. Es un modelo estable de la generación anterior a 3.8, que Google describe como de inteligencia sostenida para tareas reales, a mayor velocidad y menor costo. Destaca en generación de código, ejecución de agentes y razonamiento espacial. Queda en un punto intermedio de latencia entre los modelos livianos y gemini-3.8-flash. Sirve como base cuando se busca equilibrio entre capacidad y tiempo de respuesta.

**gemini-3.5-flash-lite**. Es un modelo económico, optimizado para tareas de alto volumen, traducción y procesamiento simple de datos. Fue el más rápido y el más barato, con una latencia estable. Sirve para consultas simples y de respuesta breve.

**gemini-3.1-flash-lite**. Google lo describe igual que gemini-3.5-flash-lite, y es el más barato por token de la lista. No pude medirlo por el error 503. Sirve para los mismos usos, y queda pendiente repetir la prueba.

## Justificación

Elegí **gemini-3.5-flash-lite** porque mi miniaplicación actual responde preguntas cortas y ejecuta tests de consistencia con respuestas estructuradas (JSON). Para este propósito, no necesito un modelo con razonamiento complejo, sino uno que sea **rápido, económico y con una latencia estable**.

En la prueba, fue el modelo más rápido con amplio margen (0,80 s de promedio frente a los 3,82 s del 3.6-flash y los 8,34 s del 3.8-flash). Además, su costo por petición fue el más bajo de todos (US$ 0,000006), generando solo 1 token de salida en la pregunta de prueba.

El precio por token del 3.5-flash-lite es considerablemente menor (0,30 de entrada y 2,50 de salida) frente a los modelos Flash grandes (0,75 y 3,75). Esto se traduce en un ahorro directo si el volumen de consultas crece.

Plan de evolución: mantener **gemini-3.5-flash-lite** como modelo base para la fase actual (consultas simples y pruebas). Si en el futuro la miniaplicación asume tareas de razonamiento más complejo, subir a gemini-3.6-flash o gemini-3.8-flash. El modelo se cambia con la variable GEMINI_MODEL del archivo .env, sin modificar el código.

Limitaciones de la comparación: la pregunta de prueba era muy simple, así que no evalué la calidad de respuestas más complejas. La latencia de gemini-3.6-flash se midió con el nombre de un modelo deprecado, con 5 ciclos y con una variación grande (de 1,36 s a 12,43 s), por lo que debe confirmarse.

## Alternativa descartada y por qué

Descarté **gemini-3.8-flash** y **gemini-3.6-flash**. Son los modelos más capaces, pero en la prueba fueron los más lentos y caros. Como la miniaplicación actual no requiere razonamiento complejo, su capacidad extra no compensa la espera ni el costo.

**gemini-3.1-flash-lite** no se descartó por resultados, sino porque no hay datos suyos por el error 503. Aunque es un poco más barato por token que el 3.5-flash-lite, este último tiene mediciones reales que demuestran su estabilidad y velocidad, por lo que es la opción más segura para producción.

**gemini-3-flash-preview** quedó fuera porque Google lo clasifica como un modelo anterior en versión preview, algo poco recomendable como base de un sistema que va a crecer.