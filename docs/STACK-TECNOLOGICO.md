# Stack tecnológico

## Lenguaje y runtime

- **Python 3.10+** — núcleo del simulador y pruebas

## Bibliotecas principales

| Paquete | Rol |
|---------|-----|
| **lark-parser** | Gramática LL/LALR, construcción del AST |
| **streamlit** | Interfaz web didáctica |
| **pandas** | Tablas de tokens, símbolos y resultados |
| **graphviz** (+ binario del sistema) | Visualización del AST en CLI |
| **networkx**, **matplotlib** | Apoyo a visualizaciones |
| **pytest** | Pruebas (`tests/smoke_test.py`) |

Ver versiones instaladas en `requirements.txt`.

## Datos y esquema

- `schema_simulado.json` — tablas y columnas para el analizador semántico
- `database_simulator.py` — SQLite en memoria para ejecutar consultas válidas en la demo

## CI

- GitHub Actions: Python 3.11, Graphviz, `pytest -q` en pull requests

## Extensiones posibles

- Más construcciones SQL (`JOIN`, `INSERT`, subconsultas)
- Reglas semánticas adicionales (tipos estrictos, agregaciones)
- Exportación del AST ya implementada en commits recientes del núcleo
