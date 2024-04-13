from dotenv import load_dotenv
import os
import pyodbc
import pandas as pd

load_dotenv()


connection_string = os.getenv("DB_CONNECTION_STRING")


def create_connection():
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        print("Connection to Azure SQL Database successful!")
        return conn, cursor

    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

def close_connection(conn, cursor):
    if cursor:
        cursor.close()
    if conn:
        conn.close()


        
def query_database(query, conn,cursor):
    """ Run SQL query and return results in a dataframe """
    df = pd.read_sql_query(query, conn)
    close_connection(conn,cursor)
    return df

def get_schema_representation():
    """ Get the database schema in a JSON-like format """
    conn, cursor = create_connection()
    if conn is not None:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE';")
        tables = cursor.fetchall()
 
        db_schema = {} 

        # Retrieving all table data .
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}';")
            columns = cursor.fetchall()

            column_details = {}
            for column in columns:
                column_name, column_type = column
                column_details[column_name] = column_type

            db_schema[table_name] = column_details

        close_connection(conn, cursor)
        return db_schema

# if __name__ == "__main__":
    
    # Querying the database
    # Example: print(query_database("SELECT * FROM your_table"))

    # Getting the schema representation
    # print(get_schema_representation())
