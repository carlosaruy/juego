import sqlite3
from datetime import datetime

# Coeficientes de puntaje segun numero de intento
COEFFICIENTS = [1.0, 0.7, 0.4, 0.1, 0]

# Preguntas de ejemplo con sus opciones
QUESTION_OPTIONS = {
    1: ["Par\u00eds", "Londres", "Roma", "Berl\u00edn"],
    2: ["3", "4", "5", "6"],
}

QUESTIONS = [
    (1, "\u00bfCapital de Francia?", 0),
    (2, "\u00bf2+2?", 1),
]

USERS = [
    (1, "Ana", 1),
    (2, "Luis", 1),
    (3, "Clara", 2),
]

GROUPS = [
    (1, "Grupo A"),
    (2, "Grupo B"),
]

def main():
    conn = sqlite3.connect("quiz.db")
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS Settings (key TEXT PRIMARY KEY, value TEXT)')

    c.execute('CREATE TABLE IF NOT EXISTS "Group" (id INTEGER PRIMARY KEY, name TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS "User" (id INTEGER PRIMARY KEY, name TEXT, group_id INTEGER)')
    c.execute("""CREATE TABLE IF NOT EXISTS Question (
        id INTEGER PRIMARY KEY,
        text TEXT,
        correct_option INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS Attempt (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_id INTEGER,
        option INTEGER,
        is_correct INTEGER,
        created_at TEXT
    )""")

    c.executemany('INSERT INTO "Group"(id,name) VALUES (?,?)', GROUPS)
    c.executemany('INSERT INTO "User"(id,name,group_id) VALUES (?,?,?)', USERS)
    c.executemany("INSERT INTO Question(id,text,correct_option) VALUES (?,?,?)", QUESTIONS)
    c.execute('INSERT OR IGNORE INTO Settings(key,value) VALUES ("registration_open","1")')
    conn.commit()
    conn.close()
    print("Base de datos inicializada")

if __name__ == "__main__":
    main()
