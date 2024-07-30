from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import numpy as np
from scipy.integrate import solve_ivp

# import simulacion
from controls.historialControl import HistorialControl

app = Flask(__name__)

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


if __name__ == "__main__":
    app.run(debug=True)
