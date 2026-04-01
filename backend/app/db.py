import pymysql
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def get_db_connection():
    """
    Crée et retourne une connexion à la base de données MySQL.
    Utilise DictCursor pour retourner les résultats sous forme de dictionnaires.
    """
    connection = pymysql.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection
