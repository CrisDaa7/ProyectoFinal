import mysql.connector


class Conexion:
    def __init__(self) -> None:
        #    self.__usernasme
        pass

    def connected(self):
        database = mysql.connector.connect(
            host="localhost", user="root", password="Criss.12345", database="fin"
        )
        return database

    # def connected(self):
    #     database = mysql.connector.connect(
    #         host="localhost", user="root", password="Criss.12345", database="fin"
    #     )
    #     return database
