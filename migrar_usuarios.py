import sqlite3
import os
from werkzeug.security import generate_password_hash

def migrar_con_usuarios():
    print("🔄 Iniciando migración para sistema de usuarios...")
    
    # Hacer backup
    if os.path.exists('tareas.db'):
        os.rename('tareas.db', 'tareas_backup_usuarios.db')
        print("✅ Backup creado: tareas_backup_usuarios.db")
    
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    
    # 1. Crear tabla usuarios
    c.execute('''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Modificar tabla proyectos para agregar usuario_id
    c.execute('''
        CREATE TABLE proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT,
            usuario_id INTEGER NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    # 3. Mantener tabla tareas (ya tiene proyecto_id)
    c.execute('''
        CREATE TABLE tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            parent_id INTEGER,
            proyecto_id INTEGER,
            completada BOOLEAN DEFAULT FALSE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES tareas (id),
            FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
        )
    ''')
    
    # 4. Crear usuario demo
    password_hash = generate_password_hash('demo123')
    c.execute(
        "INSERT INTO usuarios (username, email, password_hash) VALUES (?, ?, ?)",
        ('demo', 'demo@ejemplo.com', password_hash)
    )
    
    # 5. Crear proyecto demo para el usuario demo
    c.execute(
        "INSERT INTO proyectos (nombre, descripcion, usuario_id) VALUES (?, ?, ?)",
        ('Proyecto de Demo', 'Proyecto de ejemplo para usuario demo', 1)
    )
    
    conn.commit()
    conn.close()
    print("🎉 Migración para usuarios completada!")
    print("👤 Usuario demo creado: username='demo', password='demo123'")

if __name__ == "__main__":
    migrar_con_usuarios()
