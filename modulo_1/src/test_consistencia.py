import json
import os
import sys
from pathlib import Path

# Permite importar cliente_gemini desde modulo_1/src
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "modulo_1" / "src"))
from cliente_gemini import (            # noqa: E402
    crear_cliente, enviar_peticion, extraer_texto, parsear_respuesta_json,
)
from banco import BANCO_DE_PROMPTS       # noqa: E402

CICLOS = 3
MODELO = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def validar_valores(datos, valor_esperado):
    """Lanza ValueError si los valores no coinciden con lo esperado."""
    for clave, esperado in valor_esperado.items():
        if clave == "items_contiene":
            items = [str(x).lower() for x in datos.get("items", [])]
            faltan = [c for c in esperado if c not in items]
            if faltan:
                raise ValueError(f"items no contiene {faltan}")
        else:
            obtenido = str(datos.get(clave, "")).strip().lower()
            if obtenido != str(esperado).lower():
                raise ValueError(
                    f"'{clave}' = {obtenido!r}, se esperaba {esperado!r}"
                )


def probar_prompt(cliente, prompt):
    exitos = fallos_prompt = fallos_infra = 0
    detalles = []

    for i in range(CICLOS):
        try:
            respuesta = enviar_peticion(
                cliente, prompt["ejemplo_usuario"], MODELO,
                system_instruction=prompt["system_instruction"],
                response_schema=prompt["response_schema"],
            )
            texto = extraer_texto(respuesta)
        except RuntimeError as e:
            fallos_infra += 1
            detalles.append({"ciclo": i + 1, "tipo": "infra", "error": str(e)})
            continue

        try:
            datos = parsear_respuesta_json(texto, prompt["claves_esperadas"])
            validar_valores(datos, prompt["valor_esperado"])
            exitos += 1
            detalles.append({"ciclo": i + 1, "tipo": "ok", "datos": datos})
        except ValueError as e:
            fallos_prompt += 1
            detalles.append({"ciclo": i + 1, "tipo": "prompt", "error": str(e),
                             "texto_crudo": texto})

    return {
        "nombre": prompt["nombre"],
        "ciclos": CICLOS,
        "exitos": exitos,
        "fallos_prompt": fallos_prompt,
        "fallos_infra": fallos_infra,
        "consistente": exitos == CICLOS,
        "detalles": detalles,
    }


def main():
    cliente = crear_cliente()
    resultados = [probar_prompt(cliente, p) for p in BANCO_DE_PROMPTS]

    salida = Path(__file__).parent / "registro_resultados.json"
    salida.write_text(
        json.dumps({"modelo": MODELO, "resultados": resultados},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for r in resultados:
        estado = "OK" if r["consistente"] else "REVISAR"
        print(f"[{estado}] {r['nombre']}: "
              f"{r['exitos']}/{r['ciclos']} ok | "
              f"prompt={r['fallos_prompt']} infra={r['fallos_infra']}")
    print(f"\nResultados escritos en {salida}")


if __name__ == "__main__":
    main()