# Simulador de Compilador SQL Didáctico

Proyecto de aula de la Universidad Simón Bolívar que busca recrear un simulador pedagógico para que estudiantes principiantes experimenten, de forma didáctica, cómo funciona un compilador. A través de tres módulos principales (analizador léxico, analizador sintáctico y comprobador semántico), el sistema transforma consultas SQL en tokens, construye un Árbol de Sintaxis Abstracta (AST) y realiza verificaciones semánticas contra un esquema de base de datos simulado. La interfaz interactiva facilita la visualización paso a paso y la detección de errores con mensajes explicativos.

El objetivo es reducir la brecha entre teoría y práctica en la enseñanza de la teoría de compiladores, proporcionando ejercicios concretos, visualizaciones y retroalimentación inmediata. El desarrollo está implementado en Python (Lark para gramática y parsing; Streamlit para GUI) y el código está organizado para facilitar extensiones (más construcciones de SQL, nuevos checks semánticos, etc.).

## Objetivos

- Diseñar e implementar un simulador didáctico de compilador SQL que enseñe las fases léxica, sintáctica y semántica.
- Implementar un analizador léxico que produzca tokens categorizados y detecte errores léxicos.
- Diseñar una gramática y un analizador sintáctico que construyan un AST representativo.
- Implementar comprobaciones semánticas básicas (existencia de tablas/columnas, compatibilidad de tipos).
- Desarrollar una interfaz interactiva que visualice tokens, AST y tabla de símbolos.
- Validar el simulador mediante casos de prueba y una prueba piloto con estudiantes (pre/post test), midiendo mejoras en la comprensión.

## Metodología

- Desarrollo incremental en sprints cortos.
- Pruebas unitarias y funcionales con `pytest` (ver carpeta `tests/`).
- Prueba piloto con estudiantes en un congreso académico.
- Revisión bibliográfica (Aho et al., Ruiz Catalán) y documentación técnica.

## Requisitos

- Python 3.10+
- Dependencias del archivo `requirements.txt`

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Ejecución local

CLI:
```bash
python main.py
```

UI (Streamlit):
```bash
streamlit run ui_streamlit.py
```

## Despliegue gratuito (opciones)

- Streamlit Community Cloud: conecta este repositorio y usa el archivo `ui_streamlit.py` como entrypoint. Requiere Python 3.10+ y usará `requirements.txt` automáticamente.
- Hugging Face Spaces (Gradio/Streamlit): crea un Space tipo Streamlit y selecciona este repo; establece `ui_streamlit.py` como app file.

En ambos casos, no se necesitan secretos ni credenciales. El proyecto no expone datos sensibles y las dependencias son públicas.

## Subconjunto de SQL soportado (resumen)

- SELECT con lista de columnas o `*`
- FROM con una sola tabla
- WHERE con expresiones booleanas simples (comparaciones y `AND`/`OR` con paréntesis)
- Alias con `AS`, literales numéricos y cadenas con comillas simples

## Estructura

- `lexer.py`: Analizador léxico
- `parser_sql.py`: Analizador sintáctico (AST)
- `semantic_analyzer.py`: Comprobaciones semánticas (símbolos y tipos sobre esquema simulado)
- `ui_streamlit.py`: Interfaz didáctica paso a paso
- `tests/`: Pruebas (`pytest`)
- `assets/`: Recursos de ejemplo (consultas SQL)

## Referencias

- Aho, A. V., Sethi, R., Ullman, J. D. (2006). Compilers: Principles, Techniques, and Tools.
- Ruiz Catalán (2010). Textos fundamentales de compiladores.
- Lark-parser (2023). Lark — A modern parsing library for Python: https://github.com/lark-parser/lark
- Streamlit Inc. (2023). Documentación: https://docs.streamlit.io
- Python Software Foundation (2023). https://www.python.org/doc/
- Graphviz (2024). https://graphviz.org

## Créditos y derechos

Proyecto de aula — Universidad Simón Bolívar.

© Eduardo José Soto Herrera — Ingeniería de Sistemas. Todos los derechos reservados.
