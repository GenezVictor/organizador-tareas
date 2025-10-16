from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

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

@app.route('/')
def index():
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = sqlite3.Row
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
    
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    c.execute('INSERT INTO tareas (titulo, descripcion, parent_id) VALUES (?, ?, ?)',
              (titulo, descripcion, parent_id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/completar/<int:tarea_id>')
def completar_tarea(tarea_id):
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    c.execute('UPDATE tareas SET completada = NOT completada WHERE id = ?', (tarea_id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
