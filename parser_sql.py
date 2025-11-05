from __future__ import annotations

from lark import Lark, Transformer, Tree, Token, UnexpectedInput
from typing import Optional, List


SQL_GRAMMAR = r"""
// Gramática de un subconjunto de SQL centrado en SELECT
// Soporta: SELECT col[, col]* FROM table [WHERE expr]
// expr con AND/OR, paréntesis, comparaciones (=, !=, <, <=, >, >=)

?start: select_stmt SEMI?

select_stmt: SELECT column_list FROM table_ref where_clause?

column_list: STAR                        -> column_all
           | column (COMMA column)*      -> column_list

column: identifier (AS identifier)?      -> column_alias_opt

table_ref: identifier                    -> table_name

where_clause: WHERE boolean_expr         -> where_clause

?boolean_expr: boolean_expr OR boolean_term  -> or
             | boolean_term

?boolean_term: boolean_term AND boolean_factor -> and
             | boolean_factor

?boolean_factor: comparison
               | LPAREN boolean_expr RPAREN   -> parens

?comparison: value comp_op value           -> compare

?value: identifier                         -> id
      | NUMBER                             -> number
      | STRING                             -> string

comp_op: EQ | NEQ | LT | LTE | GT | GTE

// Terminales y léxico
%import common.CNAME -> CNAME
%import common.SIGNED_NUMBER -> NUMBER
%import common.WS
%ignore WS

// Identificadores (no reservadas) y literales
identifier: CNAME

// Palabras reservadas (case-insensitive)
SELECT: "select"i
FROM:   "from"i
WHERE:  "where"i
AND:    "and"i
OR:     "or"i
AS:     "as"i

// Operadores y símbolos
EQ:  "="
NEQ: "!=" | "<>"
LT:  "<"
LTE: "<="
GT:  ">"
GTE: ">="

STAR: "*"
COMMA: ","
LPAREN: "("
RPAREN: ")"
SEMI: ";"

// Cadenas entre comillas simples
STRING: /'(?:[^'\\]|\\.)*'/
"""


class ASTBuilder(Transformer):
    def start(self, items):
        # Desenvuelve el nodo raíz 'start' y retorna directamente el SELECT_NODE
        # items: [select_stmt, (opcional SEMI)]
        return items[0]

    def identifier(self, items):
        # Normaliza cualquier uso de identifier a un nodo IDENT
        return Tree("IDENT", [items[0]])
    def select_stmt(self, items):
        # items típicos: [Token(SELECT), COLUMN_LIST, Token(FROM), TABLE, (opcional WHERE_CLAUSE)]
        trees_only = [it for it in items if isinstance(it, Tree)]
        columns = trees_only[0]
        table = trees_only[1]
        where = trees_only[2] if len(trees_only) > 2 else None
        node_children = [columns, table]
        if where is not None:
            node_children.append(where)
        return Tree("SELECT_NODE", node_children)

    def column_all(self, _):
        return Tree("COLUMN_LIST", [Tree("STAR", [])])

    def column_list(self, items):
        return Tree("COLUMN_LIST", items)

    def column_alias_opt(self, items):
        # column [AS alias]
        # items puede incluir el token AS; filtramos tokens y nos quedamos con IDENT, [ALIAS]
        trees_only = [it for it in items if isinstance(it, Tree)]
        if len(trees_only) == 2:
            ident, alias_ident = trees_only
            return Tree("COLUMN", [ident, Tree("ALIAS", [alias_ident])])
        return Tree("COLUMN", [trees_only[0]])

    def table_name(self, items):
        return Tree("TABLE", [items[0]])

    def where_clause(self, items):
        # items típicos: [Token(WHERE), boolean_expr]
        trees_only = [it for it in items if isinstance(it, Tree)]
        expr = trees_only[0]
        return Tree("WHERE_CLAUSE", [expr])

    def or_(self, items):
        return Tree("OR", items)

    def and_(self, items):
        return Tree("AND", items)

    def parens(self, items):
        return Tree("PARENS", [items[0]])

    def compare(self, items):
        left, op, right = items
        return Tree("COMPARE", [op, left, right])

    def id(self, items):
        return Tree("IDENT", [items[0]])

    def number(self, items):
        return Tree("NUMBER", [items[0]])

    def string(self, items):
        return Tree("STRING", [items[0]])

    def comp_op(self, items):
        # items[0] es un Token: EQ/NEQ/LT/LTE/GT/GTE
        return Tree("OP", [items[0]])


def build_parser() -> Lark:
    return Lark(SQL_GRAMMAR, start="start", parser="lalr", propagate_positions=True, maybe_placeholders=False)


def parse_sql_to_ast(sql_text: str, tokens: Optional[List[Token]] = None) -> Tree:
    """
    Parsea SQL a AST. Si se proporcionan tokens del léxico, conceptualmente
    el sintáctico se construye sobre la salida del léxico.
    En Lark, internamente re-lexica, pero guardamos los tokens para referencia.
    """
    parser = build_parser()
    parsed = parser.parse(sql_text)
    ast = ASTBuilder().transform(parsed)
    return ast


def lex_sql(sql_text: str) -> list[Token]:
    """
    Analiza léxicamente el texto SQL y genera tokens.
    En un compilador real, esta fase siempre genera tokens (incluso con errores parciales).
    Si hay un error léxico, intenta generar tokens hasta donde sea posible.
    """
    parser = build_parser()
    tokens = []
    try:
        # Intento normal de tokenización
        tokens = list(parser.lex(sql_text))
    except UnexpectedInput as e:
        # En un compilador real, el léxico genera tokens hasta donde puede
        # Intentar recuperar tokens parciales
        try:
            # Usar el lexer directamente para obtener tokens hasta el error
            lexer = parser.lexer
            lexer_state = lexer.make_lexer_state(sql_text)
            # Generar tokens hasta el punto del error
            for token in lexer.lex(lexer_state):
                tokens.append(token)
            # Si llegamos aquí, pudimos generar algunos tokens antes del error
            # El error se reportará pero los tokens generados están disponibles
        except Exception:
            # Si no podemos recuperar tokens, aún intentamos generar lo que sea posible
            # En un compilador real, esto se haría de forma más sofisticada
            pass
        # Si no hay tokens generados, lanzamos el error original
        if not tokens:
            raise e
    except Exception as e:
        # Para otros errores, intentar generar tokens parciales si es posible
        try:
            tokens = list(parser.lex(sql_text[:max(0, len(sql_text)-1)]))
        except Exception:
            pass
        if not tokens:
            raise e
    return tokens



