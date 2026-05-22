# Simulador de compilador SQL (didáctico)

Proyecto académico de **Teoría de compiladores** — Universidad Simón Bolívar (Ingeniería de Sistemas). Simula las fases **léxica**, **sintáctica** y **semántica** de un subconjunto de SQL: tokens, AST (Lark), tabla de símbolos y ejecución demo sobre SQLite en memoria. Interfaz paso a paso con **Streamlit**.

**Repositorio:** https://github.com/KUTEIMO/simulador-compilador-sql  
**Demo (Streamlit Cloud):** https://simulador-compilador-sql-mveyat4jbbhzrcdfjtu5lk.streamlit.app/

---

## Qué hace (resumen)

| Fase | Módulo | Salida |
|------|--------|--------|
| Léxico | `lexer.py` | Tokens categorizados y errores léxicos |
| Sintáctico | `parser_sql.py` | AST (Lark) |
| Semántico | `semantic_analyzer.py` | Símbolos, tipos vs `schema_simulado.json` |
| Ejecución demo | `database_simulator.py` | Resultado sobre BD simulada |
| UI | `ui_streamlit.py` | Visualización didáctica |
| CLI | `main.py` | Mismo pipeline en consola + Graphviz |

### SQL soportado (subconjunto)

- `SELECT` (columnas o `*`), `FROM` (una tabla), `WHERE` con comparaciones y `AND`/`OR`
- `AS`, literales numéricos y cadenas con comillas simples

---

## Inicio rápido

Usa la **[demo en línea](https://simulador-compilador-sql-mveyat4jbbhzrcdfjtu5lk.streamlit.app/)** o clona el repo:

```bash
git clone https://github.com/KUTEIMO/simulador-compilador-sql.git
cd simulador-compilador-sql
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

**Interfaz (recomendado):**

```bash
streamlit run ui_streamlit.py
```

**CLI:**

```bash
python main.py
```

**Pruebas:**

```bash
pytest -q
```

Guía completa: [docs/EJECUCION-Y-DEPLOY.md](docs/EJECUCION-Y-DEPLOY.md).

---

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [docs/EJECUCION-Y-DEPLOY.md](docs/EJECUCION-Y-DEPLOY.md) | Instalación, Graphviz, tests, deploy Streamlit/Hugging Face |
| [docs/STACK-TECNOLOGICO.md](docs/STACK-TECNOLOGICO.md) | Python, Lark, Streamlit, dependencias |
| [docs/ARQUITECTURA-Y-FLUJOS.md](docs/ARQUITECTURA-Y-FLUJOS.md) | Pipeline del compilador y carpetas |
| [docs/NOTAS-ACADEMICAS.md](docs/NOTAS-ACADEMICAS.md) | Contexto, objetivos y metodología del proyecto de aula |
| [SECURITY.md](SECURITY.md) | Reporte de vulnerabilidades |

---

## Estructura del código

```text
simulador-compilador-sql/
├── lexer.py                 # Analizador léxico
├── parser_sql.py            # Gramática y AST
├── semantic_analyzer.py     # Análisis semántico
├── database_simulator.py    # SQLite demo
├── main.py                  # Entrada CLI
├── ui_streamlit.py          # Interfaz Streamlit
├── schema_simulado.json     # Esquema de tablas/columnas
├── assets/ejemplos.sql      # Consultas de ejemplo
├── tests/smoke_test.py      # Pruebas smoke (pytest)
├── requirements.txt
└── docs/
```

---

## Despliegue

**Producción:** https://simulador-compilador-sql-mveyat4jbbhzrcdfjtu5lk.streamlit.app/

- **Streamlit Community Cloud:** entrypoint `ui_streamlit.py`, Python 3.10+, `requirements.txt`
- **Hugging Face Spaces:** Space tipo Streamlit, mismo entrypoint

No requiere `.env` ni credenciales para la demo.

---

## Créditos

**Eduardo José Soto Herrera** — Ingeniería de Sistemas, USB Cúcuta.

## Licencia

[MIT](LICENSE)
