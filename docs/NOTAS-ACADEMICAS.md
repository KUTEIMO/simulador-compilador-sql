# Notas académicas del proyecto

## Problema que aborda

En teoría de compiladores los estudiantes estudian autómatas, gramáticas y tablas, pero con poca visibilidad del comportamiento real de un compilador. Este simulador acerca esas fases a un lenguaje conocido (SQL) con retroalimentación visual e inmediata.

## Objetivo general

Diseñar e implementar un simulador didáctico que enseñe las fases **léxica**, **sintáctica** y **semántica** sobre consultas SQL simples.

## Objetivos específicos

- Analizador léxico con tokens categorizados y detección de errores léxicos
- Gramática y parser que construyan un AST representativo
- Comprobaciones semánticas (tablas, columnas, tipos compatibles)
- Interfaz que muestre tokens, AST y tabla de símbolos
- Validación con pruebas automatizadas y piloto con estudiantes (congreso académico)

## Metodología

- Desarrollo incremental en sprints cortos
- Pruebas con `pytest` (`tests/`)
- Revisión bibliográfica: Aho et al., Ruiz Catalán; documentación de Lark y Streamlit

## Referencias (resumen)

- Aho, Sethi, Ullman — *Compilers: Principles, Techniques, and Tools*
- Ruiz Catalán — textos de compiladores
- [Lark](https://github.com/lark-parser/lark), [Streamlit](https://docs.streamlit.io), [Graphviz](https://graphviz.org)

## Autoría

**Eduardo José Soto Herrera** — Ingeniería de Sistemas, Universidad Simón Bolívar.
