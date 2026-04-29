import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "inventory-dbms-secret"
    JWT_SECRET = os.environ.get("JWT_SECRET") or "inventory-dbms-jwt-secret"

    DB_HOST = os.environ.get("DB_HOST") or "localhost"
    DB_PORT = int(os.environ.get("DB_PORT") or "3306")
    DB_USER = os.environ.get("DB_USER") or "root"
    DB_PASSWORD = os.environ.get("DB_PASSWORD") or "tanfrost#1806"
    DB_NAME = os.environ.get("DB_NAME") or "inventory_py"
