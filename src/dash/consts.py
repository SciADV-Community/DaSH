from enum import Enum


class Engines(Enum):
    """
    Enum to represent supported backend database engines.
    """

    SQLite = "sqlite:///"
    MySQL = "mysql://"
    PostgreSQL = "postgresql://"
    Memory = "sqlite://"
