import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # MySQL configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_DATABASE = os.getenv('DB_DATABASE', 'greenhouse')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')