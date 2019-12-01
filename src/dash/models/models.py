# pylint: disable=bad-super-call,no-member
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from dash.models.utils import ModelBase


class Guild(ModelBase):
    id = Column(Integer, primary_key=True)  # Discord ID
    name = Column(String)
    roles = relationship("Role", backref="guild", cascade="delete")
    channels = relationship("Channel", backref="guild", cascade="delete")
    categories = relationship("Category", backref="guild", cascade="delete")

    def __repr__(self):
        return self.name


class Game(ModelBase):
    name = Column(String, unique=True)
    aliases = relationship("GameAlias", backref="game", cascade="delete")
    channels = relationship("Channel", backref="game", cascade="delete")
    categories = relationship("Category", backref="game", cascade="delete")
    roles = relationship("Role", backref="game")
    channel_suffix = Column(String, default="")

    def __repr__(self):
        return self.name

    @classmethod
    def get_by_alias(cls, alias):
        """Helper method to get a Game instance based on its name, or alias.
        Comparison is done in all lowercase for both sides.
        """
        ret = Game.get(name=alias)
        if not ret:
            ret = GameAlias.get(name=alias)
            ret = ret.game if ret else None
        return ret

    @classmethod
    def create(cls, **kwargs):
        # Hooking into the inherited classmethod
        # to register the game's name as a game alias.
        self = super(ModelBase, cls).create(**kwargs)
        GameAlias.create(name=self.name.lower(), game=self)
        return self


class GameAlias(ModelBase):
    name = Column(String, unique=True)
    game_id = Column(Integer, ForeignKey("game.id"))

    def __repr__(self):
        return self.name

    @classmethod
    def create(cls, **kwargs):
        # Hooking into the inherited classmethod
        # to ensure all aliases are lowercase
        kwargs["name"] = kwargs["name"].lower()
        return super(ModelBase, cls).create(**kwargs)


class Role(ModelBase):
    id = Column(Integer, primary_key=True)  # Discord ID
    name = Column(String)
    guild_id = Column(String, ForeignKey("guild.id"))
    game_id = Column(String, ForeignKey("game.id"))

    def __repr__(self):
        return self.name


class CompletionRole(Role):
    id = Column(Integer, ForeignKey("role.id"), primary_key=True)
    # TODO Maybe something with "meta class" relations here?


class Category(ModelBase):
    id = Column(Integer, primary_key=True)  # Discord ID
    name = Column(String)
    guild_id = Column(Integer, ForeignKey("guild.id"))
    game_id = Column(Integer, ForeignKey("game.id"))
    archival = Column(Boolean, default=False)
    full = Column(Boolean, default=False)
    channels = relationship("Channel")

    def __repr__(self):
        return f"{self.name} - {'Full' if self.full else 'Available'}"


class Channel(ModelBase):
    id = Column(Integer, primary_key=True)  # Discord ID
    name = Column(String)
    user_id = Column(Integer)
    guild_id = Column(Integer, ForeignKey("guild.id"))
    game_id = Column(Integer, ForeignKey("game.id"))
    category_id = Column(Integer, ForeignKey("category.id"))
    category = relationship("Category", back_populates="channels")

    def __repr__(self):
        return self.name
