from bson import ObjectId
from flask import Flask, flash, render_template, request, redirect, url_for, session
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from GestorTareas import GestorTareas

app = Flask(__name__)
app.secret_key = "mi_clave_super_secreta"

gestor = GestorTareas()  

@app.route('/')
def index():
    
    if 'usuario_id' not in session:
        return render_template('index.html')  

    usuarios = list(gestor.usuarios.find())
    for u in usuarios:
        u['_id'] = str(u['_id'])
    return render_template('index.html', usuarios=usuarios)



@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('crear_usuario.html', error="Las contraseñas no coinciden")

        try:
            resultado = gestor.usuarios.insert_one({
                "nombre": nombre,
                "email": email,
                "password": password,
                "fecha_registro": datetime.now(),
                "activo": True
            })

            usuario_id = str(resultado.inserted_id)

            session['usuario_id'] = usuario_id
            session['nombre'] = nombre

            return redirect(url_for('ver_tareas', usuario_id=usuario_id))

        except DuplicateKeyError:
            return render_template('crear_usuario.html', error="Este correo ya está registrado")

    return render_template('crear_usuario.html')

@app.route('/crear_tarea/<usuario_id>', methods=['GET', 'POST'])
def crear_tarea(usuario_id):
    if request.method == 'POST':
        gestor.crear_tarea(
            usuario_id,
            request.form['titulo'],
            request.form['descripcion']
        )
        return redirect(url_for('ver_tareas', usuario_id=usuario_id))
    
    return render_template('crear_tarea.html', usuario_id=usuario_id)


@app.route('/editar_usuario/<usuario_id>', methods=['GET', 'POST'])
def editar_usuario(usuario_id):
    try:
        usuario = gestor.usuarios.find_one({"_id": ObjectId(usuario_id)})
        if not usuario:
            flash("Usuario no encontrado", "danger")
            return redirect(url_for('index'))

        if request.method == 'POST':
            nombre = request.form.get('nombre')
            email = request.form.get('email')

            gestor.usuarios.update_one(
                {"_id": ObjectId(usuario_id)},
                {"$set": {"nombre": nombre, "email": email}}
            )

            # Actualizamos el nombre en la sesión
            session['nombre'] = nombre

            flash("Usuario actualizado correctamente", "success")
            return redirect(url_for('ver_tareas', usuario_id=usuario_id))

        return render_template('editar_usuario.html', usuario=usuario)

    except Exception as e:
        # Esto ayuda a ver el error exacto
        return f"Ha ocurrido un error: {str(e)}"


@app.route('/actualizar_estado/<tarea_id>', methods=['POST'])
def actualizar_estado(tarea_id):
    gestor.actualizar_estado_tarea(
        tarea_id,
        request.form['estado']
    )
    return redirect(request.referrer)


@app.route('/eliminar_tarea/<tarea_id>', methods=['POST'])
def eliminar_tarea(tarea_id):
    gestor.eliminar_tarea(tarea_id)
    return redirect(request.referrer)

@app.route('/tareas/<usuario_id>')
def ver_tareas(usuario_id):
    tareas = gestor.obtener_tareas_usuario(usuario_id)
    return render_template('tareas.html', tareas=tareas, usuario_id=usuario_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        usuario = gestor.usuarios.find_one({"email": email})
        if usuario and usuario['password'] == password:
            session['usuario_id'] = str(usuario['_id'])
            session['nombre'] = usuario['nombre']

        
            return redirect(url_for('ver_tareas', usuario_id=session['usuario_id']))
        else:
            return render_template('login.html', error="Credenciales incorrectas")

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash(f'Has cerrado sesión correctamente', 'info')
    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=False)