from __future__ import annotations

from typing import Dict, Any, List, Tuple
import difflib

import pandas as pd
from graphviz import Digraph
from lark import Tree, Token, UnexpectedInput

from parser_sql import parse_sql_to_ast, lex_sql
from lexer import tokens_to_table
from semantic_analyzer import load_schema, analyze_semantics, Symbol


def ast_to_graphviz(ast: Tree) -> Digraph:
    graph = Digraph("AST", format="png")
    graph.attr(rankdir="TB", fontsize="10", fontname="Helvetica")

    def node_label(n: Tree | Token) -> str:
        if isinstance(n, Tree):
            return n.data
        if isinstance(n, Token):
            return f"{n.type}: {str(n)}"
        return str(n)

    def add_nodes_edges(node: Tree | Token, parent_id: str | None = None, counter=[0]):
        counter[0] += 1
        node_id = f"n{counter[0]}"
        label = node_label(node)
        graph.node(node_id, label)
        if parent_id is not None:
            graph.edge(parent_id, node_id)
        if isinstance(node, Tree):
            for ch in node.children:
                add_nodes_edges(ch, node_id, counter)
        return node_id

    add_nodes_edges(ast)
    return graph


def analyze(sql_text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "tokens_df": None,
        "ast": None,
        "ast_graph": None,
        "symbols_df": None,
        "types_df": None,
        "errors": [],
        "hints": [],
        "error_snippet": None,
        "phase": "",
    }

    # Fase Léxica
    try:
        tokens = lex_sql(sql_text)
        lex_rows = tokens_to_table(tokens)
        result["tokens_df"] = pd.DataFrame([r.__dict__ for r in lex_rows])
        result["phase"] = "léxica"
    except Exception as ex:
        result["errors"].append(f"Error léxico: {ex}")
        result["phase"] = "léxica"
        return result

    # Fase Sintáctica
    try:
        ast = parse_sql_to_ast(sql_text)
        result["ast"] = ast
        result["ast_graph"] = ast_to_graphviz(ast)
        result["phase"] = "sintáctica"
    except UnexpectedInput as ex:
        # Mensaje claro con línea/columna cuando sea posible
        line = getattr(ex, 'line', None)
        column = getattr(ex, 'column', None)
        if line and column:
            result["errors"].append(f"Error sintáctico en línea {line}, columna {column}: {ex}")
            try:
                snippet = ex.get_context(sql_text)
                result["error_snippet"] = snippet
            except Exception:
                pass
            # Sugerencias didácticas básicas según tokens esperados
            expected = set()
            try:
                expected = set(ex.expected)
            except Exception:
                expected = set()
            hints: List[str] = []
            if "FROM" in expected:
                hints.append("Agrega la cláusula FROM: FROM <tabla>")
            if "COMMA" in expected:
                hints.append("Puede faltar una coma entre columnas, por ejemplo: SELECT col1, col2")
            if "AS" in expected:
                hints.append("Si estás usando alias, utiliza AS: SELECT col AS alias")
            if "LPAREN" in expected or "RPAREN" in expected:
                hints.append("Revisa paréntesis balanceados en la expresión WHERE")
            if "EQ" in expected or "NEQ" in expected or "LT" in expected or "LTE" in expected or "GT" in expected or "GTE" in expected:
                hints.append("Falta un operador de comparación: =, !=, <>, <, <=, >, >=")
            if hints:
                result["hints"].extend(hints)
        else:
            result["errors"].append(f"Error sintáctico: {ex}")
        result["phase"] = "sintáctica"
        return result
    except Exception as ex:
        result["errors"].append(f"Error sintáctico: {ex}")
        result["phase"] = "sintáctica"
        return result

    # Fase Semántica
    try:
        schema = load_schema()
        symbols, type_rows, sem_errors = analyze_semantics(result["ast"], schema)
        result["symbols_df"] = pd.DataFrame([s.__dict__ for s in symbols])
        result["types_df"] = pd.DataFrame(type_rows)
        result["errors"].extend(sem_errors)
        # Sugerencias semánticas
        if sem_errors:
            tables = list(schema.get("tables", {}).keys())
            for err in sem_errors:
                if err.startswith("Tabla inexistente:"):
                    result["hints"].append("Tabla no encontrada. Tablas disponibles: " + ", ".join(tables))
                if err.startswith("Columna inexistente en SELECT:") or err.startswith("Columna inexistente en WHERE:"):
                    # ofrecer columnas similares
                    missing = err.split(":",1)[1].strip()
                    # intentar detectar tabla usada
                    table_used = None
                    try:
                        table_used = result["symbols_df"]["scope"].iloc[0].split(".")[-1]
                    except Exception:
                        # fallback: primera tabla del esquema
                        table_used = tables[0] if tables else None
                    if table_used and table_used in schema.get("tables", {}):
                        cols = list(schema["tables"][table_used].keys())
                        close = difflib.get_close_matches(missing, cols, n=3, cutoff=0.5)
                        if close:
                            result["hints"].append(f"¿Querías referirte a: {', '.join(close)}?")
                        else:
                            result["hints"].append("Columnas disponibles en la tabla " + table_used + ": " + ", ".join(cols))
        result["phase"] = "semántica"
    except Exception as ex:
        result["errors"].append(f"Error semántico: {ex}")
        result["phase"] = "semántica"

    return result



