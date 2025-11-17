from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

def get_db_path():
    # En Railway usa /tmp/ para escritura, o el directorio actual
    return os.path.join(os.getcwd(), 'tareas.db')

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
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

def get_db_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tareas ORDER BY parent_id, id')
    tareas = c.fetchall()
    conn.close()
    return render_template('index.html', tareas=tareas)

@app.route('/agregar', methods=['POST'])
def agregar_tarea():
    titulo = request.form['titulo']
    descripcion = request.form['descripcion']
    parent_id = request.form['parent_id'] or None
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO tareas (titulo, descripcion, parent_id) VALUES (?, ?, ?)',
              (titulo, descripcion, parent_id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/completar/<int:tarea_id>')
def completar_tarea(tarea_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE tareas SET completada = NOT completada WHERE id = ?', (tarea_id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
