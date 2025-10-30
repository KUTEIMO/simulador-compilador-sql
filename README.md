# Simulador de Compilador SQL Didáctico

Proyecto académico para simular las etapas de compilación de un subconjunto de SQL: análisis léxico, sintáctico y semántico, con una UI en Streamlit y pruebas básicas.

## Requisitos

- Python 3.10+
- Dependencias del archivo `requirements.txt`

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Ejecución (CLI)

```bash
python main.py
```

## Ejecución (UI Streamlit)

```bash
streamlit run ui_streamlit.py
```

## Estructura

- `lexer.py`: Analizador léxico
- `parser_sql.py`: Analizador sintáctico
- `semantic_analyzer.py`: Analizador semántico
- `ui_streamlit.py`: Interfaz didáctica
- `tests/`: Pruebas
- `assets/`: Recursos de ejemplo

## Licencia

Uso académico.
