from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from lark import Tree, Token


@dataclass
class Symbol:
    name: str
    type: str
    scope: str
    # Campos adicionales para tabla de símbolos de compilador real
    kind: str = "variable"  # variable, function, table, column
    size: int = 0  # Tamaño en bytes
    offset: int = 0  # Offset en memoria (para compiladores reales)


def load_schema(path: str | Path = "schema_simulado.json") -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _token_text(node) -> str:
    if isinstance(node, Token):
        return str(node)
    if isinstance(node, Tree):
        # IDENT -> [Token(CNAME, ...)]
        if node.data in {"IDENT", "NUMBER", "STRING"} and node.children:
            return _token_text(node.children[0])
    return str(node)


def _collect_columns_from_select(ast: Tree) -> List[Tuple[str, Optional[str]]]:
    # Devuelve lista de (colname, alias)
    cols: List[Tuple[str, Optional[str]]] = []
    def visit(node: Tree):
        if isinstance(node, Tree) and node.data == "COLUMN_LIST":
            for child in node.children:
                if isinstance(child, Tree) and child.data == "STAR":
                    cols.append(("*", None))
                elif isinstance(child, Tree) and child.data == "COLUMN":
                    ident = _token_text(child.children[0])
                    alias = None
                    if len(child.children) == 2 and isinstance(child.children[1], Tree) and child.children[1].data == "ALIAS":
                        alias = _token_text(child.children[1].children[0])
                    cols.append((ident, alias))
        else:
            for ch in getattr(node, "children", []):
                if isinstance(ch, Tree):
                    visit(ch)
    visit(ast)
    return cols


def _get_table_name(ast: Tree) -> Optional[str]:
    # Intento directo según estructura del AST construido
    if isinstance(ast, Tree) and ast.data == "SELECT_NODE" and len(ast.children) >= 2:
        table_node = ast.children[1]
        if isinstance(table_node, Tree) and table_node.data == "TABLE" and table_node.children:
            return _token_text(table_node.children[0])

    # Búsqueda recursiva: SOLO nodos TABLE
    def visit(node: Tree) -> Optional[str]:
        if isinstance(node, Tree) and node.data == "TABLE" and node.children:
            return _token_text(node.children[0])
        for ch in getattr(node, "children", []):
            if isinstance(ch, Tree):
                r = visit(ch)
                if r:
                    return r
        return None
    return visit(ast)


def _collect_identifiers_in_where(ast: Tree) -> List[str]:
    idents: List[str] = []
    def visit(node: Tree):
        if isinstance(node, Tree) and node.data == "WHERE_CLAUSE":
            def walk(n: Tree):
                if isinstance(n, Tree) and n.data == "IDENT":
                    idents.append(_token_text(n.children[0]))
                for c in getattr(n, "children", []):
                    if isinstance(c, Tree):
                        walk(c)
            walk(node)
        else:
            for ch in getattr(node, "children", []):
                if isinstance(ch, Tree):
                    visit(ch)
    visit(ast)
    return idents


def analyze_semantics(ast: Tree, schema: Dict) -> Tuple[List[Symbol], List[Dict[str, str]], List[str]]:
    """
    Retorna (symbol_table, type_table, errors)
    - symbol_table: lista de símbolos (nombre, tipo, ámbito)
    - type_table: lista con info de columnas (columna, tipo, tamaño)
    - errors: lista de mensajes de error
    """
    errors: List[str] = []
    symbols: List[Symbol] = []
    types_rows: List[Dict[str, str]] = []

    tables = schema.get("tables", {})

    table_name = _get_table_name(ast)
    if not table_name:
        # Fallback: buscar IDENT que coincida con tablas del esquema
        table_keys = set(schema.get("tables", {}).keys())
        found: Optional[str] = None
        def visit_ident(n: Tree):
            nonlocal found
            if found is not None:
                return
            if isinstance(n, Tree) and n.data == "IDENT" and n.children:
                text = _token_text(n.children[0])
                if text in table_keys:
                    found = text
                    return
            for c in getattr(n, "children", []):
                if isinstance(c, Tree):
                    visit_ident(c)
        visit_ident(ast)
        table_name = found
    if not table_name:
        errors.append("No se encontró la tabla en el AST")
        return symbols, types_rows, errors

    if table_name not in tables:
        errors.append(f"Tabla inexistente: {table_name}")
        return symbols, types_rows, errors

    columns_def = tables[table_name]

    # Tabla de símbolos como en compilador real:
    # Primero añadir la tabla misma
    symbols.append(Symbol(name=table_name, type="TABLE", scope="GLOBAL", kind="table"))
    
    # Columnas en SELECT
    select_cols = _collect_columns_from_select(ast)
    if select_cols and select_cols[0][0] == "*":
        # Expandir todas las columnas
        for col, meta in columns_def.items():
            col_type = meta.get("type", "UNKNOWN")
            size = meta.get("size", 0)
            symbols.append(Symbol(
                name=col, 
                type=col_type, 
                scope=f"{table_name}.SELECT", 
                kind="column",
                size=size
            ))
            types_rows.append({
                "nombre": col, 
                "tipo": col_type, 
                "tamano": str(size or "-"),
                "tabla": table_name,
                "ambito": f"{table_name}.SELECT"
            })
    else:
        for col, alias in select_cols:
            if col not in columns_def:
                errors.append(f"Columna inexistente en SELECT: {col}")
                continue
            meta = columns_def[col]
            col_type = meta.get("type", "UNKNOWN")
            size = meta.get("size", 0)
            symbol_name = alias or col
            symbols.append(Symbol(
                name=symbol_name, 
                type=col_type, 
                scope=f"{table_name}.SELECT", 
                kind="column",
                size=size
            ))
            types_rows.append({
                "nombre": col, 
                "tipo": col_type, 
                "tamano": str(size or "-"),
                "tabla": table_name,
                "ambito": f"{table_name}.SELECT",
                "alias": alias if alias else "-"
            })

    # Identificadores en WHERE: añadir a tabla de símbolos si existen
    where_idents = _collect_identifiers_in_where(ast)
    for ident in where_idents:
        if ident not in columns_def:
            errors.append(f"Columna inexistente en WHERE: {ident}")
        else:
            # Añadir símbolo para WHERE si no existe ya
            meta = columns_def[ident]
            col_type = meta.get("type", "UNKNOWN")
            size = meta.get("size", 0)
            # Solo añadir si no está ya en símbolos (evitar duplicados)
            if not any(s.name == ident and s.scope == f"{table_name}.WHERE" for s in symbols):
                symbols.append(Symbol(
                    name=ident,
                    type=col_type,
                    scope=f"{table_name}.WHERE",
                    kind="column",
                    size=size
                ))

    return symbols, types_rows, errors



