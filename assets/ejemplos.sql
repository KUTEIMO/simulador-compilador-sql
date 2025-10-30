-- Ejemplos de consultas soportadas por el simulador

-- Seleccionar columnas de una tabla
SELECT id, name, age FROM students;

-- Filtro simple con WHERE
SELECT id, title FROM courses WHERE credits >= 3;

-- Condiciones combinadas
SELECT name, gpa FROM students WHERE age > 18 AND gpa >= 3.5;

-- Uso de alias (limitado, alias de columnas)
SELECT name AS estudiante, gpa AS promedio FROM students WHERE gpa > 4.0;

-- Ejemplo con error semántico (columna inexistente)
SELECT id, apellido FROM students;

-- Ejemplo con error sintáctico (falta FROM)
SELECT id, name students;


