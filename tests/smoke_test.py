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

for sql in samples:
    print("\n--- SQL:", sql)
    try:
        toks = list(lex_sql(sql))
        print("Tokens:", [(t.type, str(t)) for t in toks])
        ast = parse_sql_to_ast(sql)
        print("AST root:", ast.data)
        schema = load_schema()
        symbols, types, errors = analyze_semantics(ast, schema)
        print("Símbolos:", [s.__dict__ for s in symbols])
        print("Tipos:", types)
        print("Errores:", errors)
    except Exception as e:
        print("Excepción:", e)

