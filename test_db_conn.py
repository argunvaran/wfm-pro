import psycopg2
import sys

def test_conn(password):
    try:
        conn = psycopg2.connect(
            user="postgres",
            password=password,
            host="localhost",
            port="5432",
            dbname="postgres"
        )
        print("SUCCESS")
        conn.close()
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    password = sys.argv[1] if len(sys.argv) > 1 else ""
    test_conn(password)
