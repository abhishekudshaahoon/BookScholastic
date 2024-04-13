import json
import streamlit as st
import pandas as pd
import sql_azdb
from prompts.prompts import SYSTEM_MESSAGE
from prompts.text_prompt import RESULT_MESSAGE
from prompts.bi import BI_MESSAGE
from openai_prompt.sql_openai import get_completion_from_messages
from openai_prompt.text_openai import get_text_from_messages
from openai_prompt.bi_openai import get_mataplotlib
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import ast
import importlib
import dash
from dash import dcc, html
import sys

def get_formatted_db_schema(formatted_db_schema, prompt, previous_response=None):
    """
    Function to get the formatted database schema and SQL query response.
    If an error occurs, it resends the prompt with the previous response and error.
    """
    try:
        response = get_completion_from_messages(formatted_db_schema, prompt)
        sql_response_lines = response.split('\n')
        code_lines = [line for line in sql_response_lines if line != '```json' and line != '```']
        formatted_sql_response = '\n'.join(code_lines)
        json_response = json.loads(formatted_sql_response)
        query = json_response['query']
        return query
    except Exception as e:
        if previous_response:
            error_message = formatted_db_schema + str(e) + "\n" + previous_response
            response = get_completion_from_messages(error_message, prompt)
            return get_formatted_db_schema(response, prompt, response)
        else:
            print(f"Error: {e}")
            return None

def execute_sql_query(query, conn, cursor):
    """
    Function to execute the SQL query and handle the results.
    """
    try:
        sql_results = sql_azdb.query_database(query, conn, cursor)
        return sql_results
    except Exception as e:
        print(f"SQL Error: {e}")
        return None

def handle_sql_results(prompt, sql_results):
    """
    Function to handle the SQL results and generate the appropriate response.
    """
    if len(sql_results) < 6:
        prompt_formatted_message = RESULT_MESSAGE.format(prompt=prompt)
        text_response = get_text_from_messages(prompt, sql_results)
        st.write(text_response)
        st.dataframe(sql_results)
        st.session_state.messages.append({"role": "assistant", "content": text_response})
    else:
        data = sql_results.values.tolist()
        bi_formatted_message = BI_MESSAGE.format(prompt=prompt)
        bi_response = get_mataplotlib(bi_formatted_message, data)
        formatted_bi_response = format_bi_response(bi_response)
        execute_bi_code(formatted_bi_response, data, sql_results)

def format_bi_response(bi_response):
    """
    Function to format the BI response by removing the code block markers.
    """
    bi_response_lines = bi_response.split('\n')
    code_lines = [line for line in bi_response_lines if line != '```python' and line != '```']
    formatted_bi_response = '\n'.join(code_lines)
    print(formatted_bi_response)
    return formatted_bi_response

def execute_bi_code(formatted_bi_response, data, sql_results):
    """
    Function to execute the generated BI code and handle any errors.
    If an error occurs, it resends the prompt with the previous response and error.
    """
    locals = {}

    # Parse the generated code to extract import statements
    try:
        parsed_code = ast.parse(formatted_bi_response)
    except SyntaxError as e:
        print(f"Syntax Error: {e}")
        return

    # Dynamically import required modules
    for node in ast.walk(parsed_code):
        if isinstance(node, ast.Import):
            for alias in node.names:
                try:
                    importlib.import_module(alias.name)
                except ImportError as e:
                    print(f"Import Error: {e}")
        elif isinstance(node, ast.ImportFrom):
            try:
                imported_module = importlib.import_module(node.module)
                for alias in node.names:
                    full_name = f"{node.module}.{alias.name}"
                    try:
                        imported_submodule = importlib.import_module(full_name)
                        setattr(locals, alias.name, getattr(imported_submodule, alias.name))
                    except ImportError:
                        try:
                            setattr(locals, alias.name, getattr(imported_module, alias.name))
                        except AttributeError:
                            try:
                                locals[alias.name] = importlib.import_module(full_name)
                            except ImportError as e:
                                print(f"Import Error: {e}")
            except ImportError as e:
                print(f"Import Error: {e}")

    try:
        exec(formatted_bi_response, globals(), locals)
    except Exception as e:
        print(f"Code Error: {e}")
        error_message = f"Error: {str(e)}\n\nOriginal Code:\n{formatted_bi_response}"
        bi_response = get_mataplotlib(error_message, data)
        execute_bi_code(bi_response, data, sql_results)
    else:
        generated_fig_func = locals['generate_fig']
        fig = generated_fig_func()
        st.dataframe(sql_results)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, height=400)
        
def main():
    if formatted_db_schema and prompt:
        query = get_formatted_db_schema(formatted_db_schema, prompt)
        if query:
            sql_results = execute_sql_query(query, conn, cursor)
            if sql_results is not None:
                handle_sql_results(prompt, sql_results)

conn_tuple = sql_azdb.create_connection()
conn = conn_tuple[0]  # Extracting the connection object from the tuple
cursor = conn_tuple[1]

# Schema Representation
schemas = sql_azdb.get_schema_representation()
print(schemas)

st.set_page_config(
    page_title="Artemis AI - Conversation with your Data",
    page_icon=" ",
)

# Custom CSS styles
custom_css = """
<style>
    body {
        font-family: 'Arial', sans-serif;
        background-color: #f5f5f5;
    }
    .container {
        max-width: 800px;
        margin: auto;
        padding: 20px;
        background-color: #fff;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        margin-top: 50px;
    }
    .user-input {
        margin-bottom: 20px;
    }
    .generated-query {
        margin-top: 30px;
    }
    .error-message {
        color: #FF0000;
    }
</style>
"""

# Display custom CSS
st.markdown(custom_css, unsafe_allow_html=True)

st.title("Artemis AI - Conversation with your Data")
st.markdown("")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

formatted_db_schema = ""  # Define a default value for formatted_db_schema

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    if prompt and schemas is not None:
        formatted_db_schema = SYSTEM_MESSAGE + f"\nHere is the schema of the table: {schemas}"
    elif not schemas:
        st.error("Connection to DB Failed. Check you have Permission and correct DB Credential")

    with st.chat_message("user"):
        st.markdown(prompt)

    main()

if __name__ == "__main__":
    main()