import json
import os
import urllib
from dataclasses import dataclass
from decimal import Decimal

import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
)

# Load your polygon data, replace 'your_polygon_data.shp' with your file
gdf = gpd.read_file("Jnet_0_gws.shp")

from shapely.geometry import Point, Polygon


def get_getway_id(lon, lat):
    point = Point(lon, lat)
    return next(
        (row["ID"] for index, row in gdf.iterrows() if point.within(row["geometry"])),
        None,
    )


load_dotenv()


class Fixture:
    def __init__(self, name, latitude, longitude, id_gateway=None, **kwargs):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.id_gateway = id_gateway
        # self.__dict__.update(kwargs)

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
    driver: str = "{ODBC Driver 18 for SQL Server}"
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
        self.metadata = MetaData(bind=self.engine)
        self.tbl_fixtures = Table(
            "tbl_fixtures",
            self.metadata,
        )

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
            return result.scalar()
        except Exception as e:
            print(e)
            return None

    def delete_fixture(self, fixture_id=None, fixture_name=None):
        try:
            if fixture_id is None:
                query = self.tbl_fixtures.delete().where(self.tbl_fixtures.columns.name == fixture_name)
            else:
                query = self.tbl_fixtures.delete().where(self.tbl_fixtures.columns.id == fixture_id)
            return self.conn.execute(query)
        except Exception as e:
            print(e)
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
            print(e)
            return False


if __name__ == "__main__":
    print(get_getway_id(34.791, 32.085))
