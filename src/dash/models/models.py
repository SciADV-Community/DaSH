from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from dash.models.utils import ModelBase


class Guild(ModelBase):
    id = Column(String, primary_key=True)  # Discord ID
    name = Column(String)
    roles = relationship("Role", backref="guild")
    channels = relationship("Channel", backref="guild")

    def __repr__(self):
        return self.name


class Game(ModelBase):
    name = Column(String, unique=True)
    aliases = relationship("GameAlias", backref="game")
    channels = relationship("Channel", backref="game")

    def __repr__(self):
        return self.name


class GameAlias(ModelBase):
    name = Column(String, unique=True)
    game_id = Column(Integer, ForeignKey("game.id"))

    def __repr__(self):
        return self.name


class Role(ModelBase):
    name = Column(String)
    guild_id = Column(String, ForeignKey("guild.id"))

    def __repr__(self):
        return self.name


class Channel(ModelBase):
    id = Column(String, primary_key=True)  # Discord ID
    name = Column(String)
    user_id = Column("user_id", String)
    guild_id = Column(String, ForeignKey("guild.id"))
    game_id = Column(Integer, ForeignKey("game.id"))

    def __repr__(self):
        return self.name
