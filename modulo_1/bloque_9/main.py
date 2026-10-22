from cliente_gemini import obtener_dato_de_prueba

# 1. Pregunta normal, texto libre
print(obtener_dato_de_prueba("¿Cuál es la capital de Japón?"))

# 2. Dato inválido: debe avisar y devolver None, sin romper el programa
print(obtener_dato_de_prueba([1, 2]))

# 3. Con prompt de sistema y salida JSON
esquema = {
    "type": "OBJECT",
    "properties": {
        "rta": {"type": "STRING"},
        "fuente": {"type": "STRING"},
    },
    "required": ["rta", "fuente"],
}
print(obtener_dato_de_prueba(
    "¿Cuál es el río más largo de Sudamérica?",
    system_instruction="Responde con una sola palabra en 'rta' e indica la fuente en 'fuente'.",
    response_schema=esquema,
))