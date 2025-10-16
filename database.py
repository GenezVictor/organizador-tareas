import sqlite3

def init_db():
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            parent_id INTEGER,
            completada BOOLEAN DEFAULT FALSE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES tareas (id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Base de datos creada!")
