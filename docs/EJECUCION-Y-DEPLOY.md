# Ejecución y despliegue

## Demo en producción

**Streamlit Cloud:** https://simulador-compilador-sql-mveyat4jbbhzrcdfjtu5lk.streamlit.app/

## Requisitos

- **Python 3.10+** (CI usa 3.11)
- **Graphviz** instalado en el sistema (binario `dot`) para visualizar el AST en CLI
- Dependencias: `pip install -r requirements.txt`

### Graphviz

- **Windows:** instalar desde https://graphviz.org/download/ y añadir `dot` al PATH
- **Ubuntu/CI:** `sudo apt-get install -y graphviz`

## Desarrollo local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run ui_streamlit.py
```

Abrir la URL que muestra Streamlit (por defecto `http://localhost:8501`).

## CLI (consola)

```bash
python main.py
```

Escribe consultas SQL de ejemplo; el programa muestra tokens, AST (texto/Graphviz) y análisis semántico.

## Pruebas

```bash
pytest -q
# o
python -m tests.smoke_test
```

El workflow [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) ejecuta `pytest` en cada pull request a `main`.

## Despliegue gratuito

### Streamlit Community Cloud

**App publicada:** https://simulador-compilador-sql-mveyat4jbbhzrcdfjtu5lk.streamlit.app/

1. Conectar el repo `KUTEIMO/simulador-compilador-sql`
2. **Main file:** `ui_streamlit.py`
3. Python 3.10+; dependencias desde `requirements.txt`

### Hugging Face Spaces

1. Crear Space → SDK **Streamlit**
2. Vincular este repositorio
3. App file: `ui_streamlit.py`

No configurar secretos: el simulador usa esquema local (`schema_simulado.json`) y SQLite en memoria.

## Problemas frecuentes

| Problema | Solución |
|----------|----------|
| Error al generar PNG del AST | Instalar Graphviz y verificar `dot -V` en terminal |
| `ModuleNotFoundError: lark` | Activar el venv y `pip install -r requirements.txt` |
| Streamlit no arranca | `pip install streamlit` y ejecutar desde la raíz del proyecto |
