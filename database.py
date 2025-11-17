import sqlite3

def init_db():
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    
    # Tabla de proyectos
    c.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Modificar tabla tareas para incluir proyecto_id
    c.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            parent_id INTEGER,
            proyecto_id INTEGER DEFAULT 1,
            completada BOOLEAN DEFAULT FALSE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES tareas (id),
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
        )
    ''')
    
    # Proyecto por defecto
    c.execute("INSERT OR IGNORE INTO proyectos (id, nombre) VALUES (1, 'Proyecto Principal')")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Base de datos actualizada con proyectos!")