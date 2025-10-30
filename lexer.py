from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
from lark import Token


TOKEN_CATEGORY_MAP: Dict[str, str] = {
    # Palabras reservadas
    "SELECT": "RESERVED",
    "FROM": "RESERVED",
    "WHERE": "RESERVED",
    "AND": "RESERVED",
    "OR": "RESERVED",
    "AS": "RESERVED",
    # Operadores
    "EQ": "OPERATOR",
    "NEQ": "OPERATOR",
    "LT": "OPERATOR",
    "LTE": "OPERATOR",
    "GT": "OPERATOR",
    "GTE": "OPERATOR",
    # Símbolos
    "STAR": "SYMBOL",
    "COMMA": "SYMBOL",
    "LPAREN": "SYMBOL",
    "RPAREN": "SYMBOL",
    "SEMI": "SYMBOL",
    # Literales e identificadores
    "NUMBER": "NUMBER",
    "STRING": "STRING",
    "CNAME": "IDENTIFIER",
}


@dataclass
class LexToken:
    token: str
    tipo: str
    linea: int
    columna: int


def tokens_to_table(tokens: List[Token]) -> List[LexToken]:
    rows: List[LexToken] = []
    for t in tokens:
        category = TOKEN_CATEGORY_MAP.get(t.type, t.type)
        rows.append(
            LexToken(
                token=str(t),
                tipo=category,
                linea=getattr(t, "line", None) or getattr(t, "lineo", 0) or 0,
                columna=getattr(t, "column", None) or getattr(t, "columno", 0) or 0,
            )
        )
    return rows



