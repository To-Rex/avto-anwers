# import os
# import psycopg2
# import json
# from datetime import datetime
# from dotenv import load_dotenv
#
# # Load environment variables from .env file
# load_dotenv()
#
# DATABASE_URL = os.getenv('DATABASE_URL')
# print(DATABASE_URL)
#
#
# # Connect to PostgreSQL
# def connect_db():
#     try:
#         conn = psycopg2.connect(DATABASE_URL)
#         return conn
#     except Exception as e:
#         print(f"Failed to connect to the database: {e}")
#         return None
#
#
# # Create a table to store the data if it doesn't already exist
# def create_table(conn):
#     with conn.cursor() as cur:
#         cur.execute('''
#         CREATE TABLE IF NOT EXISTS bot_responses (
#             id SERIAL PRIMARY KEY,
#             key TEXT UNIQUE,
#             value TEXT[],
#             active BOOLEAN DEFAULT TRUE,
#             working_count INT DEFAULT 0,
#             added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );
#         ''')
#         conn.commit()
#
#
# # Insert data from JSON file into the PostgreSQL table
# def insert_data_from_json(conn, json_file):
#     with open(json_file, 'r') as f:
#         data = json.load(f)
#
#     with conn.cursor() as cur:
#         for key, values in data.items():
#             # Ensure `values` is a list of strings
#             if isinstance(values, list):
#                 values = [str(v) for v in values]
#             else:
#                 values = [values]  # Convert single string to a list
#
#             try:
#                 cur.execute('''
#                     INSERT INTO bot_responses (key, value)
#                     VALUES (%s, %s)
#                     ON CONFLICT (key) DO NOTHING;
#                 ''', (key, values))
#             except Exception as e:
#                 print(f"Error inserting data: {e}")
#                 continue
#         conn.commit()
#
#
# def delete_table(conn, table_name):
#     with conn.cursor() as cur:
#         cur.execute(f"DROP TABLE {table_name};")
#         conn.commit()
#
#
# # Fetch data from PostgreSQL
# def fetch_data(conn, key):
#     with conn.cursor() as cur:
#         cur.execute("SELECT value, active, working_count FROM bot_responses WHERE key = %s;", (key,))
#         result = cur.fetchone()
#         if result and result[1]:  # Check if the response is active
#             cur.execute("UPDATE bot_responses SET working_count = working_count + 1 WHERE key = %s;", (key,))
#             conn.commit()
#             return result[0]  # Return the list of response messages
#         else:
#             return None
#
#
# # Insert a new entry into the database with additional fields
# def insert_new_entry(conn, key, values):
#     if not isinstance(values, list):
#         values = [values]  # Convert single value to a list
#
#     with conn.cursor() as cur:
#         try:
#             cur.execute('''
#                 INSERT INTO bot_response (key, value, added_time)
#                 VALUES (%s, %s, %s)
#                 ON CONFLICT (key) DO NOTHING;
#             ''', (key, values, datetime.now()))
#             conn.commit()
#         except Exception as e:
#             print(f"Error inserting new entry: {e}")
#
#
# # working_count + 1
# def _working_count(conn, key):
#     with conn.cursor() as cur:
#         cur.execute("UPDATE bot_responses SET working_count = working_count + 1 WHERE key = %s;", (key,))
#         conn.commit()
#
#
# def get_data_from_db():
#     if not connect_db():
#         return {}
#     try:
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT key, value FROM bot_responses;")
#             data = {row[0]: row[1] for row in cursor.fetchall()}
#             print(data)
#         return data
#     except Exception as e:
#         print(f"Error fetching data from the database: {e}")
#         return {}
#     finally:
#         conn.close()
#
#
# if __name__ == "__main__":
#     conn = connect_db()
#     if conn:
#         #delete_table(conn, 'bot_responses')
#         create_table(conn)
#
#         insert_data_from_json(conn, 'data_list.json')
#         get_data_from_db()
#         # Example of fetching data and updating working count
#         key_to_search = "salom"
#         response = fetch_data(conn, key_to_search)
#         if response:
#             print(f"Response for '{key_to_search}': {response}")
#         else:
#             print(f"No active response found for '{key_to_search}'")
#
#         # Insert a new entry example
#         insert_new_entry(conn, "yangi_kalit", ["Bu yangi qiymat", "Boshqa variant"])
#
#         conn.close()
import json
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


def connect_db():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        return conn
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        return None


def add_working_count(conn, user_message):
    with conn.cursor() as cursor:
        cursor.execute(
            sql.SQL("UPDATE bot_responses SET working_count = working_count + 1 WHERE key = %s;"),
            (user_message,)
        )
        conn.commit()


def backup_db_to_json(conn):
    backup_dir = "backup"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"'{backup_dir}' papkasi yaratildi.")
    backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT key, value FROM bot_responses;")
            data = {row[0]: row[1] for row in cursor.fetchall()}
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            output_data = {
                "timestamp": current_time,
                "data": data
            }
            with open(backup_file, 'w') as f:
                json.dump(output_data, f, indent=4)
            print(f"Ma'lumotlar '{backup_file}' fayliga muvaffaqiyatli saqlandi.")
    except Exception as e:
        print(f"Xato yuz berdi: {e}")
    finally:
        conn.close()
