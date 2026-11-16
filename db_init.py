import mysql.connector
from config import Config

def initialize_database():
    """Initialize the database with required tables"""
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
        cursor.execute(f"USE {Config.MYSQL_DB}")
        
        # Create tables
        create_tables = [
            """
            CREATE TABLE IF NOT EXISTS plans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                duration_months INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS members (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                join_date DATE NOT NULL,
                plan_id INT,
                address TEXT,
                emergency_contact VARCHAR(100),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES plans(id) ON DELETE SET NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS trainers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                specialty VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20) NOT NULL,
                hire_date DATE NOT NULL,
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                member_id INT NOT NULL,
                check_in_time DATETIME NOT NULL,
                check_out_time DATETIME,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS assignments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                member_id INT NOT NULL,
                trainer_id INT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
                FOREIGN KEY (trainer_id) REFERENCES trainers(id) ON DELETE CASCADE
            )
            """
        ]
        
        for table_query in create_tables:
            cursor.execute(table_query)
        
        # Insert initial sample plans data
        initial_plans = [
            "INSERT INTO plans (name, duration_months, price, description) VALUES ('Basic', 1, 29.99, 'Access to basic gym facilities') ON DUPLICATE KEY UPDATE name=name",
            "INSERT INTO plans (name, duration_months, price, description) VALUES ('Standard', 3, 79.99, 'Access to all gym facilities and group classes') ON DUPLICATE KEY UPDATE name=name",
            "INSERT INTO plans (name, duration_months, price, description) VALUES ('Premium', 6, 149.99, 'Access to all facilities, group classes, and 1 weekly session with a trainer') ON DUPLICATE KEY UPDATE name=name",
            "INSERT INTO plans (name, duration_months, price, description) VALUES ('Annual', 12, 249.99, 'Annual membership with all premium benefits and special discounts') ON DUPLICATE KEY UPDATE name=name"
        ]
        
        for plan_query in initial_plans:
            cursor.execute(plan_query)
            
        conn.commit()
        print("Database initialized successfully.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    initialize_database()
