import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_db():
    try:
        con = psycopg2.connect(user='postgres', password='1234', host='localhost', port='5432')
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        cur.execute("CREATE DATABASE monitor_db")
        cur.close()
        con.close()
        print("Database monitor_db created successfully")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_db()
