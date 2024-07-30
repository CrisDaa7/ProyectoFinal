import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit
import os

# Definir la ruta base para los archivos CSV
base_path = 'C:/Users/Victor/Documents/Proyectos 4 ciclo/MOROCHOV2/'

# Función para cargar datos desde un archivo CSV basado en la carrera
def cargar_datos(carrera):
    nombre_archivo = carrera.lower().replace(" ", "_").replace("ñ", "n")
    archivo = f'{base_path}{nombre_archivo}.csv'
    if os.path.isfile(archivo):
        return pd.read_csv(archivo)
    else:
        print(f"Archivo para {carrera} no encontrado en la ruta {archivo}.")
        return None

# Verificar archivos en el directorio
archivos = os.listdir(base_path)
print("Archivos en el directorio:")
for archivo in archivos:
    print(archivo)

# Paso 1: Mostrar las opciones disponibles al usuario y permitir que seleccione
carreras_disponibles = [
    'Telecomunicaciones',
    'Minas',
    'Computacion',
    'Electricidad',
    'Automotriz'
]
print("Carreras disponibles:")
for idx, carrera in enumerate(carreras_disponibles):
    print(f"{idx + 1}. {carrera}")

carrera_idx = int(input("Seleccione el número de la carrera que desea analizar: ")) - 1
carrera_seleccionada = carreras_disponibles[carrera_idx]

# Cargar datos para la carrera seleccionada
data = cargar_datos(carrera_seleccionada)

if data is not None:
    print("Datos cargados:")
    print(data.head())  # Imprimir las primeras filas del DataFrame

    # Paso 2: Mostrar opciones de deserción
    print("Opciones de deserción disponibles:")
    print("1. Deserción por carrera")
    print("2. Deserción por ciclo")
    opcion_desercion = int(input("Seleccione el número de la opción de deserción que desea analizar: "))

    if opcion_desercion in [1, 2]:
        # Paso 3: Mostrar opciones de predicción
        print("Opciones de predicción disponibles:")
        print("1. Predicción con datos históricos")
        print("2. Predicción a futuro")
        opcion_prediccion = int(input("Seleccione el número de la opción de predicción que desea realizar: "))

        if opcion_prediccion == 1:
            # Predicción con datos históricos
            if opcion_desercion == 1:
                # Deserción por carrera
                print(f"Deserción por carrera para {carrera_seleccionada}")
                # Obtener los datos agregados por carrera
                datos_agregados = data.groupby('ciclo').sum()

                # Graficar resultados
                plt.figure(figsize=(10, 6))
                plt.plot(datos_agregados.index, datos_agregados['estudiantesMatriculados'], label='Estudiantes Matriculados (S)')
                plt.plot(datos_agregados.index, datos_agregados['estudiantesReprobados'], label='Estudiantes Reprobados (R)')
                plt.plot(datos_agregados.index, datos_agregados['estudiantesRetirados'], label='Estudiantes Desertores (D)')
                plt.plot(datos_agregados.index, datos_agregados['estudiantesAprobados'], label='Estudiantes Aprobados (A)')
                plt.xlabel('Ciclo Académico')
                plt.ylabel('Número de Estudiantes')
                plt.title(f'Modelo de Deserción Estudiantil para {carrera_seleccionada}')
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                plt.show()
            elif opcion_desercion == 2:
                # Deserción por ciclo
                # Mostrar ciclos disponibles para la carrera seleccionada
                ciclos_disponibles = data['ciclo'].unique()
                print(f"Ciclos disponibles para {carrera_seleccionada}:")
                for idx, ciclo in enumerate(ciclos_disponibles):
                    print(f"{idx + 1}. {ciclo}")

                ciclo_idx = int(input("Seleccione el número del ciclo que desea analizar: ")) - 1
                ciclo_seleccionado = ciclos_disponibles[ciclo_idx]

                # Filtrar datos para la carrera y ciclo seleccionados
                datos_filtrados = data[(data['ciclo'] == ciclo_seleccionado)]

                if not datos_filtrados.empty:
                    print("Datos filtrados:")
                    print(datos_filtrados)

                    # Datos iniciales
                    S0 = datos_filtrados['estudiantesMatriculados'].values[0]
                    R0 = datos_filtrados['estudiantesReprobados'].values[0]
                    D0 = datos_filtrados['estudiantesRetirados'].values[0]
                    A0 = datos_filtrados['estudiantesAprobados'].values[0]
                    initial_conditions = [S0, R0, D0, A0]

                    # Parámetros iniciales
                    lambda_val = 0.1
                    gamma_val = 0.05
                    alpha_val = 0.2
                    beta_val = 0.1

                    # Definir el modelo de ecuaciones diferenciales
                    def model(t, y, lambda_val, gamma_val, alpha_val, beta_val):
                        S, R, D, A = y
                        dSdt = -lambda_val * S - alpha_val * S
                        dRdt = alpha_val * S - gamma_val * R
                        dDdt = lambda_val * S - gamma_val * D
                        dAdt = beta_val * R
                        return [dSdt, dRdt, dDdt, dAdt]

                    # Resolver el modelo
                    def solve_model(initial_conditions, num_cycles, params):
                        t_span = (0, num_cycles - 1)
                        t_eval = np.arange(t_span[0], t_span[1] + 1, 1)
                        sol = solve_ivp(lambda t, y: model(t, y, *params), t_span, initial_conditions, t_eval=t_eval)
                        return sol

                    # Resolver y graficar los resultados
                    params = [lambda_val, gamma_val, alpha_val, beta_val]
                    solution = solve_model(initial_conditions, len(datos_filtrados), params)

                    # Graficar resultados
                    plt.figure(figsize=(10, 6))
                    plt.plot(datos_filtrados['periodo'], datos_filtrados['estudiantesMatriculados'], label='Estudiantes Matriculados (S) - Datos Históricos')
                    plt.plot(datos_filtrados['periodo'], datos_filtrados['estudiantesReprobados'], label='Estudiantes Reprobados (R) - Datos Históricos')
                    plt.plot(datos_filtrados['periodo'], datos_filtrados['estudiantesRetirados'], label='Estudiantes Desertores (D) - Datos Históricos')
                    plt.plot(datos_filtrados['periodo'], datos_filtrados['estudiantesAprobados'], label='Estudiantes Aprobados (A) - Datos Históricos')

                    # Línea vertical para separar los datos históricos de las predicciones
                    ultimo_periodo = datos_filtrados['periodo'].max()
                    plt.axvline(x=ultimo_periodo, color='gray', linestyle='--', label='Inicio de Predicción Futura')

                    # Graficar las predicciones futuras
                    año_futuro = int(input("Ingrese el número de ciclos futuros a predecir: "))
                    total_cycles = len(datos_filtrados) + año_futuro
                    solution_future = solve_model(initial_conditions, total_cycles, params)

                    plt.plot(solution_future.t + datos_filtrados['periodo'].max(), solution_future.y[0], label='Estudiantes Matriculados (S) - Predicción Futura', linestyle='--')
                    plt.plot(solution_future.t + datos_filtrados['periodo'].max(), solution_future.y[1], label='Estudiantes Reprobados (R) - Predicción Futura', linestyle='--')
                    plt.plot(solution_future.t + datos_filtrados['periodo'].max(), solution_future.y[2], label='Estudiantes Desertores (D) - Predicción Futura', linestyle='--')
                    plt.plot(solution_future.t + datos_filtrados['periodo'].max(), solution_future.y[3], label='Estudiantes Aprobados (A) - Predicción Futura', linestyle='--')

                    plt.xlabel('Ciclo')
                    plt.ylabel('Número de Estudiantes')
                    plt.title(f'Predicción de Deserción Estudiantil para {carrera_seleccionada}, Ciclo {ciclo_seleccionado}')
                    plt.legend()
                    plt.grid(True)
                    plt.tight_layout()
                    plt.show()

                else:
                    print(f"No hay datos para el ciclo {ciclo_seleccionado} en {carrera_seleccionada}.")
        elif opcion_prediccion == 2:
            # Predicción a futuro
            año_futuro = int(input("Ingrese el año a futuro para la predicción: "))

            # Filtrar datos históricos para la carrera seleccionada
            datos_historicos = data[data['carrera'] == carrera_seleccionada]

            if not datos_historicos.empty:
                print("Datos históricos:")
                print(datos_historicos)

                # Datos iniciales (últimos datos disponibles)
                ultimo_registro = datos_historicos.iloc[-1]
                S0 = ultimo_registro['estudiantesMatriculados']
                R0 = ultimo_registro['estudiantesReprobados']
                D0 = ultimo_registro['estudiantesRetirados']
                A0 = ultimo_registro['estudiantesAprobados']
                initial_conditions = [S0, R0, D0, A0]

                # Parámetros iniciales
                lambda_val = 0.1
                gamma_val = 0.05
                alpha_val = 0.2
                beta_val = 0.1

                # Definir el modelo de ecuaciones diferenciales
                def model(t, y, lambda_val, gamma_val, alpha_val, beta_val):
                    S, R, D, A = y
                    dSdt = -lambda_val * S - alpha_val * S
                    dRdt = alpha_val * S - gamma_val * R
                    dDdt = lambda_val * S - gamma_val * D
                    dAdt = beta_val * R
                    return [dSdt, dRdt, dDdt, dAdt]

                # Resolver el modelo
                def solve_model(initial_conditions, num_cycles, params):
                    t_span = (0, num_cycles - 1)
                    t_eval = np.arange(t_span[0], t_span[1] + 1, 1)
                    sol = solve_ivp(lambda t, y: model(t, y, *params), t_span, initial_conditions, t_eval=t_eval)
                    return sol

                # Número de ciclos a simular hasta el año futuro
                num_cycles = año_futuro - datos_historicos['periodo'].max() + 1

                # Resolver y graficar los resultados
                params = [lambda_val, gamma_val, alpha_val, beta_val]
                solution_future = solve_model(initial_conditions, num_cycles, params)

                # Graficar resultados futuros
                plt.figure(figsize=(10, 6))
                plt.plot(datos_historicos['periodo'], datos_historicos['estudiantesMatriculados'], label='Estudiantes Matriculados (S) - Datos Históricos')
                plt.plot(datos_historicos['periodo'], datos_historicos['estudiantesReprobados'], label='Estudiantes Reprobados (R) - Datos Históricos')
                plt.plot(datos_historicos['periodo'], datos_historicos['estudiantesRetirados'], label='Estudiantes Desertores (D) - Datos Históricos')
                plt.plot(datos_historicos['periodo'], datos_historicos['estudiantesAprobados'], label='Estudiantes Aprobados (A) - Datos Históricos')

                # Línea vertical para separar los datos históricos de las predicciones
                plt.axvline(x=datos_historicos['periodo'].max(), color='gray', linestyle='--', label='Inicio de Predicción Futura')

                # Graficar las predicciones futuras
                plt.plot(solution_future.t + datos_historicos['periodo'].max(), solution_future.y[0], label='Estudiantes Matriculados (S) - Predicción Futura', linestyle='--')
                plt.plot(solution_future.t + datos_historicos['periodo'].max(), solution_future.y[1], label='Estudiantes Reprobados (R) - Predicción Futura', linestyle='--')
                plt.plot(solution_future.t + datos_historicos['periodo'].max(), solution_future.y[2], label='Estudiantes Desertores (D) - Predicción Futura', linestyle='--')
                plt.plot(solution_future.t + datos_historicos['periodo'].max(), solution_future.y[3], label='Estudiantes Aprobados (A) - Predicción Futura', linestyle='--')

                plt.xlabel('Año')
                plt.ylabel('Número de Estudiantes')
                plt.title(f'Predicción Futura de Deserción Estudiantil para {carrera_seleccionada} hasta el año {año_futuro}')
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                plt.show()
            else:
                print(f"No hay datos históricos para la carrera {carrera_seleccionada}.")
        else:
            print("Opción de predicción no válida.")
    else:
        print("Opción de deserción no válida.")
else:
    print(f"No se pudieron cargar datos para la carrera {carrera_seleccionada}.")
