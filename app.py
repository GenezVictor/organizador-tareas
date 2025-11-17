from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'clave_secreta_muy_segura_para_desarrollo'  # En producción usar variable de entorno

# Función para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    conn = sqlite3.connect('tareas.db')
    c = conn.cursor()
    
    # Tabla de usuarios
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de proyectos con usuario_id
    c.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT,
            usuario_id INTEGER NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    # Tabla tareas
    c.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
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
    
    # Crear usuario demo si no existe
    try:
        password_hash = generate_password_hash('demo123')
        c.execute(
            "INSERT OR IGNORE INTO usuarios (id, username, email, password_hash) VALUES (1, ?, ?, ?)",
            ('demo', 'demo@ejemplo.com', password_hash)
        )
        
        # Crear proyecto demo si no existe
        c.execute(
            "INSERT OR IGNORE INTO proyectos (id, nombre, descripcion, usuario_id) VALUES (1, ?, ?, ?)",
            ('Proyecto de Demo', 'Proyecto de ejemplo para usuario demo', 1)
        )
    except:
        pass
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = sqlite3.Row
    return conn

# INICIALIZAR LA BD SIEMPRE
init_db()

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validaciones básicas
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('registro.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('registro.html')
        
        conn = get_db_connection()
        c = conn.cursor()
        
        try:
            # Verificar si el usuario o email ya existen
            existing_user = c.execute(
                'SELECT id FROM usuarios WHERE username = ? OR email = ?', 
                (username, email)
            ).fetchone()
            
            if existing_user:
                flash('El nombre de usuario o email ya está en uso.', 'danger')
                return render_template('registro.html')
            
            # Crear nuevo usuario
            password_hash = generate_password_hash(password)
            c.execute(
                'INSERT INTO usuarios (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            conn.commit()
            
            flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash('Error en el registro. Intenta nuevamente.', 'danger')
            return render_template('registro.html')
        finally:
            conn.close()
    
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Buscar usuario por username o email
        user = c.execute(
            'SELECT * FROM usuarios WHERE username = ? OR email = ?', 
            (username, username)
        ).fetchone()
        
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'¡Bienvenido {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

# ==================== RUTAS PROTEGIDAS ====================

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    
    # Obtener proyectos del usuario actual
    proyectos = conn.execute(
        'SELECT * FROM proyectos WHERE usuario_id = ? ORDER BY id', 
        (session['user_id'],)
    ).fetchall()
    
    # Obtener proyecto activo (por defecto el primero)
    proyecto_activo_id = request.args.get('proyecto_id', proyectos[0]['id'] if proyectos else 0, type=int)
    
    # Obtener tareas del proyecto activo (solo si pertenece al usuario)
    tareas = []
    if proyecto_activo_id:
        # Verificar que el proyecto pertenece al usuario
        proyecto_usuario = conn.execute(
            'SELECT id FROM proyectos WHERE id = ? AND usuario_id = ?', 
            (proyecto_activo_id, session['user_id'])
        ).fetchone()
        
        if proyecto_usuario:
            tareas = conn.execute(
                'SELECT * FROM tareas WHERE proyecto_id = ? ORDER BY parent_id, id',
                (proyecto_activo_id,)
            ).fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         tareas=tareas, 
                         proyectos=proyectos, 
                         proyecto_activo_id=proyecto_activo_id,
                         username=session.get('username'))

@app.route('/agregar', methods=['POST'])
@login_required
def agregar_tarea():
    titulo = request.form['titulo']
    descripcion = request.form['descripcion']
    parent_id = request.form['parent_id'] or None
    proyecto_id = request.form.get('proyecto_id', type=int)
    
    # Verificar que el proyecto pertenece al usuario
    conn = get_db_connection()
    proyecto_usuario = conn.execute(
        'SELECT id FROM proyectos WHERE id = ? AND usuario_id = ?', 
        (proyecto_id, session['user_id'])
    ).fetchone()
    
    if not proyecto_usuario:
        flash('Proyecto no válido.', 'danger')
        return redirect('/')
    
    c = conn.cursor()
    c.execute('INSERT INTO tareas (titulo, descripcion, parent_id, proyecto_id) VALUES (?, ?, ?, ?)',
              (titulo, descripcion, parent_id, proyecto_id))
    conn.commit()
    conn.close()
    
    flash('Tarea agregada correctamente.', 'success')
    return redirect('/?proyecto_id=' + str(proyecto_id))

@app.route('/completar/<int:tarea_id>')
@login_required
def completar_tarea(tarea_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Obtener proyecto_id y verificar permisos
    tarea_info = c.execute('''
        SELECT t.proyecto_id 
        FROM tareas t 
        JOIN proyectos p ON t.proyecto_id = p.id 
        WHERE t.id = ? AND p.usuario_id = ?
    ''', (tarea_id, session['user_id'])).fetchone()
    
    if not tarea_info:
        flash('Tarea no encontrada o sin permisos.', 'danger')
        return redirect('/')
    
    proyecto_id = tarea_info['proyecto_id']
    
    c.execute('UPDATE tareas SET completada = NOT completada WHERE id = ?', (tarea_id,))
    conn.commit()
    conn.close()
    
    return redirect('/?proyecto_id=' + str(proyecto_id))

@app.route('/eliminar/<int:tarea_id>')
@login_required
def eliminar_tarea(tarea_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Verificar permisos antes de eliminar
    tarea_info = c.execute('''
        SELECT t.proyecto_id 
        FROM tareas t 
        JOIN proyectos p ON t.proyecto_id = p.id 
        WHERE t.id = ? AND p.usuario_id = ?
    ''', (tarea_id, session['user_id'])).fetchone()
    
    if not tarea_info:
        flash('Tarea no encontrada o sin permisos.', 'danger')
        return redirect('/')
    
    proyecto_id = tarea_info['proyecto_id']
    
    # Eliminar la tarea y sus subtareas
    c.execute('DELETE FROM tareas WHERE id = ? OR parent_id = ?', (tarea_id, tarea_id))
    conn.commit()
    conn.close()
    
    flash('Tarea eliminada correctamente.', 'success')
    return redirect('/?proyecto_id=' + str(proyecto_id))

@app.route('/crear_proyecto', methods=['POST'])
@login_required
def crear_proyecto():
    nombre = request.form['nombre_proyecto']
    descripcion = request.form.get('descripcion_proyecto', '')
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO proyectos (nombre, descripcion, usuario_id) VALUES (?, ?, ?)',
              (nombre, descripcion, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Proyecto creado correctamente.', 'success')
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)