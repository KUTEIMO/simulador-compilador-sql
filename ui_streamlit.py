from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from main import analyze


st.set_page_config(page_title="Simulador Didáctico de Compilador SQL", layout="wide")

st.title("Simulador Didáctico de Compilador SQL")
st.write(
    """
    Este simulador muestra de forma educativa cómo un compilador procesa un subconjunto de SQL
    a través de tres fases: léxica, sintáctica (construcción del AST) y semántica (validación con un esquema simulado).
    """
)

with st.expander("¿Qué subconjunto de SQL está soportado?", expanded=False):
    st.markdown(
        """
        - SELECT con lista de columnas o `*`
        - FROM con una sola tabla
        - WHERE con expresiones booleanas simples:
          - Comparaciones: =, !=, <>, <, <=, >, >=
          - Operadores lógicos: AND, OR
          - Paréntesis `( )`
        - Alias de columnas con `AS`
        - Literales: números y cadenas con comillas simples
        """
    )

examples_path = Path("assets/ejemplos.sql")
examples_text = examples_path.read_text("utf-8") if examples_path.exists() else ""

# Estado de la app
if "sql_text" not in st.session_state:
    st.session_state.sql_text = "SELECT id, name FROM students WHERE age > 18;"
if "prefill_sql" not in st.session_state:
    st.session_state.prefill_sql = None
if "fase_idx" not in st.session_state:
    st.session_state.fase_idx = 3  # 1=lex,2=parse,3=semantica (por defecto todo)
if "outcome" not in st.session_state:
    st.session_state.outcome = None
if "last_analyzed_sql" not in st.session_state:
    st.session_state.last_analyzed_sql = None

col_left, col_right = st.columns([2, 1])
with col_left:
    st.subheader("Editor SQL")
    # Si hay prefill, asignarlo ANTES de instanciar el widget
    if st.session_state.prefill_sql:
        st.session_state.sql_text = st.session_state.prefill_sql
        st.session_state.prefill_sql = None
    sql_text = st.text_area(
        label="Escribe tu consulta SQL",
        value=st.session_state.sql_text,
        height=180,
        placeholder="SELECT * FROM students;",
        key="sql_text",
    )
    # No reasignar st.session_state.sql_text aquí para evitar conflicto de Streamlit
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        analyze_btn = st.button("Analizar", type="primary")
    with c2:
        step_mode = st.toggle("Modo paso a paso", value=False, help="Ejecuta por fases: Léxica → Sintáctica → Semántica")
    with c3:
        next_btn = st.button("Siguiente fase") if step_mode else False
with col_right:
    st.subheader("Ejemplos")
    st.code(examples_text, language="sql")
    if st.button("Cargar primer ejemplo"):
        # Cargar la primera sentencia encontrada del archivo de ejemplos
        for line in examples_text.splitlines():
            if line.strip().upper().startswith("SELECT"):
                st.session_state.prefill_sql = line.strip()
                st.rerun()
        st.warning("No se encontraron SELECT en los ejemplos.")

st.markdown("")

# Control de fases
fase_labels = {1: "léxica", 2: "sintáctica", 3: "semántica"}
input_changed = st.session_state.last_analyzed_sql is not None and st.session_state.last_analyzed_sql != sql_text
if input_changed:
    st.warning("La entrada SQL cambió desde el último análisis. Presiona 'Analizar' para actualizar los resultados.")
    if step_mode:
        st.info("Consejo: en modo paso a paso, el flujo se reiniciará desde la fase léxica")

if analyze_btn or (next_btn and not input_changed):
    # Actualizar índice de fase en modo paso a paso
    if step_mode:
        st.session_state.fase_idx = min(3, (st.session_state.fase_idx or 0) + 1) if next_btn else 1
    else:
        st.session_state.fase_idx = 3

    # Ejecutar análisis completo y mostrar según fase
    outcome = analyze(sql_text)
    st.session_state.outcome = outcome
    st.session_state.last_analyzed_sql = sql_text
else:
    outcome = st.session_state.outcome

fase_actual = st.session_state.fase_idx
if outcome is not None:
    # KPIs rápidos
    tok_df = outcome.get("tokens_df")
    ast_obj = outcome.get("ast")
    sym_df = outcome.get("symbols_df")
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Tokens", outcome.get("metrics", {}).get("tokens", 0))
    with k2:
        st.metric("Nodos AST", outcome.get("metrics", {}).get("ast_nodes", 0))
    with k3:
        st.metric("Símbolos", outcome.get("metrics", {}).get("symbols", 0))

    tabs = st.tabs(["📜 Tokens", "🌳 AST", "🧩 Semántica", "⚠️ Errores"])

    with tabs[0]:
        st.info(
            """
            🔍 Fase Léxica: El compilador separa tu código en unidades básicas llamadas "tokens".
            Cada token representa una palabra clave, identificador, operador o literal.
            En un compilador real, esta fase siempre genera tokens (incluso con errores parciales).
            """
        )
        tokens_df: pd.DataFrame | None = outcome.get("tokens_df")
        if tokens_df is not None and not tokens_df.empty:
            # Paleta suave acorde al tema
            def color_row(row):
                m = {
                    "RESERVED": "#e3f2fd",
                    "IDENTIFIER": "#e8f5e9",
                    "OPERATOR": "#fff3e0",
                    "NUMBER": "#f3e5f5",
                    "STRING": "#fce4ec",
                    "SYMBOL": "#f5f5f5",
                }
                return [f"background-color: {m.get(row['tipo'], '#ffffff')}; color:#111;" for _ in row]
            styled = tokens_df.style.apply(color_row, axis=1).hide(axis="index")
            st.dataframe(styled, width="stretch")
        else:
            st.write("No se generaron tokens.")
        if step_mode and fase_actual == 1:
            st.stop()

    with tabs[1]:
        st.info(
            """
            🌳 Fase Sintáctica: Se construye el Árbol de Sintaxis Abstracta (AST) desde los tokens
            generados por la fase léxica. Cada nodo representa una estructura del lenguaje
            (por ejemplo: `SELECT_NODE`, `WHERE_CLAUSE`, `COLUMN_LIST`).
            En un compilador real, el sintáctico opera sobre la salida del léxico.
            """
        )
        ast_graph = outcome.get("ast_graph")
        if ast_graph is not None:
            st.graphviz_chart(ast_graph.source, width="stretch")
            try:
                png_bytes = ast_graph.pipe(format="png")
                st.download_button("Descargar AST (PNG)", data=png_bytes, file_name="ast.png", mime="image/png")
            except Exception:
                pass
        else:
            st.write("No se pudo construir el AST.")
        # Vista textual del AST
        with st.expander("Ver AST como lista jerárquica", expanded=False):
            ast_text = outcome.get("ast_text")
            if ast_text:
                st.code(ast_text)
            else:
                st.write("AST no disponible.")
        if step_mode and fase_actual == 2:
            st.stop()

    with tabs[2]:
        st.info(
            """
            🧩 Fase Semántica: Se valida que la tabla y las columnas existan y que haya compatibilidad
            de tipos. La tabla de símbolos muestra los identificadores con su tipo y ámbito; la de tipos
            describe la información de cada columna.
            """
        )
        symbols_df: pd.DataFrame | None = outcome.get("symbols_df")
        types_df: pd.DataFrame | None = outcome.get("types_df")
        col1, col2 = st.columns(2)
        with col1:
            st.caption("Tabla de símbolos")
            if symbols_df is not None and not symbols_df.empty:
                st.dataframe(symbols_df, width="stretch")
            else:
                st.write("Sin símbolos (posible error previo o SELECT vacío)")
        with col2:
            st.caption("Tabla de tipos")
            if types_df is not None and not types_df.empty:
                st.dataframe(types_df, width="stretch")
            else:
                st.write("Sin tipos (posible error o SELECT con columnas inexistentes)")

    with tabs[3]:
        st.markdown("### ⚠️ Errores detectados")
        errors = outcome.get("errors", [])
        if errors:
            snippet = outcome.get("error_snippet")
            if snippet:
                st.code(snippet)
            for e in errors:
                st.error(e)
            hints = outcome.get("hints", [])
            if hints:
                phase = outcome.get("phase", "")
                with st.expander(f"🛠️ Guía de corrección ({phase})", expanded=True):
                    st.markdown("#### Recomendaciones")
                    for h in hints:
                        st.write("- ", h)
                    st.markdown("#### Ejemplo correcto")
                    if phase == "léxica":
                        st.code("SELECT id, name FROM students", language="sql")
                    elif phase == "sintáctica":
                        st.code("SELECT col1, col2 FROM tabla WHERE col1 >= 0", language="sql")
                    else:
                        st.code("SELECT id, name FROM students WHERE age > 18", language="sql")
                    st.markdown("#### Contraejemplo")
                    if phase == "sintáctica":
                        st.code("SELECT col1 col2 FROM tabla  -- falta coma", language="sql")
                    else:
                        st.code("SELECT id, apellido FROM students  -- 'apellido' no existe", language="sql")
        else:
            st.success("No se detectaron errores")

    st.markdown("---")
    st.caption(
        f"Fase alcanzada: {outcome.get('phase','')} · Ejecuta nuevamente tras corregir si hubo errores."
    )

else:
    st.info(
        """
        Presiona "Analizar" para ejecutar las fases. Se mostrará el resultado hasta la última fase válida.
        Si ocurre un error, el sistema se detendrá en esa fase y explicará el motivo con claridad.
        """
    )

# Footer institucional y créditos
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; font-size: 0.9rem; opacity:0.85;">
      <div><strong>Proyecto de aula — Universidad Simón Bolívar</strong></div>
      <div>Simulador Didáctico de Compilador SQL</div>
      <div>© Eduardo José Soto Herrera — Ingeniería de Sistemas. Todos los derechos reservados.</div>
    </div>
    """,
    unsafe_allow_html=True,
)



