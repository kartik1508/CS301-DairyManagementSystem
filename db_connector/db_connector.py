# db_connector.py
import mysql.connector
from dotenv import load_dotenv
import os



class DBConfig:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

def load_db_config():
    load_dotenv()
    return DBConfig(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def create_connection():
    config = load_db_config()
    connection = None
    try:
        connection = mysql.connector.connect(
            host=config.host,
            user=config.user,
            password=config.password
        )
        if connection.is_connected():
            print(f"Connected to MySQL Server version {connection.get_server_info()}")
            return connection
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()
        print("Connection closed")
