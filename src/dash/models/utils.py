# pylint: disable=no-self-argument, no-member
from enum import Enum
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import as_declarative, declarative_base, declared_attr
from dash import config
from dash.models import Session
from dash.consts import Engines


@as_declarative()
class ModelBase(object):
    """
    Boilerplate class to manage common behaviour and abstract over the session API.
    """

    id = Column("id", Integer, primary_key=True, autoincrement=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @classmethod
    def create(cls, **kwargs):
        """
        Class helper method to create a new object.
        :param session: the DB session to use
        """
        obj = cls(**kwargs)
        session = Session()
        session.add(obj)
        session.commit()
        return obj

    @classmethod
    def filter(cls, **kwargs):
        """
        Helper method to query objects.
        """
        return Session.query(cls).filter_by(**kwargs)

    @classmethod
    def get(cls, **kwargs):
        """
        Helper method to get a specific object.
        """
        return cls.filter(**kwargs).first()

    @classmethod
    def get_or_create(cls, **kwargs):
        obj = cls.get(**kwargs)
        if obj:
            return obj

        return cls.create(**kwargs)

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
