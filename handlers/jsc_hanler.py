import datetime
import json
import logging
import urllib
from dataclasses import dataclass
from decimal import Decimal

import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv
from shapely.geometry import Point
from sqlalchemy import MetaData, Table, create_engine, inspect
from sqlalchemy.orm import Session

# Load your polygon data, replace 'your_polygon_data.shp' with your file
gdf = gpd.read_file("Jnet_0_gws.shp")
# log_file = open("app.log", "a")


def log_message(message, log_level=logging.INFO):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} [{log_level}]: {message}"
    # log_file.write(message + "\n")
    # log_file.flush()
    print(log_entry)


def get_getway_id(lon, lat):
    point = Point(lon, lat)
    return next(
        (row["ID"] for index, row in gdf.iterrows() if point.within(row["geometry"])),
        None,
    )


load_dotenv()


class Fixture:
    def __init__(self, name, latitude, longitude, id_gateway=None, ident=None, **kwargs):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.id_gateway = id_gateway
        self.ident = ident
        # self.__dict__.update(kwargs)

    def to_dict(self):
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "id_gateway": self.id_gateway,
            "ident": self.ident
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
    driver: str = "{ODBC Driver 18 for SQL Server}"
    timeout: int = 30


class AzureDbConnection:
    def __init__(self, conn_settings: ConnectionSettings, echo: bool = False) -> None:
        self.conn_settings = conn_settings
        self.echo = echo
        self.conn_string = self._construct_connection_string()
        self.metadata = MetaData(schema="dbo")
        self.engine = create_engine(self.conn_string, echo=self.echo, fast_executemany=True)
        self.conn = self.engine.connect()
        self.tbl_fixtures = Table("tbl_fixtures", self.metadata, autoload_with=self.conn)
        self.session = Session(self.engine)
        # self.conn.begin()

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

    # def connect(self):

    # self.metadata = MetaData(schema="dbo.tbl_fixtures")
    # self.metadata.create_all(self.engine)
    # self.metadata.bind = self.engine
    # # self.tbl_fixtures = self.metadata.tables["tbl_fixtures"]
    # self.tbl_fixtures = Table(
    #     "tbl_fixtures",
    #     self.metadata,
    # )
    # self.session = Session(self.engine)

    def disconnect(self):
        self.conn.close()
        self.engine.dispose()

    def get_all_table_names(self):
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def select_fixture(self) -> pd.DataFrame:
        query = self.tbl_fixtures.select()
        output = self.conn.execute(query)
        results = output.fetchall()
        return pd.DataFrame(results)

    def insert_fixture(self, fixture: Fixture):
        fixture_dict = fixture.to_dict()
        try:
            query = self.tbl_fixtures.insert().values(**fixture_dict).returning(self.tbl_fixtures.columns.id)
            result = self.conn.execute(query)
            log_message(f"Fixture {fixture.name} was added successfully")
            return result.scalar()
        except Exception as e:
            log_message(f"An error occured: {str(e)}", log_level=logging.ERROR)
            return None

    def delete_fixture(self, fixture_id=None, fixture_name=None):
        try:
            if fixture_id is None:
                query = self.tbl_fixtures.delete().where(self.tbl_fixtures.columns.name == fixture_name)
            else:
                query = self.tbl_fixtures.delete().where(self.tbl_fixtures.columns.id == fixture_id)
            log_message(f"Fixture {fixture_name} was deleted successfully")
            return self.conn.execute(query)
        except Exception as e:
            log_message(f"An error occured: {str(e)}", log_level=logging.ERROR)
            return None

    def update_fixture(self, fixture: Fixture, fixture_name=None, fixture_id=None):
        fixture_dict = fixture.to_dict()
        if fixture_id is None:
            query = (
                self.tbl_fixtures.update().values(**fixture_dict).where(self.tbl_fixtures.columns.name == fixture_name)
            )
        elif fixture_name is None:
            query = self.tbl_fixtures.update().values(**fixture_dict).where(self.tbl_fixtures.columns.id == fixture_id)
        return self.conn.execute(query)

    def fixture_exists(self, fixture_name) -> bool:
        try:
            query = self.tbl_fixtures.select().where(self.tbl_fixtures.columns.name == fixture_name)
            output = self.conn.execute(query)
            results = output.fetchall()
            return len(results) != 0
        except Exception as e:
            log_message(f"An error occured- Didnt find SN: {str(e)}", log_level=logging.ERROR)
            return False


# if __name__ == "__main__":
# print(get_getway_id(34.791, 32.085))

# log_file.close()
