# Arquitectura y flujos

## Pipeline del compilador (consulta SQL)

```text
Entrada SQL
    │
    ▼
┌─────────────┐
│   lexer     │  → lista de tokens (categorías, posición)
└──────┬──────┘
       ▼
┌─────────────┐
│ parser_sql  │  → AST (árbol Lark)
└──────┬──────┘
       ▼
┌─────────────────────┐
│ semantic_analyzer   │  → símbolos, errores (tablas/columnas/tipos)
└──────┬──────────────┘
       ▼
┌─────────────────────┐
│ database_simulator  │  → resultado demo (opcional, si la consulta es válida)
└─────────────────────┘
```

## Puntos de entrada

| Archivo | Uso |
|---------|-----|
| `ui_streamlit.py` | UI paso a paso para estudiantes |
| `main.py` | Demostración en terminal + Graphviz |

Ambos reutilizan `lex_sql`, `parse_sql_to_ast`, `analyze_semantics` y el esquema cargado desde JSON.

## Módulos

- **`lexer.py`** — Tokenización; reservadas (`SELECT`, `FROM`, …)
- **`parser_sql.py`** — Gramática del subconjunto SQL; errores sintácticos
- **`semantic_analyzer.py`** — Tabla de símbolos y reglas sobre el esquema
- **`database_simulator.py`** — Motor SQLite temporal para “ejecutar” SELECT válidos

## Recursos

- `assets/ejemplos.sql` — consultas de referencia para la UI o pruebas manuales
