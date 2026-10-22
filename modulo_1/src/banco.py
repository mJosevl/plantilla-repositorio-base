BANCO_DE_PROMPTS = [
    {
        "nombre": "capital_pais",
        "system_instruction": (
            "Responde en el campo 'rta' con 1 o 2 palabras. "
            "Añade en 'contexto' una sola frase breve (máx. 20 palabras). "
            "Devuelve únicamente JSON con las claves 'rta' y 'contexto'."
        ),
        "ejemplo_usuario": "¿Cuál es la capital de Japón?",
        "claves_esperadas": ["rta", "contexto"],
        "response_schema": {
            "type": "object",
            "properties": {
                "rta":      {"type": "string"},
                "contexto": {"type": "string"},
            },
            "required": ["rta", "contexto"],
        },
        "valor_esperado": {"rta": "Tokio"},
    },
    {
        "nombre": "es_par",
        "system_instruction": (
            "Indica en 'respuesta' solo 'si' o 'no'. "
            "Justifica en 'motivo' con una frase corta. "
            "Devuelve únicamente JSON con las claves 'respuesta' y 'motivo'."
        ),
        "ejemplo_usuario": "¿El número 7 es par?",
        "claves_esperadas": ["respuesta", "motivo"],
        "response_schema": {
            "type": "object",
            "properties": {
                "respuesta": {"type": "string", "enum": ["si", "no"]},
                "motivo":    {"type": "string"},
            },
            "required": ["respuesta", "motivo"],
        },
        "valor_esperado": {"respuesta": "no"},
    },
    {
        "nombre": "colores_primarios",
        "system_instruction": (
            "Devuelve en 'items' una lista de máximo 3 colores primarios. "
            "En 'criterio' explica en una frase por qué son primarios. "
            "Devuelve únicamente JSON con las claves 'items' y 'criterio'."
        ),
        "ejemplo_usuario": "Lista los colores primarios.",
        "claves_esperadas": ["items", "criterio"],
        "response_schema": {
            "type": "object",
            "properties": {
                "items":   {"type": "array", "items": {"type": "string"},
                            "maxItems": 3},
                "criterio": {"type": "string"},
            },
            "required": ["items", "criterio"],
        },
        "valor_esperado": {"items_contiene": ["rojo", "azul", "amarillo"]},
    },
]