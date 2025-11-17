import sqlite3
import os

def migrar_base_datos():
    print("🔄 Iniciando migración de base de datos...")
    
    # Hacer backup de la base de datos actual
    if os.path.exists('tareas.db'):
        os.rename('tareas.db', 'tareas_backup.db')
        print("✅ Backup creado: tareas_backup.db")
    
    # Reconectar para crear nueva estructura
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    
    # Crear tabla de proyectos
    c.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear tabla tareas con la nueva estructura
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
    
    # Migrar datos del backup si existe
    if os.path.exists('tareas_backup.db'):
        print("🔄 Migrando datos del backup...")
        backup_conn = sqlite3.connect('tareas_backup.db')
        backup_c = backup_conn.cursor()
        
        try:
            # Obtener todas las tareas del backup
            backup_c.execute('SELECT * FROM tareas')
            tareas_viejas = backup_c.fetchall()
            
            # Insertar en la nueva tabla (asignando proyecto_id = 1)
            for tarea in tareas_viejas:
                # Asumimos la estructura: id, titulo, descripcion, parent_id, completada, fecha_creacion
                c.execute('''
                    INSERT INTO tareas (id, titulo, descripcion, parent_id, proyecto_id, completada, fecha_creacion)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                ''', tarea)
            
            print(f"✅ Migradas {len(tareas_viejas)} tareas al nuevo proyecto")
            backup_conn.close()
            
        except sqlite3.Error as e:
            print(f"⚠️ No se pudieron migrar datos: {e}")
            print("✅ Se creará una base de datos nueva")
    
    conn.commit()
    conn.close()
    print("🎉 Migración completada exitosamente!")
    print("📊 Nueva estructura:")
    
    # Verificar la nueva estructura
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = c.fetchall()
    print("Tablas:", [tabla[0] for tabla in tablas])
    
    c.execute("SELECT COUNT(*) FROM proyectos")
    print("Proyectos:", c.fetchone()[0])
    
    c.execute("SELECT COUNT(*) FROM tareas")
    print("Tareas:", c.fetchone()[0])
    
    conn.close()

if __name__ == "__main__":
    migrar_base_datos()
