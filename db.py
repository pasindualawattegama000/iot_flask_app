import mysql.connector
from mysql.connector import Error
from config import Config
import os

def create_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            database=Config.DB_DATABASE,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def execute_query(query, params=None, fetch_one=False):
    connection = create_connection()
    cursor = None
    try:
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if query.strip().lower().startswith('select'):
                if fetch_one:
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
            else:
                connection.commit()
                result = cursor.lastrowid
            
            return result
    except Error as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()