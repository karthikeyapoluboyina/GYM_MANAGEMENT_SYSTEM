import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    PORT = int(os.getenv('PORT', 5000))

    # Support both .env names and Railway/cloud MySQL variable names
    MYSQL_HOST = os.getenv('MYSQL_HOST') or os.getenv('MYSQLHOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER') or os.getenv('MYSQLUSER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD') or os.getenv('MYSQLPASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB') or os.getenv('MYSQLDATABASE', 'gym_management_db')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT') or os.getenv('MYSQLPORT', 3306))
