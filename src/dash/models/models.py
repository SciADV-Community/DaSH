from sqlalchemy import Column, String, ForeignKey
from dash.models.utils import ModelBase

class Game(ModelBase):
    name = Column("name", String, unique=True)

    def __repr__(self):
        return self.name