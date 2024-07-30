import csv
from flask import (
    Flask,
    send_file,
    render_template,
    flash,
    request,
    jsonify,
    redirect,
    url_for,
)
from database import database
import numpy as np
from io import StringIO
from scipy.integrate import solve_ivp
import pandas as pd
import base64
import io
import os
import mysql.connector
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly
import json
from controls.historialControl import HistorialControl


# -------------------------Extraemos los datos de la base-------------------------------


# --------------------Implementamos el modelo de la ecuacion diferencial---------------------------------------------------------


# --------------------------------------------Graficar la prediccion-----------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------------------------------------------------------------


# -----------------------------------------------------------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "tu_clave_secreta_aqui"  # Clave secreta para sesiones


# ------------------------------Ruta para prediccion-----------------------------------------------------


# ------------------------------------------------------------------------------------------------


# ---------------------------------------Ruta para la página de inicio------------------------------------------
@app.route("/")
def home():
    print("HOLA")
    hc = HistorialControl()
    resukt = hc.get_historial()
    print(resukt)
    # simulacion.ver_historial()
    return render_template("inicio.html")


# -----------------------------------------------------------------------------------------------------------------------------


# ----------------------------------------- Ruta para la página de inicio de sesión---------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Validación del correo electrónico y la contraseña
        if not email or not password:
            flash("Llene todos los campos", "danger")
            return redirect(url_for("login"))

        if '@' not in email:
            flash("Ingrese una dirección de correo electrónico válida", "danger")
            return redirect(url_for("login"))

        cursor = database.cursor()

        # Consulta para verificar administrador
        query_admin = "SELECT * FROM administrador WHERE correo = %s AND contrasenia = %s"
        cursor.execute(query_admin, (email, password))
        admin = cursor.fetchone()

        if admin:
            flash("Inicio de sesión exitoso como administrador", "success")
            return redirect(url_for("admin_dashboard"))

        # Consulta para verificar usuario normal
        query_usuario = "SELECT * FROM usuario WHERE email = %s AND contrasenia = %s"
        cursor.execute(query_usuario, (email, password))
        usuario = cursor.fetchone()

        if usuario:
            flash("Inicio de sesión exitoso como usuario", "success")
            return redirect(url_for("dashboard_usuario"))

        flash("Credenciales incorrectas. Verifique su correo electrónico y contraseña.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


# -----------------------------------------------------------------------------------------------------------------------------


# -------------------------------------Ruta para el dashboard del administrador----------------------------------------------
@app.route("/admin")
def admin_dashboard():
    return render_template("admi.html")


# -----------------------------------------------------------------------------------------------------------------------------


# --------------------------------------Ruta para el dashboard del usuario normal----------------------------------------------
@app.route("/dashboard_usuario")
def dashboard_usuario():
    try:
        cursor = database.cursor(dictionary=True)

        # Obtener carreras
        cursor.execute("SELECT id, nombre FROM carrera ORDER BY nombre")
        carreras = cursor.fetchall()

        # Obtener ciclos
        cursor.execute("SELECT id, nombre FROM ciclo ORDER BY id")
        ciclos = cursor.fetchall()

        # Obtener años (periodos)
        cursor.execute("SELECT DISTINCT periodo FROM historial ORDER BY periodo")
        anios = [{"periodo": row["periodo"]} for row in cursor.fetchall()]

        cursor.close()

        return render_template(
            "pred.html", carreras=carreras, ciclos=ciclos, anios=anios
        )
    except Exception as e:
        print(f"Error al cargar datos: {str(e)}")
        return render_template("pred.html", error="Error al cargar datos")


# -----------------------------------------------------------------------------------------------------------------------------


# -------------------------------------------Ruta para cerrar sesión-------------------------------------------------------
@app.route("/logout")
def cerrar_sesion():
    return redirect(url_for("login"))


# -----------------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------- Ruta para crear un nuevo usuario--------------------------------------
@app.route("/crear_usuario", methods=["GET", "POST"])
def crear_usuario():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        telefono = request.form["telefono"]
        email = request.form["email"]
        password = request.form["password"]
        rol_id = request.form["rol"]
        carrera_id = request.form["carrera"]

        if (
            not nombre
            or not apellido
            or not telefono
            or not email
            or not password
            or not rol_id
            or not carrera_id
        ):
            flash("Llene todos los campos", "danger")
            return redirect(url_for("crear_usuario"))

        try:
            cursor = database.cursor()
            query = """
                INSERT INTO usuario (nombre, apellido, telefono, email, contrasenia, rol_id, carrera_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query, (nombre, apellido, telefono, email, password, rol_id, carrera_id)
            )
            database.commit()
            flash("Usuario guardado correctamente", "success")
            return redirect(url_for("crear_usuario"))
        except Exception as e:
            flash(f"Error al guardar el usuario: {str(e)}", "danger")
            return redirect(url_for("crear_usuario"))

    # Consultas para obtener roles y carreras disponibles
    cursor = database.cursor()
    cursor.execute("SELECT id, nombre FROM rol")
    roles = cursor.fetchall()
    cursor.execute("SELECT id, nombre FROM carrera")
    carreras = cursor.fetchall()

    return render_template("crearUsuario.html", roles=roles, carreras=carreras)


# -----------------------------------------------------------------------------------------------------------------------------


# Función para obtener los años desde la base de datos
def obtener_anios_desde_bd():
    cursor = database.cursor()
    query = "SELECT nombre FROM anio"  # Ajusta esta consulta según la estructura de tu tabla 'anio'
    cursor.execute(query)
    anios = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return anios


# ---------------------------------------------------Ruta para buscar usuario--------------------------------------------------------------
@app.route("/buscar_usuario", methods=["GET", "POST"])
def buscar_usuario():
    if request.method == "POST":
        termino = request.form.get("termino", "")
        filtro = request.form.get("filtro", "")

        if filtro not in ["carrera", "rol"]:
            return render_template("error.html", mensaje="Filtro inválido")

        cursor = database.cursor(dictionary=True)

        if filtro == "carrera":
            query = """
            SELECT usuario.id, usuario.nombre, usuario.apellido, usuario.telefono, usuario.email, rol.nombre as rol, carrera.nombre as carrera
            FROM usuario
            LEFT JOIN rol ON usuario.rol_id = rol.id
            LEFT JOIN carrera ON usuario.carrera_id = carrera.id
            WHERE carrera.nombre LIKE %s
            """
        elif filtro == "rol":
            query = """
            SELECT usuario.id, usuario.nombre, usuario.apellido, usuario.telefono, usuario.email, rol.nombre as rol, carrera.nombre as carrera
            FROM usuario
            LEFT JOIN rol ON usuario.rol_id = rol.id
            LEFT JOIN carrera ON usuario.carrera_id = carrera.id
            WHERE rol.nombre LIKE %s
            """

        cursor.execute(query, ("%" + termino + "%",))
        usuarios = cursor.fetchall()

        return render_template("buscarUsuario.html", usuarios=usuarios)

    # Muestra todos los usuarios si no hay término de búsqueda
    cursor = database.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT usuario.id, usuario.nombre, usuario.apellido, usuario.telefono, usuario.email, rol.nombre as rol, carrera.nombre as carrera
        FROM usuario
        LEFT JOIN rol ON usuario.rol_id = rol.id
        LEFT JOIN carrera ON usuario.carrera_id = carrera.id
    """
    )
    usuarios = cursor.fetchall()

    return render_template("buscarUsuario.html", usuarios=usuarios)


# -----------------------------------------------------------------------------------------------------------------------------

database = mysql.connector.connect(
    host="localhost", user="root", password="Criss.12345", database="fin"
)



def busquedaNombres():
    cursor = database.cursor(dictionary=True)

    cursor.execute("SELECT nombre FROM carrera")
    carreras = cursor.fetchall()

    cursor.execute("SELECT nombre FROM ciclo")
    ciclos = cursor.fetchall()

    cursor.close()
    return carreras, ciclos


@app.route("/estadisticasGenerales", methods=["GET", "POST"])
def estadisticasGenerales():
    carreras, ciclos = busquedaNombres()

    if request.method == "POST":
        busqueda = request.form.get("busqueda", "").strip()
        carrera = request.form.get("carrera", "").strip()
        ciclo = request.form.get("ciclo", "").strip()

        query = "SELECT h.periodo, c.nombre AS carrera, ci.nombre AS ciclo, h.estudiantesMatriculados, h.estudiantesRetirados, h.estudiantesReprobados, h.estudiantesAprobados FROM historial h JOIN carrera c ON h.carrera = c.nombre JOIN ciclo ci ON h.ciclo = ci.id WHERE 1=1"

        params = []
        if busqueda:
            query += " AND (c.nombre LIKE %s OR ci.nombre LIKE %s)"
            params.extend([f"%{busqueda}%", f"%{busqueda}%"])
        if carrera:
            query += " AND c.nombre = %s"
            params.append(carrera)
        if ciclo:
            query += " AND ci.nombre = %s"
            params.append(ciclo)

        cursor = database.cursor(dictionary=True)
        cursor.execute(query, params)
        datos = cursor.fetchall()
        cursor.close()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"datos": datos})
        else:
            return render_template(
                "estadisticasGenerales.html",
                carreras=carreras,
                ciclos=ciclos,
                datos=datos,
            )

    return render_template(
        "estadisticasGenerales.html", carreras=carreras, ciclos=ciclos
    )


# ------------------------------------------Ruta para editar usuario---------------------------------------------------
@app.route("/editar_usuario/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):
    cursor = database.cursor(dictionary=True)

    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        telefono = request.form["telefono"]
        email = request.form["email"]
        password = request.form["password"]
        rol_id = request.form["rol"]
        carrera_id = request.form["carrera"]

        query = """
            UPDATE usuario
            SET nombre=%s, apellido=%s, telefono=%s, email=%s, contrasenia=%s, rol_id=%s, carrera_id=%s
            WHERE id=%s
        """
        cursor.execute(
            query, (nombre, apellido, telefono, email, password, rol_id, carrera_id, id)
        )
        database.commit()
        flash("Usuario actualizado correctamente", "success")
        return redirect(url_for("buscar_usuario"))

    query = "SELECT * FROM usuario WHERE id = %s"
    cursor.execute(query, (id,))
    usuario = cursor.fetchone()

    cursor.execute("SELECT id, nombre FROM rol")
    roles = cursor.fetchall()
    cursor.execute("SELECT id, nombre FROM carrera")
    carreras = cursor.fetchall()

    return render_template(
        "editarUsuario.html", usuario=usuario, roles=roles, carreras=carreras
    )


# -----------------------------------------------------------------------------------------------------------------------------


# ---------------------------------------Ruta para buscar o visualizar  carrerras---------------------------------------------
@app.route("/buscar_carreras")
def buscar_carreras():
    cursor = database.cursor(dictionary=True)
    query = "SELECT nombre FROM carrera"
    cursor.execute(query)
    carreras = cursor.fetchall()
    return render_template("buscarCarreras.html", carreras=carreras)


# -----------------------------------------------------------------------------------------------------------------------------


# -------------------------------------Ruta para eliminar usuario--------------------------------------------------------
@app.route("/eliminar_usuario/<int:id>", methods=["GET", "POST"])
def eliminar_usuario(id):
    cursor = database.cursor(dictionary=True)
    cursor.execute("DELETE FROM usuario WHERE id = %s", (id,))
    database.commit()
    cursor.close()
    flash("Usuario eliminado correctamente", "success")
    return redirect(url_for("buscar_usuario"))


# -----------------------------------------------------------------------------------------------------------------------------


# ---------------------------------- Ruta para agregar estadísticas de carrera-----------------------------------
@app.route("/agregar_estadistica", methods=["GET", "POST"])
def agregar_carrera():
    if request.method == "POST":
        nombre = request.form["nombre"]
        ciclo = request.form["ciclo"]
        periodo = request.form["anio"]  # Cambiado de periodo_academico a periodo
        estudiantes_matriculados = int(request.form["estudiantesMatriculados"])
        estudiantes_retirados = int(request.form["estudiantesRetirados"])
        estudiantes_reprobados = int(request.form["estudiantesReprobados"])
        estudiantes_aprobados = int(request.form["estudiantesAprobados"])

        # Guardar en la base de datos
        cursor = database.cursor()
        sql = """
            INSERT INTO historial (carrera, ciclo, periodo, estudiantesMatriculados, estudiantesRetirados,
                                  estudiantesReprobados, estudiantesAprobados)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            nombre,
            ciclo,
            periodo,
            estudiantes_matriculados,
            estudiantes_retirados,
            estudiantes_reprobados,
            estudiantes_aprobados,
        )

        cursor.execute(sql, values)
        database.commit()
        cursor.close()

        flash("Carrera agregada correctamente", "success")
        return redirect(
            url_for("admin_dashboard")
        )  # Redirige al dashboard de administrador

    # Obtener los años disponibles desde la base de datos
    anios = obtener_anios_desde_bd()

    return render_template("agregarEstadistica.html", anios=anios)


# -----------------------------------------------------------------------------------------------------------------------------
# Definir la ruta base para los archivos CSV
base_path = "/home/cristian/Escritorio/AreaDeTrabajo/PROYECTO/"


def cargar_datos(carrera):
    nombre_archivo = carrera.lower().replace(" ", "_").replace("ñ", "n")
    archivo = f"{base_path}{nombre_archivo}.csv"
    if os.path.isfile(archivo):
        return pd.read_csv(archivo)
    else:
        return None


def procesar_datos(data, desercion, prediccion, num_cycles_futuros=None):
    if desercion == 1:
        datos_agregados = data.groupby("ciclo").sum()
        labels = datos_agregados.index.tolist()
        datasets = [
            {
                "label": "Estudiantes Matriculados (S)",
                "data": datos_agregados["estudiantesMatriculados"].tolist(),
            },
            {
                "label": "Estudiantes Reprobados (R)",
                "data": datos_agregados["estudiantesReprobados"].tolist(),
            },
            {
                "label": "Estudiantes Retirados (D)",
                "data": datos_agregados["estudiantesRetirados"].tolist(),
            },
            {
                "label": "Estudiantes Aprobados (A)",
                "data": datos_agregados["estudiantesAprobados"].tolist(),
            },
        ]
    elif desercion == 2:
        ciclos_disponibles = data["ciclo"].unique()
        ciclo_seleccionado = ciclos_disponibles[
            -1
        ]  # Por ejemplo, seleccionar el último ciclo
        datos_filtrados = data[data["ciclo"] == ciclo_seleccionado]

        if datos_filtrados.empty:
            return {"error": f"No hay datos para el ciclo {ciclo_seleccionado}."}

        S0 = datos_filtrados["estudiantesMatriculados"].values[0]
        R0 = datos_filtrados["estudiantesReprobados"].values[0]
        D0 = datos_filtrados["estudiantesRetirados"].values[0]
        A0 = datos_filtrados["estudiantesAprobados"].values[0]
        initial_conditions = [S0, R0, D0, A0]

        lambda_val = 0.1
        gamma_val = 0.05
        alpha_val = 0.2
        beta_val = 0.1

        def model(t, y, lambda_val, gamma_val, alpha_val, beta_val):
            S, R, D, A = y
            dSdt = -lambda_val * S - alpha_val * S
            dRdt = alpha_val * S - gamma_val * R
            dDdt = lambda_val * S - gamma_val * D
            dAdt = beta_val * R
            return [dSdt, dRdt, dDdt, dAdt]

        def solve_model(initial_conditions, num_cycles, params):
            t_span = (0, num_cycles - 1)
            t_eval = np.arange(t_span[0], t_span[1] + 1, 1)
            sol = solve_ivp(
                lambda t, y: model(t, y, *params),
                t_span,
                initial_conditions,
                t_eval=t_eval,
            )
            return sol

        params = [lambda_val, gamma_val, alpha_val, beta_val]
        total_cycles = len(datos_filtrados) + (num_cycles_futuros or 0)
        solution = solve_model(initial_conditions, total_cycles, params)

        labels = list(datos_filtrados["periodo"]) + list(
            range(
                datos_filtrados["periodo"].max() + 1,
                datos_filtrados["periodo"].max() + num_cycles_futuros + 1,
            )
        )
        datasets = [
            {
                "label": "Estudiantes Matriculados (S)",
                "data": list(datos_filtrados["estudiantesMatriculados"])
                + list(solution.y[0][len(datos_filtrados) :]),
            },
            {
                "label": "Estudiantes Reprobados (R)",
                "data": list(datos_filtrados["estudiantesReprobados"])
                + list(solution.y[1][len(datos_filtrados) :]),
            },
            {
                "label": "Estudiantes Retirados (D)",
                "data": list(datos_filtrados["estudiantesRetirados"])
                + list(solution.y[2][len(datos_filtrados) :]),
            },
            {
                "label": "Estudiantes Aprobados (A)",
                "data": list(datos_filtrados["estudiantesAprobados"])
                + list(solution.y[3][len(datos_filtrados) :]),
            },
        ]

    return {"labels": labels, "datasets": datasets}


@app.route("/")
def index():
    hc = HistorialControl()
    hc.get_historial()
    return render_template("index.html")


@app.route("/obtener_datos", methods=["GET"])
def obtener_datos():
    carrera = request.args.get("carrera")
    desercion = int(request.args.get("desercion"))
    prediccion = int(request.args.get("prediccion"))
    num_cycles_futuros = int(request.args.get("num_cycles_futuros", 0))

    data = cargar_datos(carrera)
    if data is None:
        return jsonify({"error": "Archivo no encontrado"}), 404

    response = procesar_datos(data, desercion, prediccion, num_cycles_futuros)
    if "error" in response:
        return jsonify(response), 404

    return jsonify(response)


# --------------------------Ruta para calcula prediccion----------------------------------------------------
def model(t, y, lambda_val, gamma_val, alpha_val, beta_val):
    S, R, D, A = y
    dSdt = -lambda_val * S - alpha_val * S
    dRdt = alpha_val * S - gamma_val * R
    dDdt = lambda_val * S - gamma_val * D
    dAdt = beta_val * R
    return [dSdt, dRdt, dDdt, dAdt]


def solve_model(initial_conditions, num_cycles, params):
    t_span = (0, num_cycles - 1)
    t_eval = np.arange(t_span[0], t_span[1] + 1, 1)
    sol = solve_ivp(
        lambda t, y: model(t, y, *params), t_span, initial_conditions, t_eval=t_eval
    )
    return sol


@app.route("/predecir_historicos", methods=["POST"])
def predecir_historicos():
    carrera_id = request.json["carrera"]

    cursor = database.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT periodo, SUM(estudiantesMatriculados) as matriculados, 
               SUM(estudiantesRetirados) as retirados, 
               SUM(estudiantesReprobados) as reprobados, 
               SUM(estudiantesAprobados) as aprobados
        FROM historial
        JOIN carrera ON historial.carrera = carrera.nombre
        WHERE carrera.id = %s
        GROUP BY periodo
        ORDER BY periodo
    """,
        (carrera_id,),
    )

    data = cursor.fetchall()
    cursor.close()

    df = pd.DataFrame(data)

    return jsonify(
        {
            "periodos": df["periodo"].tolist(),
            "matriculados": df["matriculados"].tolist(),
            "retirados": df["retirados"].tolist(),
            "reprobados": df["reprobados"].tolist(),
            "aprobados": df["aprobados"].tolist(),
        }
    )


@app.route("/predecir_ciclo", methods=["POST"])
def predecir_ciclo():
    carrera_id = request.json["carrera"]
    ciclo_id = request.json["ciclo"]

    cursor = database.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT periodo, estudiantesMatriculados as matriculados, 
               estudiantesRetirados as retirados, 
               estudiantesReprobados as reprobados, 
               estudiantesAprobados as aprobados
        FROM historial
        JOIN carrera ON historial.carrera = carrera.nombre
        WHERE carrera.id = %s AND historial.ciclo = %s
        ORDER BY periodo
    """,
        (carrera_id, ciclo_id),
    )

    data = cursor.fetchall()
    cursor.close()

    if not data:
        return jsonify(
            {"error": "No hay datos para esta combinación de carrera y ciclo"}
        )

    df = pd.DataFrame(data)

    return jsonify(
        {
            "periodos": df["periodo"].tolist(),
            "matriculados": df["matriculados"].tolist(),
            "retirados": df["retirados"].tolist(),
            "reprobados": df["reprobados"].tolist(),
            "aprobados": df["aprobados"].tolist(),
        }
    )


@app.route("/predecir_futuro", methods=["POST"])
def predecir_futuro():
    carrera_id = request.json["carrera"]
    tipo_prediccion = request.json["tipo_prediccion"]
    num_periodos_futuros = int(request.json["num_periodos_futuros"])
    ciclo_id = request.json.get("ciclo")
    anio_inicio = request.json.get("anio_inicio")
    anio_fin = request.json.get("anio_fin")

    cursor = database.cursor(dictionary=True)

    if tipo_prediccion == "carrera":
        query = """
        SELECT periodo, SUM(estudiantesMatriculados) as matriculados, 
               SUM(estudiantesRetirados) as retirados, 
               SUM(estudiantesReprobados) as reprobados, 
               SUM(estudiantesAprobados) as aprobados
        FROM historial
        JOIN carrera ON historial.carrera = carrera.nombre
        WHERE carrera.id = %s AND periodo BETWEEN %s AND %s
        GROUP BY periodo
        ORDER BY periodo
        """
        cursor.execute(query, (carrera_id, anio_inicio, anio_fin))
    else:
        query = """
        SELECT periodo, estudiantesMatriculados as matriculados, 
               estudiantesRetirados as retirados, 
               estudiantesReprobados as reprobados, 
               estudiantesAprobados as aprobados
        FROM historial
        JOIN carrera ON historial.carrera = carrera.nombre
        WHERE carrera.id = %s AND historial.ciclo = %s
        ORDER BY periodo
        """
        cursor.execute(query, (carrera_id, ciclo_id))

    data = cursor.fetchall()
    cursor.close()

    df = pd.DataFrame(data)
    df["periodo"] = pd.to_numeric(df["periodo"])

    last_period = int(df["periodo"].max())

    def model(t, y, params):
        S, R, D, A = y
        lambda_val, gamma_val, alpha_val, beta_val = params
        dSdt = -lambda_val * S - alpha_val * S
        dRdt = alpha_val * S - gamma_val * R
        dDdt = lambda_val * S - beta_val * D
        dAdt = gamma_val * R + beta_val * D
        return [dSdt, dRdt, dDdt, dAdt]

    params = [0.1, 0.05, 0.2, 0.1]

    y0 = [
        float(df["matriculados"].iloc[-1]),
        float(df["reprobados"].iloc[-1]),
        float(df["retirados"].iloc[-1]),
        float(df["aprobados"].iloc[-1]),
    ]

    sol = solve_ivp(
        lambda t, y: model(t, y, params),
        [0, num_periodos_futuros],
        y0,
        t_eval=range(num_periodos_futuros + 1),
    )

    future_periods = range(last_period + 1, last_period + num_periodos_futuros + 1)
    future_df = pd.DataFrame(
        {
            "periodo": future_periods,
            "matriculados": sol.y[0][: len(future_periods)],
            "reprobados": sol.y[1][: len(future_periods)],
            "retirados": sol.y[2][: len(future_periods)],
            "aprobados": sol.y[3][: len(future_periods)],
        }
    )

    def to_list(series):
        return [int(x) if isinstance(x, np.integer) else float(x) for x in series]

    return jsonify(
        {
            "historicos": {
                "periodos": to_list(df["periodo"]),
                "matriculados": to_list(df["matriculados"]),
                "retirados": to_list(df["retirados"]),
                "reprobados": to_list(df["reprobados"]),
                "aprobados": to_list(df["aprobados"]),
            },
            "predicciones": {
                "periodos": to_list(future_df["periodo"]),
                "matriculados": to_list(future_df["matriculados"]),
                "retirados": to_list(future_df["retirados"]),
                "reprobados": to_list(future_df["reprobados"]),
                "aprobados": to_list(future_df["aprobados"]),
            },
            "ultimo_periodo_historico": last_period,
        }
    )


# -----------------------------------------------------------------------------------------------------------------------------
@app.route('/importar', methods=['GET', 'POST'])
def importar():
    if request.method == 'POST':
        if 'csvFile' not in request.files:
            return jsonify({'success': False, 'message': 'No se ha subido ningún archivo'})
        
        file = request.files['csvFile']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No se ha seleccionado ningún archivo'})
        
        if file and file.filename.endswith('.csv'):
            try:
                csvfile = StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(csvfile)
                datos = list(csv_reader)
                
                if not datos:
                    return jsonify({'success': False, 'message': 'El archivo CSV está vacío'})
                
                cursor = database.cursor()
                
                for fila in datos:
                    try:
                        sql = """INSERT INTO historial 
                                 (carrera, ciclo, estudiantesMatriculados, estudiantesRetirados, 
                                  estudiantesReprobados, estudiantesAprobados, periodo) 
                                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                        valores = (
                            fila['carrera'],
                            int(fila['ciclo']),
                            int(fila['estudiantes_matriculados']),
                            int(fila['estudiantes_retirados']),
                            int(fila['estudiantes_reprobados']),
                            int(fila['estudiantes_aprobados']),
                            fila['periodo']
                        )
                        cursor.execute(sql, valores)
                    except (ValueError, KeyError) as e:
                        database.rollback()
                        return jsonify({'success': False, 'message': f'Error en los datos: {str(e)}'})
                
                database.commit()
                cursor.close()
                
                tabla_html = '<table class="table table-striped">'
                tabla_html += '<thead><tr>'
                for campo in datos[0].keys():
                    tabla_html += f'<th>{campo}</th>'
                tabla_html += '</tr></thead><tbody>'
                for fila in datos:
                    tabla_html += '<tr>'
                    for valor in fila.values():
                        tabla_html += f'<td>{valor}</td>'
                    tabla_html += '</tr>'
                tabla_html += '</tbody></table>'
                
                return jsonify({'success': True, 'table': tabla_html})
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error al procesar el archivo: {str(e)}'})
        else:
            return jsonify({'success': False, 'message': 'Archivo no válido. Por favor, sube un archivo CSV.'})
    
    return render_template('importar.html')


# -------------------------------- Ruta para calcular la diserción general por carrera--------------------------------------

# -----------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
