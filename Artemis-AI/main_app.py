# main_app.py

import streamlit as st
import pandas as pd
import sql_azdb
from prompts.prompts import SYSTEM_MESSAGE
from azure_openai import get_completion_from_messages
import json

# Create or connect to Azure database
conn_tuple = sql_azdb.create_connection()
conn = conn_tuple[0]  # Extracting the connection object from the tuple


def query_database(query):
    """ Run SQL query and return results in a dataframe """
    return pd.read_sql_query(query, conn)


# Schema Representation 
schemas = sql_azdb.get_schema_representation()
# print(schemas['dgdb'])

# Format the system message with the schema
formatted_system_message = SYSTEM_MESSAGE.format(schema=schemas)

# Generate the SQL query from the user message
user_message = ""

# Use GPT-4 to generate the SQL query
response = get_completion_from_messages(formatted_system_message, user_message)
print("Response from get_completion_from_messages:", response)
json_response = json.loads(response)
query = json_response['query']
print(query)

# Run the SQL query
sql_results = query_database(query)
print(sql_results)

