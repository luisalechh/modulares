from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, request, send_file
from flask_login import login_required, current_user
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter

# para el módulo firma electrónica
from spire.pdf.common import *
from spire.pdf import *
from spire.pdf.common import License as pdfLicense



app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Redirige a la vista de login si no ha iniciado sesión


# Base de datos ficticia de usuarios
users = {
    "admin": {"password": "1234", "role": "admin"},
    "ZRAMOS": {"password": "zramos", "role": "user"},
    "LCHANQUETTI":{{"password": "LCHANQUETTI1", "role": "user"}}
}



# Modelo de usuario
class User(UserMixin):
    def __init__(self, username, role):
        self.id = username
        self.role = role  # Almacenar el rol del usuario


# Cargar usuario en sesión
@login_manager.user_loader
def load_user(username):
    if username not in users:
        return None
    user_data = users[username]
    return User(username, user_data["role"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        if username in users and users[username]["password"] == password:
            role = users[username]["role"]  # Obtener el rol del usuario
            user = User(username, role)  # Pasar el rol al objeto User
            login_user(user)
            return redirect(url_for("home"))  # Redirige a /home si el login es exitoso
        else:
            flash("Credenciales incorrectas", "danger")

    return render_template("login.html")


# Ruta protegida: Página principal
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("home"))  # Si el usuario está autenticado, va a /home
    return redirect(url_for("login"))  # Si no, lo envía a /login

@app.route("/home")
@login_required
def home():
    return render_template("home.html", username=current_user.id, role=current_user.role)

@app.route("/reporte")
@login_required
def reporte():
    return render_template("reporte.html", username=current_user.id, role=current_user.role)

@app.route("/reporte_ventas")
@login_required
def reporte_ventas():
    return render_template("reporte_ventas.html", username=current_user.id, role=current_user.role)

@app.route("/analisis_clientes")
@login_required
def analisis_clientes():
    return render_template("analisis_clientes.html", username=current_user.id, role=current_user.role)

# LABORATORIOS

@app.route("/laboratorio-flujo-y-grandes-volumenes")
@login_required
def laboratorio_flujograndesvolumenes():
    return render_template("laboratorio_flujoGrandesVolumenes.html", username=current_user.id, role=current_user.role)

@app.route("/laboratorio-presion")
@login_required
def laboratorio_presion():
    return render_template("laboratorio_presion.html", username=current_user.id, role=current_user.role)

@app.route("/laboratorio-masa")
@login_required
def laboratorio_masa():
    return render_template("laboratorio_masa.html", username=current_user.id, role=current_user.role)

@app.route("/generar_pdf", methods=["POST"])
@login_required
def generar_pdf():
    # Obtener los datos del formulario
    nombre = request.form.get("nombre")
    empresa = request.form.get("empresa")
    detalle = request.form.get("detalle")

    # Crear un buffer de memoria para el PDF
    buffer = io.BytesIO()

    # Crear el PDF con reportlab
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(100, 750, f"Reporte de Flujo y Grandes Volúmenes")
    pdf.drawString(100, 730, f"Nombre: {nombre}")
    pdf.drawString(100, 710, f"Empresa: {empresa}")
    pdf.drawString(100, 690, f"Detalles: {detalle}")

    pdf.save()

    buffer.seek(0)  # Volver al inicio del buffer

    # Enviar el archivo al usuario
    return send_file(buffer, as_attachment=True, download_name="reporte.pdf", mimetype="application/pdf")


# FIRMA ELECTRONICA
@app.route("/firma-electronica")
@login_required
def firma_electronica():
    return render_template("firma_electronica.html", username=current_user.id, role=current_user.role)

# Ruta para subir el PDF
@app.route("/subir_pdf", methods=["POST"])
@login_required
def subir_pdf():
    # Eliminar todos los archivos dentro de la carpeta uploads antes de subir uno nuevo
    folder = app.config["UPLOAD_FOLDER"]
    for archivo in os.listdir(folder):
        archivo_path = os.path.join(folder, archivo)
        if os.path.isfile(archivo_path) or os.path.islink(archivo_path):
            os.unlink(archivo_path)  # Eliminar archivos y enlaces simbólicos
        elif os.path.isdir(archivo_path):
            shutil.rmtree(archivo_path)  # Eliminar directorios y su contenido

    if "archivo" not in request.files:
        flash("No se seleccionó ningún archivo", "danger")
        return redirect(url_for("firma_electronica"))

    archivo = request.files["archivo"]
    if archivo.filename == "":
        flash("No se seleccionó ningún archivo", "danger")
        return redirect(url_for("firma_electronica"))

    if archivo and archivo.filename.endswith(".pdf"):
        filename = secure_filename(archivo.filename)
        ruta_guardado = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        archivo.save(ruta_guardado)
        flash("Archivo subido correctamente", "success")
        return render_template("firma_electronica.html", pdf_subido=filename, username=current_user.id, role=current_user.role)

    flash("Formato no válido. Solo se permiten archivos PDF.", "danger")
    return redirect(url_for("firma_electronica"))

# Ruta para descargar el PDF modificado
import glob
import os


@app.route("/descargar_pdf/<filename>")
@login_required
def descargar_pdf(filename):
    ruta_original = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    ruta_modificada = os.path.join(app.config["UPLOAD_FOLDER"], f"{filename}")

    if not os.path.exists(ruta_original):
        flash("El archivo no existe", "danger")
        return redirect(url_for("firma_electronica"))

    # Obtener valores GET
    key = request.args.get("key")
    posicionx = request.args.get("posicionx")
    posiciony = request.args.get("posiciony")
    ancho = request.args.get("ancho")
    altura = request.args.get("altura")

    agregar_texto_pdf(ruta_original, ruta_modificada, key, posicionx, posiciony, ancho, altura)

    # Enviar el archivo modificado
    response = send_file(
        ruta_modificada,
        as_attachment=True,
        download_name=f"firmado_{filename}",
        mimetype="application/pdf"
    )

    return response



# Función para agregar texto en la primera página del PDF
def agregar_texto_pdf(pdf_entrada, pdf_salida, key, posicionx, posiciony, ancho,altura):
    reader = PdfReader(pdf_entrada)
    writer = PdfWriter()

    packet = io.BytesIO()
    can = canvas.Canvas(packet)

    # Configurar fuente y tamaño
    can.setFont("Helvetica", 12)

    # Posiciones Y para los 5 textos (puedes ajustar según sea necesario)
    posiciones_y = [750, 730, 710, 690, 670]

    # Dibujar cada texto en su posición
    
    can.drawString(0, 0, str(key))
    can.drawString(0, 10, str(posicionx))
    can.drawString(0, 20, str(posiciony))
    can.drawString(0, 30, str(ancho))
    can.drawString(0, 40, str(altura))
    can.save()

    # Mover al inicio del buffer y agregar la página con los textos al PDF
    packet.seek(0)
    new_pdf = PdfReader(packet)
    first_page = reader.pages[0]
    first_page.merge_page(new_pdf.pages[0])

    writer.add_page(first_page)

    # Agregar el resto de páginas sin modificaciones
    for page in reader.pages[1:]:
        writer.add_page(page)

    with open(pdf_salida, "wb") as output_pdf:
        writer.write(output_pdf)

@app.route('/subir_json', methods=['POST'])
def subir_json():
    if 'archivo' not in request.files:
        return redirect(request.url)
    archivo = request.files['archivo']
    if archivo.filename == '':
        return redirect(request.url)
    if archivo:
        # Eliminar todos los archivos dentro de la carpeta uploads antes de subir uno nuevo
        folder = app.config['UPLOAD_FOLDER']
        for archivo_existente in os.listdir(folder):
            archivo_path = os.path.join(folder, archivo_existente)
            if os.path.isfile(archivo_path) or os.path.islink(archivo_path):
                os.unlink(archivo_path)  # Eliminar archivos y enlaces simbólicos
            elif os.path.isdir(archivo_path):
                shutil.rmtree(archivo_path)  # Eliminar directorios y su contenido

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
        archivo.save(filepath)
        return render_template('reporte.html', json_subido=archivo.filename, username=current_user.id, role=current_user.role)
    return redirect(request.url)

@app.route('/descargar_json/<filename>')
def descargar_json(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(filepath, as_attachment=True)

# Cerrar sesión
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
