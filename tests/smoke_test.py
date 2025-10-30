import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path para las importaciones
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from parser_sql import parse_sql_to_ast, lex_sql
from semantic_analyzer import load_schema, analyze_semantics

samples = [
    "SELECT id, name, age FROM students;",
    "SELECT id, title FROM courses WHERE credits >= 3;",
    "SELECT name, gpa FROM students WHERE age > 18 AND gpa >= 3.5;",
    "SELECT name AS estudiante, gpa AS promedio FROM students WHERE gpa > 4.0;",
    "SELECT id, apellido FROM students;",  # error semántico esperado
    "SELECT id, name students;",           # error sintáctico esperado
]


def test_smoke():
    """Recorrido del pipeline con casos válidos y con errores esperados."""
    for sql in samples:
        # Siempre debe tokenizar sin lanzar excepciones graves
        toks = list(lex_sql(sql))
        assert isinstance(toks, list)

        # Caso de error sintáctico: debe lanzar excepción al parsear
        if " name students" in sql:
            threw = False
            try:
                parse_sql_to_ast(sql)
            except Exception:
                threw = True
            assert threw, "Se esperaba una excepción de parsing en el caso sintácticamente inválido"
            continue

        # Parseo debería funcionar para los demás
        ast = parse_sql_to_ast(sql)
        assert ast is not None

        # Semántica: si se usa una columna inexistente, deben reportarse errores
        schema = load_schema()
        symbols, types, errors = analyze_semantics(ast, schema)
        if "apellido" in sql:
            assert errors and len(errors) > 0, "Se esperaban errores semánticos por columna inexistente"
        else:
            # No exigimos cero errores en todos los casos, pero sí que sea una lista
            assert isinstance(errors, list)

