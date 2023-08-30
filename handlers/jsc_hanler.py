from dataclasses import dataclass
from sqlalchemy import create_engine, inspect
import urllib
import os
import json
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()
class Fixture:
    def __init__(self, name=None, latitude=None, longitude=None, id_gateway=None, **kwargs):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.id_gateway = id_gateway

    def to_dict(self):
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "id_gateway": self.id_gateway
            # Add other properties here if needed
        }

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal and datetime objects."""
    def default(self, o):
        return str(o) if isinstance(o, Decimal) else super(DecimalEncoder, self).default(o)

@dataclass(frozen=True)
class ConnectionSettings:
    """Connection Settings."""
    server: str
    database: str
    username: str
    password: str
    driver: str = '{ODBC Driver 18 for SQL Server}'
    timeout: int = 30

class AzureDbConnection:
    def __init__(self, conn_settings: ConnectionSettings, echo: bool = False) -> None:
        self.conn_settings = conn_settings
        self.echo = echo
        self.conn_string = self._construct_connection_string()

    def _construct_connection_string(self) -> str:
        conn_params = urllib.parse.quote_plus(
            f"Driver={self.conn_settings.driver};"
            f"Server=tcp:{self.conn_settings.server}.database.windows.net,1433;"
            f"Database={self.conn_settings.database};"
            f"Uid={self.conn_settings.username};"
            f"Pwd={self.conn_settings.password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout={self.conn_settings.timeout};"
        )
        return f"mssql+pyodbc:///?odbc_connect={conn_params}"

    def connect(self):
        self.engine = create_engine(self.conn_string, echo=self.echo, fast_executemany=True)
        self.conn = self.engine.connect()

    def get_tables(self) -> dict:
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        return {"tables": tables}

    def get_table_columns(self, table_name: str) -> dict:
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name)
        column_names = [column["name"] for column in columns]
        return {"columns": column_names}

    def execute_query(self, query: str) -> dict:
        result = self.conn.execute(query)
        rows = []
        for row in result:
            row_dict = {}
            for key, value in row._mapping.items():
                if isinstance(value, Decimal):
                    row_dict[key] = str(value)
                elif isinstance(value, bytes):
                    try:
                        row_dict[key] = value.decode("utf-8")
                    except UnicodeDecodeError:
                        row_dict[key] = value.hex()
                else:
                    row_dict[key] = value
            rows.append(row_dict)
        return rows
    def insert_into_table(self, table_name: str, values_dict: dict):
        columns = ", ".join(values_dict.keys())
        placeholders = ", ".join(f"'{value}'" for value in values_dict.values())
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return self.execute_query(insert_query)


    def update_table(self, table_name: str, values_dict: dict, condition: str):
        set_clause = ", ".join(f"{key} = '{value}'" for key,value in values_dict)
        update_query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"
        self.conn.execute(update_query, **values_dict)

    def select_n_rows(self, table_name: str, n: int):
        select_query = f"SELECT TOP {n} * FROM {table_name}"
        return self.execute_query(select_query)
    def select_all_rows(self, table_name: str):
        select_query = f"SELECT * FROM {table_name}"
        return self.execute_query(select_query)
    def select_all_rows_where(self, table_name: str, condition: str):
        select_query = f"SELECT * FROM {table_name} WHERE {condition}"
        return self.execute_query(select_query)
    def select_all_rows_where_and(self, table_name: str, condition1: str, condition2: str):
        select_query = f"SELECT * FROM {table_name} WHERE {condition1} AND {condition2}"
        return self.execute_query(select_query)
    def select_all_rows_where_or(self, table_name: str, condition1: str, condition2: str):
        select_query = f"SELECT * FROM {table_name} WHERE {condition1} OR {condition2}"
        return self.execute_query(select_query)
    def select_all_rows_where_and_and(self, table_name: str, condition1: str, condition2: str, condition3: str):
        select_query = f"SELECT * FROM {table_name} WHERE {condition1} AND {condition2} AND {condition3}"
        return self.execute_query(select_query)
    def delete_all_rows_where(self, table_name: str, condition: str):
        delete_query = f"DELETE FROM {table_name} WHERE {condition}"
        self.conn.execute(delete_query)
    def delete_sn(self, table_name: str, sn: str):
        delete_query = f"DELETE FROM {table_name} WHERE name = '{sn}'"
        self.conn.execute(delete_query)
    
    def disconnect(self):
        self.conn.close()
        self.engine.dispose()

if __name__ == "__main__":
    conn_settings = ConnectionSettings(
        server=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        username=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD")
    )

    db_conn = AzureDbConnection(conn_settings)
    try:
        db_conn.connect()
        
        # Get a list of tables
        tables_result = db_conn.get_tables()
        print(json.dumps(tables_result, indent=4))

        table_name = "tbl_fixtures"
        
        # Get columns of a table
        columns_result = db_conn.get_table_columns(table_name)
        print(json.dumps(columns_result, indent=4))

        # Select all rows from the table
        select_query = f"SELECT * FROM {table_name}"
        select_result = db_conn.execute_query(select_query)
        print (select_result)
        # print(json.dumps(select_result, indent=4))
        fixtur_data = {
            "name": "test",
            "latitude": 123.456,
            "longitude": 789.012,
            "id_gateway": 1
        }
        
        Fixture = Fixture(**fixtur_data)
        print(Fixture.to_dict())
        
        res = db_conn.insert_into_table(table_name, Fixture.to_dict())
        pass
        res = db_conn.update_table(table_name, {"name": "test2"}, "name = 'test'")
        # Handle other operations (insert, update, delete) as needed
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
    finally:
        db_conn.disconnect()
