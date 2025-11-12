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
        st.session_state.last_analyzed_sql = None  # Resetear para forzar re-análisis
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
        analyze_btn = st.button("Analizar", type="primary", key="analyze_button")
    with c2:
        step_mode = st.toggle("Modo paso a paso", value=False, help="Ejecuta por fases: Léxica → Sintáctica → Semántica")
    with c3:
        next_btn = st.button("Siguiente fase") if step_mode else False
with col_right:
    st.subheader("Ejemplos")
    st.text_area(
        label="Ejemplos disponibles",
        value=examples_text,
        height=110,
        key="examples_text_area",
        disabled=True,
        label_visibility="collapsed",
    )
    if st.button("Cargar primer ejemplo"):
        # Cargar la primera sentencia encontrada del archivo de ejemplos
        for line in examples_text.splitlines():
            if line.strip().upper().startswith("SELECT"):
                st.session_state.prefill_sql = line.strip()
                st.rerun()
        st.warning("No se encontraron SELECT en los ejemplos.")

# Control de fases - ejecutar análisis cuando se presiona el botón o cambia el texto
fase_labels = {1: "léxica", 2: "sintáctica", 3: "semántica"}
should_analyze = analyze_btn or (next_btn and step_mode)

# Si cambió el texto, resetear el resultado anterior
if st.session_state.last_analyzed_sql != sql_text:
    st.session_state.outcome = None
    st.session_state.fase_idx = 3  # Resetear a fase completa

if should_analyze:
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

# Sección didáctica de errores (entre entrada y métricas)
if outcome is not None:
    errors = outcome.get("errors", [])
    if errors:
        st.markdown("### 📚 Zona de Aprendizaje: Errores Detectados")
        phase = outcome.get("phase", "")
        if phase:
            st.info(f"🔍 **Fase donde ocurrió el error:** {phase.capitalize()}")
        
        for idx, error in enumerate(errors, 1):
            error_preview = error[:80] + "..." if len(error) > 80 else error
            with st.expander(f"❌ Error {idx}: {error_preview}", expanded=idx == 1):
                st.error(f"**Detalle completo:** {error}")
                snippet = outcome.get("error_snippet")
                if snippet and idx == 1:
                    st.markdown("**Código donde ocurrió el error:**")
                    st.code(snippet, language="sql")
        
        hints = outcome.get("hints", [])
        if hints:
            st.markdown("#### 💡 Sugerencias para corregir:")
            for hint in hints:
                st.markdown(f"- {hint}")
        
        # Ejemplos según la fase
        st.markdown("#### ✅ Ejemplos correctos según la fase:")
        if phase == "léxica":
            st.code("SELECT id, name FROM students;", language="sql")
            st.caption("Asegúrate de usar palabras reservadas correctas (SELECT, FROM, WHERE, etc.)")
        elif phase == "sintáctica":
            st.code("SELECT col1, col2 FROM tabla WHERE col1 >= 0;", language="sql")
            st.caption("Verifica la estructura: SELECT columnas FROM tabla [WHERE condición]")
        elif phase == "semántica":
            st.code("SELECT id, name FROM students WHERE age > 18;", language="sql")
            st.caption("Asegúrate de que las tablas y columnas existan en el esquema")
        else:
            st.code("SELECT id, name FROM students WHERE age > 18;", language="sql")
        
        st.markdown("---")

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

    tabs = st.tabs([
        "📜 Tabla de Tokens (Fase Léxica)",
        "🌳 AST (Fase Sintáctica)",
        "🧩 Tablas Tipos y Símbolos (Fase Semántica)",
        "🗂️ Resultado SQL Real",
        "⚠️ Errores (Fase Semántica)"
    ])

    with tabs[0]:
        # Resultado REAL primero
        st.markdown("### 🔍 Fase Léxica - Tokens Generados")
        st.caption("Tokens generados por el analizador léxico (resultado real del compilador)")
        tokens_df: pd.DataFrame | None = outcome.get("tokens_df")
        if tokens_df is not None and not tokens_df.empty:
            # Eliminar columnas 3 y 4 (linea y columna), mantener solo token y tipo
            tokens_display = tokens_df[['token', 'tipo']].copy()
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
            styled = tokens_display.style.apply(color_row, axis=1).hide(axis="index")
            st.dataframe(styled, use_container_width=True)
        else:
            st.write("No se generaron tokens.")
        
        # Sección didáctica separada
        st.markdown("---")
        with st.expander("📚 Explicación Didáctica: ¿Cómo funciona el Análisis Léxico?", expanded=False):
            st.markdown("""
            #### ¿Qué es el Análisis Léxico?
            El análisis léxico es la **primera fase** de un compilador. Su función es convertir el código fuente
            en una secuencia de **tokens** (unidades básicas del lenguaje).
            
            #### ¿Qué es un Token?
            Un token es la unidad más pequeña con significado en el lenguaje. Por ejemplo:
            - **Palabras reservadas**: `SELECT`, `FROM`, `WHERE`, `AND`, `OR`
            - **Identificadores**: Nombres de tablas, columnas (ej: `students`, `id`, `age`)
            - **Operadores**: `=`, `!=`, `>`, `<`, `>=`, `<=`
            - **Literales**: Números (`18`) y cadenas (`'texto'`)
            - **Símbolos**: `,`, `;`, `(`, `)`
            
            #### ¿Cómo funciona?
            1. El analizador léxico **lee el código fuente** carácter por carácter
            2. **Agrupa caracteres** según reglas definidas (palabras reservadas, identificadores, etc.)
            3. **Genera tokens** con su categoría (tipo)
            4. **Ignora espacios y comentarios** (dependiendo del lenguaje)
            
            #### ¿Por qué es importante?
            - **Separación de responsabilidades**: El léxico solo se preocupa de identificar tokens
            - **Independiente de sintaxis**: No necesita entender la estructura completa
            - **Eficiencia**: Puede procesar el código en una sola pasada
            - **Manejo de errores**: Puede detectar caracteres inválidos o tokens mal formados
            
            **Ejemplo**: `SELECT id FROM students` se convierte en:
            - Token: `SELECT` (tipo: RESERVED)
            - Token: `id` (tipo: IDENTIFIER)
            - Token: `FROM` (tipo: RESERVED)
            - Token: `students` (tipo: IDENTIFIER)
            """)
        
        if step_mode and fase_actual == 1:
            st.stop()

    with tabs[1]:
        # AST REAL (como compilador)
        st.markdown("### 🌳 Árbol de Sintaxis Abstracta (AST) - Resultado Real")
        st.caption("Este es el AST generado por el compilador, mostrando solo los tokens organizados jerárquicamente según la estructura semántica.")
        
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
        
        # Sección didáctica separada
        st.markdown("---")
        with st.expander("📚 Explicación Didáctica: ¿Cómo funciona el AST?", expanded=False):
            st.markdown("""
            #### ¿Qué es un AST?
            El Árbol de Sintaxis Abstracta (AST) es una representación en árbol de la estructura sintáctica del código fuente.
            En un compilador SQL real, el AST se construye **desde los tokens** generados por el analizador léxico.
            
            #### Estructura del AST mostrado arriba:
            - **SELECT (raíz)**: Representa la consulta completa
            - **Columnas**: Tokens de las columnas seleccionadas (id, name, etc.)
            - **FROM**: Palabra clave que indica la fuente de datos
            - **Tabla**: Nombre de la tabla (students)
            - **WHERE**: Cláusula de condición (opcional)
            - **Operador**: Operador de comparación (>, <, =, etc.)
            - **Left/Right**: Lado izquierdo y derecho de la comparación
            
            #### ¿Por qué esta estructura?
            En compiladores reales, el AST refleja la **semántica** del lenguaje, no solo la sintaxis.
            La estructura jerárquica permite al compilador:
            1. Validar la semántica (tablas y columnas existen)
            2. Optimizar consultas
            3. Generar código de ejecución
            
            **Ejemplo**: `SELECT id, name FROM students WHERE age > 18`
            - El AST agrupa `age`, `>`, `18` bajo el operador `>`
            - Esto permite al compilador entender que es una comparación binaria
            """)
        
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
        # Tablas REALES (como compilador)
        st.markdown("### 🧩 Fase Semántica - Tablas de Símbolos y Tipos")
        st.caption("Tablas generadas por el compilador según la literatura estándar de compiladores.")
        
        symbols_df: pd.DataFrame | None = outcome.get("symbols_df")
        types_df: pd.DataFrame | None = outcome.get("types_df")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📋 Tabla de Símbolos")
            st.caption("Identificadores con su tipo, ámbito y categoría (como en compiladores reales)")
            if symbols_df is not None and not symbols_df.empty:
                # Mostrar columnas relevantes para compilador real
                display_cols = ['Nombre', 'Tipo', 'Ámbito', 'Categoría', 'Tamaño', 'Offset']
                available_cols = [c for c in display_cols if c in symbols_df.columns]
                if available_cols:
                    st.dataframe(symbols_df[available_cols], use_container_width=True, hide_index=True)
                else:
                    st.dataframe(symbols_df, use_container_width=True, hide_index=True)
            else:
                st.write("Sin símbolos (posible error previo o SELECT vacío)")
        
        with col2:
            st.markdown("#### 📊 Tabla de Tipos")
            st.caption("Información de tipos de datos de las columnas (nombre, tipo, tamaño, tabla, ámbito)")
            if types_df is not None and not types_df.empty:
                st.dataframe(types_df, use_container_width=True, hide_index=True)
            else:
                st.write("Sin tipos (posible error o SELECT con columnas inexistentes)")
        
        # Sección didáctica separada
        st.markdown("---")
        with st.expander("📚 Explicación Didáctica: Tablas de Símbolos y Tipos", expanded=False):
            st.markdown("""
            #### ¿Qué es una Tabla de Símbolos?
            La tabla de símbolos es una estructura de datos que almacena información sobre los identificadores
            (nombres de variables, tablas, columnas) encontrados en el programa. En compiladores reales:
            
            - **Nombre**: Identificador (ej: `students`, `id`, `age`)
            - **Tipo**: Tipo de dato (ej: `INT`, `VARCHAR`, `TABLE`)
            - **Ámbito **: Dónde es visible el símbolo (ej: `GLOBAL`, `students.SELECT`, `students.WHERE`)
            - **Categoría**: Qué tipo de símbolo es (`table`, `column`, `variable`)
            
            #### ¿Qué es una Tabla de Tipos?
            La tabla de tipos almacena información detallada sobre los tipos de datos:
            - **Nombre**: Nombre de la columna
            - **Tipo**: Tipo de dato (INT, VARCHAR, etc.)
            - **Tamaño**: Tamaño en bytes o caracteres
            - **Tabla**: A qué tabla pertenece
            - **Ámbito**: Dónde se usa (SELECT, WHERE, etc.)
            
            #### ¿Por qué son importantes?
            Estas tablas permiten al compilador:
            1. **Validar existencia**: Verificar que tablas/columnas existen
            2. **Verificar tipos**: Asegurar compatibilidad de tipos en operaciones
            3. **Resolución de nombres**: Saber qué símbolo se refiere a qué
            4. **Optimización**: Usar información de tipos para optimizar consultas
            """)

    with tabs[3]:
        st.markdown("### 🗂️ Resultado de la Consulta en SQLite real")
        st.caption("Salida real del motor SQL didáctico (SQLite en memoria) utilizando los datos de ejemplo.")
        db_df: pd.DataFrame | None = outcome.get("db_result_df")
        db_error = outcome.get("db_error")

        if db_df is not None:
            if not db_df.empty:
                st.success("La consulta se ejecutó correctamente en la base de datos simulada.")
                st.dataframe(db_df, use_container_width=True, hide_index=True)
            else:
                st.info("La consulta se ejecutó, pero no devolvió filas.")
        if db_error:
            st.error(f"Error del motor SQL real: {db_error}")
        if db_df is None and not db_error:
            st.info("Ejecuta la consulta para visualizar el resultado real del motor SQL.")

        summary = outcome.get("learning_summary")
        if summary:
            st.markdown("#### 📝 Resumen del recorrido completo")
            st.write(summary)

        st.markdown("---")
        st.caption("La base incluye tablas: students, courses, enrollments con registros de ejemplo para practicar.")

    with tabs[4]:
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
    # Si no hay resultado pero hay texto, mostrar mensaje de ayuda
    if sql_text.strip():
        st.info("💡 Presiona el botón **'Analizar'** para procesar tu consulta SQL y ver las fases del compilador en acción.")
    else:
        st.info("✍️ Escribe una consulta SQL en el editor y presiona **'Analizar'** para comenzar.")

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



