from controls.conexion import Conexion


class HistorialControl:
    def __init__(self) -> None:
        self.__conection = Conexion()

    def get_historial(self):
        conn = self.__conection.connected()
        cusor = conn.cursor(dictionary=True)
        cusor.execute("SELECT * FROM historial")
        result = cusor.fetchall()
        return result
