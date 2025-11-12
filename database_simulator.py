from __future__ import annotations

import sqlite3
from typing import Tuple

import pandas as pd


SAMPLE_DATA = {
    "students": [
        (1, "Ana Torres", 20, 3.4),
        (2, "Luis Pérez", 22, 3.8),
        (3, "María Gómez", 19, 3.1),
        (4, "Carlos Díaz", 21, 2.9),
        (5, "Laura Méndez", 23, 3.6),
    ],
    "courses": [
        (10, "Compiladores", 4),
        (11, "Bases de Datos", 3),
        (12, "Redes de Computadores", 4),
    ],
    "enrollments": [
        (1, 10, "A"),
        (1, 11, "B"),
        (2, 10, "A"),
        (3, 12, "C"),
        (4, 11, "B"),
    ],
}


CREATE_TABLE_STATEMENTS = {
    "students": """
        CREATE TABLE students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gpa REAL
        );
    """,
    "courses": """
        CREATE TABLE courses (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            credits INTEGER NOT NULL
        );
    """,
    "enrollments": """
        CREATE TABLE enrollments (
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            grade TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        );
    """,
}


INSERT_STATEMENTS = {
    "students": "INSERT INTO students(id, name, age, gpa) VALUES (?, ?, ?, ?);",
    "courses": "INSERT INTO courses(id, title, credits) VALUES (?, ?, ?);",
    "enrollments": "INSERT INTO enrollments(student_id, course_id, grade) VALUES (?, ?, ?);",
}


def build_demo_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    for table, ddl in CREATE_TABLE_STATEMENTS.items():
        cursor.executescript(ddl)
    for table, rows in SAMPLE_DATA.items():
        cursor.executemany(INSERT_STATEMENTS[table], rows)
    conn.commit()
    return conn


def execute_demo_query(sql_text: str) -> Tuple[pd.DataFrame | None, str | None]:
    conn = build_demo_connection()
    try:
        df = pd.read_sql_query(sql_text, conn)
        return df, None
    except Exception as ex:
        return None, str(ex)
    finally:
        conn.close()


