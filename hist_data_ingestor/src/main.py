import os
import psycopg2

DB_USER = os.getenv('POSTGRES_USER')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_HOST = os.getenv('POSTGRES_HOST', 'timescaledb')  # service name in docker-compose
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB')

def main():
    print("Testing TimescaleDB connection...")
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("✅ Successfully connected to TimescaleDB!")
        conn.close()
    except Exception as e:
        print(f"❌ Failed to connect to TimescaleDB: {e}")

if __name__ == "__main__":
    main()
