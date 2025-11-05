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
        "ast_text": None,
        "symbols_df": None,
        "types_df": None,
        "errors": [],
        "hints": [],
        "error_snippet": None,
        "phase": "",
        "metrics": {"tokens": 0, "ast_nodes": 0, "symbols": 0},
    }

    # Fase Léxica: En un compilador real, siempre genera tokens (incluso con errores parciales)
    tokens = []
    lex_errors = []
    try:
        tokens = lex_sql(sql_text)
        if not tokens:
            lex_errors.append("No se generaron tokens. Revisa la entrada SQL.")
    except Exception as ex:
        lex_errors.append(f"Error léxico: {ex}")
        # Intentar generar tokens parciales si es posible
        try:
            # En un compilador real, el léxico intenta generar tokens hasta donde puede
            # Por ahora, si hay error, no generamos tokens parciales
            pass
        except Exception:
            pass
    
    # Mostrar tokens generados (incluso si hay errores)
    if tokens:
        lex_rows = tokens_to_table(tokens)
        tokens_df = pd.DataFrame([r.__dict__ for r in lex_rows])
        result["tokens_df"] = tokens_df
        result["metrics"]["tokens"] = len(tokens_df)
    else:
        result["tokens_df"] = pd.DataFrame()
        result["metrics"]["tokens"] = 0
    
    result["errors"].extend(lex_errors)
    result["phase"] = "léxica"
    
    # Si no hay tokens, no podemos continuar
    if not tokens and lex_errors:
        return result

    # Fase Sintáctica: Construye AST desde los tokens del léxico
    # En un compilador real, el sintáctico opera sobre la salida del léxico
    try:
        ast = parse_sql_to_ast(sql_text, tokens=tokens)
        result["ast"] = ast
        result["ast_graph"] = ast_to_graphviz(ast)
        # Texto del AST
        def dump(node: Tree | Token, indent: int = 0, out_lines: list[str] | None = None):
            if out_lines is None:
                out_lines = []
            prefix = "  " * indent
            if isinstance(node, Tree):
                out_lines.append(f"{prefix}{node.data}")
                for ch in node.children:
                    dump(ch, indent + 1, out_lines)
            else:
                out_lines.append(f"{prefix}{node.type}:{str(node)}")
            return out_lines
        ast_lines = dump(ast, 0, [])
        result["ast_text"] = "\n".join(ast_lines)
        # Conteo de nodos
        def count_nodes(node: Tree | Token) -> int:
            if isinstance(node, Tree):
                return 1 + sum(count_nodes(ch) for ch in node.children)
            return 1
        result["metrics"]["ast_nodes"] = count_nodes(ast)
        result["phase"] = "sintáctica"
    except UnexpectedInput as ex:
        # En un compilador real, intentamos construir AST parcial incluso con errores
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
        # En un compilador real, aún intentaríamos construir AST parcial
        # Por ahora, retornamos sin AST si hay error sintáctico
        return result
    except Exception as ex:
        result["errors"].append(f"Error sintáctico: {ex}")
        result["phase"] = "sintáctica"
        return result

    # Fase Semántica
    try:
        schema = load_schema()
        symbols, type_rows, sem_errors = analyze_semantics(result["ast"], schema)
        symbols_df = pd.DataFrame([s.__dict__ for s in symbols])
        result["symbols_df"] = symbols_df
        result["types_df"] = pd.DataFrame(type_rows)
        result["errors"].extend(sem_errors)
        result["metrics"]["symbols"] = 0 if symbols_df is None else len(symbols_df)
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



