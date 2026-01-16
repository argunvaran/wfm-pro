import psycopg2

passwords = ["postgres", "password", "123456", "admin", "root", "1234", "1q2w3e4r"]

def try_conn(password):
    try:
        conn = psycopg2.connect(
            user="postgres",
            password=password,
            host="localhost",
            port="5432",
            dbname="postgres"
        )
        print(f"SUCCESS:{password}")
        conn.close()
        return True
    except Exception as e:
        # print(f"FAILED:{password} - {e}")
        return False

found = False
for p in passwords:
    if try_conn(p):
        found = True
        break

if not found:
    print("ALL_FAILED")
