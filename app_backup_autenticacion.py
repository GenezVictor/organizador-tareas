from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

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

def get_db_connection():
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = sqlite3.Row
    return conn

# INICIALIZAR LA BD SIEMPRE
init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    
    # Obtener todos los proyectos
    proyectos = conn.execute('SELECT * FROM proyectos ORDER BY id').fetchall()
    
    # Obtener proyecto activo (por defecto el primero)
    proyecto_activo_id = request.args.get('proyecto_id', 1, type=int)
    
    # Obtener tareas del proyecto activo
    tareas = conn.execute(
        'SELECT * FROM tareas WHERE proyecto_id = ? ORDER BY parent_id, id',
        (proyecto_activo_id,)
    ).fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         tareas=tareas, 
                         proyectos=proyectos, 
                         proyecto_activo_id=proyecto_activo_id)

@app.route('/agregar', methods=['POST'])
def agregar_tarea():
    titulo = request.form['titulo']
    descripcion = request.form['descripcion']
    parent_id = request.form['parent_id'] or None
    proyecto_id = request.form.get('proyecto_id', 1, type=int)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO tareas (titulo, descripcion, parent_id, proyecto_id) VALUES (?, ?, ?, ?)',
              (titulo, descripcion, parent_id, proyecto_id))
    conn.commit()
    conn.close()
    
    return redirect('/?proyecto_id=' + str(proyecto_id))

@app.route('/completar/<int:tarea_id>')
def completar_tarea(tarea_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Obtener proyecto_id antes de actualizar
    proyecto = c.execute('SELECT proyecto_id FROM tareas WHERE id = ?', (tarea_id,)).fetchone()
    proyecto_id = proyecto['proyecto_id'] if proyecto else 1
    
    c.execute('UPDATE tareas SET completada = NOT completada WHERE id = ?', (tarea_id,))
    conn.commit()
    conn.close()
    
    return redirect('/?proyecto_id=' + str(proyecto_id))

# NUEVA RUTA: ELIMINAR TAREA
@app.route('/eliminar/<int:tarea_id>')
def eliminar_tarea(tarea_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Obtener proyecto_id antes de eliminar
    proyecto = c.execute('SELECT proyecto_id FROM tareas WHERE id = ?', (tarea_id,)).fetchone()
    proyecto_id = proyecto['proyecto_id'] if proyecto else 1
    
    # Eliminar la tarea y sus subtareas (si las tiene)
    c.execute('DELETE FROM tareas WHERE id = ? OR parent_id = ?', (tarea_id, tarea_id))
    conn.commit()
    conn.close()
    
    return redirect('/?proyecto_id=' + str(proyecto_id))

# NUEVA RUTA: CREAR PROYECTO
@app.route('/crear_proyecto', methods=['POST'])
def crear_proyecto():
    nombre = request.form['nombre_proyecto']
    descripcion = request.form.get('descripcion_proyecto', '')
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO proyectos (nombre, descripcion) VALUES (?, ?)',
              (nombre, descripcion))
    conn.commit()
    conn.close()
    
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)