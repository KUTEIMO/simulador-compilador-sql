from __future__ import annotations

from typing import Dict, Any, List, Tuple
import difflib
import re

import pandas as pd
from graphviz import Digraph
from lark import Tree, Token, UnexpectedInput

from parser_sql import parse_sql_to_ast, lex_sql
from lexer import tokens_to_table
from semantic_analyzer import load_schema, analyze_semantics, Symbol
from database_simulator import execute_demo_query

RESERVED_KEYWORDS = {"SELECT", "FROM", "WHERE", "AND", "OR", "AS"}


def ast_to_graphviz(ast: Tree) -> Digraph:
    """
    Genera visualización del AST navegando el árbol Tree real según la estructura semántica.
    Estructura como compilador SQL real según la literatura:
    Query (SELECT) -> SelectExprs (columnas), From (tabla), Where -> BinaryExpression (Left, Operator, Right)
    Solo muestra tokens reales extraídos del árbol.
    """
    graph = Digraph("AST", format="png")
    graph.attr(rankdir="TB", fontsize="10", fontname="Helvetica")
    
    # Diccionario para mapear tokens a IDs de nodos
    token_to_node_id = {}
    node_counter = [0]  # Contador para IDs únicos
    
    def get_node_id(token_value: str) -> str:
        """Obtiene o crea un ID de nodo para un token"""
        if token_value not in token_to_node_id:
            node_counter[0] += 1
            token_to_node_id[token_value] = f"n{node_counter[0]}"
            graph.node(token_to_node_id[token_value], token_value, shape="ellipse")
        return token_to_node_id[token_value]
    
    def extract_token_value(node: Tree | Token) -> str | None:
        """Extrae el valor del token real desde un nodo Tree o Token"""
        if isinstance(node, Token):
            return str(node)
        elif isinstance(node, Tree):
            # Para nodos IDENT, NUMBER, STRING, OP, STAR, extraer el token interno
            if node.data in {"IDENT", "NUMBER", "STRING", "OP", "STAR"}:
                if node.children:
                    # El primer hijo es el Token
                    if isinstance(node.children[0], Token):
                        return str(node.children[0])
                    # Si es un Tree anidado (caso raro), buscar recursivamente
                    elif isinstance(node.children[0], Tree):
                        return extract_token_value(node.children[0])
            # Para palabras reservadas, devolver el nombre del nodo
            if node.data in {"SELECT", "FROM", "WHERE", "AND", "OR"}:
                return node.data
        return None
    
    def find_token_in_tree(node: Tree, target_types: set) -> Token | None:
        """Busca un token de tipo específico en el árbol"""
        if isinstance(node, Token):
            if node.type in target_types:
                return node
        elif isinstance(node, Tree):
            for child in node.children:
                result = find_token_in_tree(child, target_types)
                if result:
                    return result
        return None
    
    # Navegar el árbol SELECT_NODE
    if not isinstance(ast, Tree) or ast.data != "SELECT_NODE":
        graph.node("n1", "AST inválido")
        return graph
    
    # SELECT es la raíz (Query)
    select_node_id = get_node_id("SELECT")
    root_id = select_node_id
    
    # Procesar hijos de SELECT_NODE: COLUMN_LIST, TABLE, WHERE_CLAUSE
    for child in ast.children:
        if isinstance(child, Tree):
            if child.data == "COLUMN_LIST":
                # COLUMN_LIST: extraer columnas (COLUMN -> IDENT)
                for col_node in child.children:
                    if isinstance(col_node, Tree) and col_node.data == "COLUMN":
                        # COLUMN tiene IDENT como hijo
                        if col_node.children:
                            ident_node = col_node.children[0]
                            if isinstance(ident_node, Tree) and ident_node.data == "IDENT":
                                if ident_node.children and isinstance(ident_node.children[0], Token):
                                    col_token = ident_node.children[0]
                                    col_id = get_node_id(str(col_token))
                                    graph.edge(root_id, col_id)
                    elif isinstance(col_node, Tree) and col_node.data == "STAR":
                        # SELECT *
                        star_id = get_node_id("*")
                        graph.edge(root_id, star_id)
            
            elif child.data == "TABLE":
                # TABLE: FROM y tabla
                from_id = get_node_id("FROM")
                graph.edge(root_id, from_id)
                
                # Extraer nombre de tabla
                if child.children:
                    table_node = child.children[0]
                    if isinstance(table_node, Tree) and table_node.data == "IDENT":
                        if table_node.children and isinstance(table_node.children[0], Token):
                            table_token = table_node.children[0]
                            table_id = get_node_id(str(table_token))
                            graph.edge(from_id, table_id)
            
            elif child.data == "WHERE_CLAUSE":
                # WHERE_CLAUSE: WHERE y expresión booleana
                where_id = get_node_id("WHERE")
                graph.edge(root_id, where_id)
                
                # Procesar expresión booleana (AND/OR/COMPARE)
                if child.children:
                    expr_node = child.children[0]
                    _process_boolean_expr(expr_node, where_id, graph, get_node_id, extract_token_value)
    
    return graph


def _process_boolean_expr(expr_node: Tree, parent_id: str, graph: Digraph, 
                           get_node_id, extract_token_value):
    """Procesa expresiones booleanas: AND, OR, COMPARE"""
    if not isinstance(expr_node, Tree):
        return
    
    if expr_node.data == "COMPARE":
        # COMPARE: [OP, left, right]
        # Estructura: Operator -> Left, Right
        if len(expr_node.children) >= 3:
            op_node = expr_node.children[0]  # OP
            left_node = expr_node.children[1]  # IDENT/NUMBER/STRING
            right_node = expr_node.children[2]  # IDENT/NUMBER/STRING
            
            # Extraer operador
            op_value = extract_token_value(op_node)
            if op_value:
                op_id = get_node_id(op_value)
                graph.edge(parent_id, op_id)
                
                # Left: puede ser IDENT anidado
                left_value = extract_token_value(left_node)
                if left_value:
                    left_id = get_node_id(left_value)
                    graph.edge(op_id, left_id)
                elif isinstance(left_node, Tree):
                    # Si es IDENT anidado, buscar recursivamente
                    if left_node.data == "IDENT" and left_node.children:
                        nested_value = extract_token_value(left_node.children[0])
                        if nested_value:
                            left_id = get_node_id(nested_value)
                            graph.edge(op_id, left_id)
                
                # Right: puede ser NUMBER, STRING, o IDENT
                right_value = extract_token_value(right_node)
                if right_value:
                    right_id = get_node_id(right_value)
                    graph.edge(op_id, right_id)
                elif isinstance(right_node, Tree):
                    # Si es IDENT anidado, buscar recursivamente
                    if right_node.data == "IDENT" and right_node.children:
                        nested_value = extract_token_value(right_node.children[0])
                        if nested_value:
                            right_id = get_node_id(nested_value)
                            graph.edge(op_id, right_id)
    
    elif expr_node.data == "AND" or expr_node.data == "and":
        # AND: [left, (token AND opcional), right]
        # Filtrar tokens intermedios y procesar solo expresiones Tree
        and_id = get_node_id("AND")
        graph.edge(parent_id, and_id)
        
        # Filtrar solo nodos Tree (ignorar tokens intermedios)
        tree_children = [ch for ch in expr_node.children if isinstance(ch, Tree)]
        if len(tree_children) >= 2:
            left_expr = tree_children[0]
            right_expr = tree_children[1]
            _process_boolean_expr(left_expr, and_id, graph, get_node_id, extract_token_value)
            _process_boolean_expr(right_expr, and_id, graph, get_node_id, extract_token_value)
        elif len(tree_children) >= 1:
            # Si solo hay un hijo Tree, procesarlo
            _process_boolean_expr(tree_children[0], and_id, graph, get_node_id, extract_token_value)
    
    elif expr_node.data == "OR" or expr_node.data == "or":
        # OR: [left, (token OR opcional), right]
        or_id = get_node_id("OR")
        graph.edge(parent_id, or_id)
        
        # Filtrar solo nodos Tree
        tree_children = [ch for ch in expr_node.children if isinstance(ch, Tree)]
        if len(tree_children) >= 2:
            left_expr = tree_children[0]
            right_expr = tree_children[1]
            _process_boolean_expr(left_expr, or_id, graph, get_node_id, extract_token_value)
            _process_boolean_expr(right_expr, or_id, graph, get_node_id, extract_token_value)
        elif len(tree_children) >= 1:
            _process_boolean_expr(tree_children[0], or_id, graph, get_node_id, extract_token_value)
    
    elif expr_node.data == "PARENS":
        # PARENS: desenvuelve y procesa la expresión interna
        if expr_node.children:
            inner_expr = expr_node.children[0]
            _process_boolean_expr(inner_expr, parent_id, graph, get_node_id, extract_token_value)


def detect_reserved_keyword_typos(sql_text: str) -> List[Tuple[str, str]]:
    """
    Detecta palabras que son cercanas a palabras reservadas pero están mal escritas.
    Retorna pares (palabra_detectada, palabra_esperada).
    """
    tokens = re.findall(r"\b[A-Za-z_]+\b", sql_text)
    typos: List[Tuple[str, str]] = []
    seen: set[Tuple[str, str]] = set()
    for raw in tokens:
        upper = raw.upper()
        if upper in RESERVED_KEYWORDS:
            continue
        # Evitar señalar identificadores muy largos o con prefijos comunes
        if len(raw) < 3:
            continue
        closest = difflib.get_close_matches(upper, list(RESERVED_KEYWORDS), n=1, cutoff=0.85)
        if closest:
            target = closest[0]
            if abs(len(target) - len(upper)) > 2:
                continue
            key = (upper, target)
            if key in seen:
                continue
            seen.add(key)
            typos.append((raw, target))
    return typos


def build_learning_summary(result: Dict[str, Any]) -> str:
    parts: List[str] = []
    tokens_count = result.get("metrics", {}).get("tokens")
    if tokens_count is not None:
        parts.append(f"Análisis léxico: {tokens_count} token(s) identificados.")
    ast_nodes = result.get("metrics", {}).get("ast_nodes")
    if ast_nodes:
        parts.append(f"Análisis sintáctico: AST con {ast_nodes} nodo(s).")
    symbols_count = result.get("metrics", {}).get("symbols")
    if symbols_count is not None:
        parts.append(f"Análisis semántico: {symbols_count} símbolo(s) registrados en la tabla.")
    errors = result.get("errors") or []
    if errors:
        parts.append(f"Errores didácticos detectados: {len(errors)}.")
    else:
        parts.append("Sin errores reportados por el compilador didáctico.")
    db_df = result.get("db_result_df")
    db_error = result.get("db_error")
    if db_df is not None:
        rows, cols = db_df.shape
        parts.append(f"Motor SQL real (SQLite): la consulta devolvió {rows} fila(s) y {cols} columna(s).")
    elif db_error:
        parts.append(f"Motor SQL real (SQLite) reportó: {db_error}")
    return " ".join(parts)


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
        "db_result_df": None,
        "db_error": None,
        "learning_summary": "",
    }

    def finalize() -> Dict[str, Any]:
        result["learning_summary"] = build_learning_summary(result)
        return result

    stripped_sql = sql_text.strip()
    if stripped_sql:
        db_df, db_error = execute_demo_query(sql_text)
        if db_df is not None:
            result["db_result_df"] = db_df
        if db_error:
            result["db_error"] = db_error
    else:
        result["db_error"] = None

    typo_pairs_cached = detect_reserved_keyword_typos(sql_text) if stripped_sql else []

    # Fase Léxica: En un compilador real, siempre genera tokens (incluso con errores parciales)
    tokens = []
    lex_errors = []
    try:
        tokens = lex_sql(sql_text)
        if not tokens:
            lex_errors.append("No se generaron tokens. Revisa la entrada SQL.")
    except Exception as ex:
        error_msg = str(ex)
        lex_errors.append(f"Error léxico: {error_msg}")
        # Intentar generar tokens parciales si es posible
        try:
            # En un compilador real, el léxico intenta generar tokens hasta donde puede
            # Intentar tokenizar con manejo de errores más robusto
            from parser_sql import build_parser
            parser = build_parser()
            # Intentar tokenizar hasta el primer error
            partial_text = sql_text.strip()
            if partial_text:
                try:
                    # Intentar obtener al menos algunos tokens
                    tokens = list(parser.lex(partial_text))
                except Exception:
                    # Si falla, intentar con una versión truncada
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
    if lex_errors:
        for wrong, expected in typo_pairs_cached:
            msg = f"Palabra reservada mal escrita: '{wrong}' → se esperaba '{expected}'."
            if msg not in result["errors"]:
                result["errors"].append(msg)
            hint_msg = f"Corregir a '{expected}' en lugar de '{wrong}'."
            if hint_msg not in result["hints"]:
                result["hints"].append(hint_msg)
    result["phase"] = "léxica"
    
    # Si no hay tokens y hay errores críticos, intentar continuar de todas formas si hay algo de texto
    if not tokens and lex_errors and not stripped_sql:
        return finalize()

    # Fase Sintáctica: Construye AST desde los tokens del léxico
    # En un compilador real, el sintáctico opera sobre la salida del léxico
    # Intentar construir AST incluso si hay errores léxicos (si hay tokens)
    try:
        # Si hay tokens, intentar parsear
        if tokens:
            ast = parse_sql_to_ast(sql_text, tokens=tokens)
        else:
            # Si no hay tokens pero hay texto, intentar parsear de todas formas
            # (el parser internamente re-lexica)
            ast = parse_sql_to_ast(sql_text, tokens=None)
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
        error_msg = str(ex)
        if line and column:
            result["errors"].append(f"Error sintáctico en línea {line}, columna {column}: {error_msg}")
            try:
                snippet = ex.get_context(sql_text)
                result["error_snippet"] = snippet
            except Exception:
                result["error_snippet"] = sql_text[max(0, column-20):column+20] if column else sql_text
            # Sugerencias didácticas básicas según tokens esperados
            expected = set()
            try:
                expected = set(ex.expected) if hasattr(ex, 'expected') else set()
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
            if not hints and expected:
                hints.append(f"Se esperaba uno de estos elementos: {', '.join(list(expected)[:5])}")
            if hints:
                result["hints"].extend(hints)
        else:
            result["errors"].append(f"Error sintáctico: {error_msg}")
        result["phase"] = "sintáctica"
        for wrong, expected in typo_pairs_cached:
            msg = f"Palabra reservada mal escrita: '{wrong}' → se esperaba '{expected}'."
            if msg not in result["errors"]:
                result["errors"].append(msg)
            hint_msg = f"Corregir a '{expected}' en lugar de '{wrong}'."
            if hint_msg not in result["hints"]:
                result["hints"].append(hint_msg)
        # En un compilador real, aún intentaríamos construir AST parcial
        # Por ahora, retornamos sin AST si hay error sintáctico crítico
        return finalize()
    except Exception as ex:
        error_msg = str(ex)
        result["errors"].append(f"Error sintáctico: {error_msg}")
        result["phase"] = "sintáctica"
        return finalize()

    # Fase Semántica
    try:
        schema = load_schema()
        symbols, type_rows, sem_errors = analyze_semantics(result["ast"], schema)
        # Convertir símbolos a DataFrame con todas las columnas del dataclass
        symbols_dicts: List[Dict[str, Any]] = []
        for s in symbols:
            sym_dict = {
                "Nombre": s.name,
                "Tipo": s.type,
                "Ámbito": s.scope,
                "Categoría": getattr(s, "kind", "variable"),
                "Tamaño": getattr(s, "size", 0) or "-",
                "Offset": getattr(s, "offset", 0) or "-",
            }
            symbols_dicts.append(sym_dict)
        symbols_df = pd.DataFrame(symbols_dicts)
        result["symbols_df"] = symbols_df

        pretty_types: List[Dict[str, Any]] = []
        for row in type_rows:
            pretty_types.append({
                "Nombre": row.get("nombre"),
                "Tipo": row.get("tipo"),
                "Tamaño": row.get("tamano"),
                "Tabla": row.get("tabla"),
                "Ámbito": row.get("ambito"),
                "Alias": row.get("alias", "-"),
            })
        result["types_df"] = pd.DataFrame(pretty_types)
        result["errors"].extend(sem_errors)
        result["metrics"]["symbols"] = len(symbols_dicts)
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
                        table_used = result["symbols_df"]["Ámbito"].iloc[0].split(".")[-1]
                    except Exception:
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

    return finalize()



