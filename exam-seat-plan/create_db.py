import pymysql as MySQLdb

def create_database():
    try:
        # Connect to MySQL Server (Default: localhost, root, no password)
        db = MySQLdb.connect(host="localhost", user="root", passwd="")
        cursor = db.cursor()
        
        # Drop and Create DB
        cursor.execute("DROP DATABASE IF EXISTS exam_seat_plan_db")
        cursor.execute("CREATE DATABASE exam_seat_plan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("Database 'exam_seat_plan_db' dropped and recreated successfully.")
        
        db.close()
    except Exception as e:
        print(f"Error creating database: {e}")

if __name__ == "__main__":
    create_database()
