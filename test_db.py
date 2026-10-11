import psycopg2

credentials_to_try = [
    "postgresql://user:password@127.0.0.1:5432/smart_solar_dev",
    "postgresql://postgres:postgres@127.0.0.1:5432/postgres",
    "postgresql://postgres:password@127.0.0.1:5432/postgres",
    "postgresql://postgres:admin@127.0.0.1:5432/postgres",
    "postgresql://postgres:root@127.0.0.1:5432/postgres",
    "postgresql://smart_solar_dev:password@127.0.0.1:5432/smart_solar_dev",
]

for url in credentials_to_try:
    try:
        conn = psycopg2.connect(url)
        print("SUCCESS:", url)
        conn.close()
    except Exception as e:
        print("FAILED:", url, "->", e)
