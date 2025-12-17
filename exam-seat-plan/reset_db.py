import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    # Connect to default database
    con = psycopg2.connect(dbname='postgres', user='postgres', password='root', host='localhost')
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    
    # Drop existing
    print("Dropping existing database...")
    # Force termination of connections to this DB
    cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'exam_seat_plan_db'")
    cur.execute("DROP DATABASE IF EXISTS exam_seat_plan_db")
    
    # Create new
    print("Creating new database...")
    cur.execute("CREATE DATABASE exam_seat_plan_db")
    print("Database reset successfully.")
        
    cur.close()
    con.close()
except Exception as e:
    print(f"Error resetting database: {e}")
