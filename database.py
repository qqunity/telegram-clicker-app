import os
import psycopg2
from urllib.parse import urlparse

class Database:
    _instance = None
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance
    
    def connect(self):
        try:
            DATABASE_URL = os.getenv('DATABASE_URL')
            if not DATABASE_URL:
                print("Ошибка: DATABASE_URL не установлен")
                return
                
            url = urlparse(DATABASE_URL)
            self.connection = psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
            )
            print("Успешное подключение к БД")
            
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
    
    def get_connection(self):
        if self.connection is None or self.connection.closed:
            self.connect()
        return self.connection 