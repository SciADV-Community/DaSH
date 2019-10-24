from enum import Enum
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from dash import config
from dash.models import Session
from dash.consts import Engines

Base = declarative_base()


class ModelBase(Base):
    """
    Boilerplate class to manage common behaviour and abstract over the session API.
    """
    id = Column('id', Integer, primary_key=True)
    __tablename__ = "dummytable"

    @classmethod
    def create(cls, session: Session, **kwargs):
        """
        Class helper method to create a new object.
        :param session: the DB session to use
        """
        obj = cls(**kwargs)
        session.add(obj)
        session.commit()

    def delete(self):
        """
        Helper method to delete a certain object.
        """
        session = Session.object_session(self)
        session.delete(self)
        session.commit()

    def save(self):
        """
        Helper method to save changes to a certain object.
        """
        session = Session.object_session(self)
        session.add(self)
        session.commit()


def get_engine():
    """
    Utility function to retrieve the correct engine based on configuration.
    """
    engine, options = config.DATABASE_CONFIG.values()
    url = engine.value
    if engine == Engines.SQLite:
        url += options["filename"]
    elif engine == Engines.MySQL or engine == Engines.PostgreSQL:
        user, password, db_url, db = options.values()
        url += f"{user}:{password}@{db_url}/{db}"

    return create_engine(url)
