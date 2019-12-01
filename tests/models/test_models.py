# pylint: disable=unused-wildcard-import
import pytest
from dash.models import *


@pytest.mark.usefixtures("init_db")
class ModelTest:
    def teardown_method(self):
        Session.remove()


class TestGame(ModelTest):
    @staticmethod
    def create_game(name="sample game"):
        return Game.create(name=name)

    def test_create(self):
        name = "sample game"
        self.create_game(name)
        game = Game.get(name=name)
        assert game.name == name
        assert str(game) == name

        assert str(GameAlias.filter(game=game)[0]) == name

    def test_delete(self):
        game = self.create_game()
        game.delete()

        game = Game.get(name=game.name)
        assert game is None

    def test_update(self):
        game = self.create_game()
        game.name = "sample game 2"
        game.save()

        game = Game.get(id=game.id)
        assert game.name == "sample game 2"


class TestGameAlias(ModelTest):
    def test_create(self):
        game = TestGame.create_game()
        GameAlias.create(name="some other game", game=game)

        game = Game.get(name=game.name)
        assert len(game.aliases) == 2
        assert str(game.aliases[1]) == "some other game"


class TestGuild(ModelTest):
    @staticmethod
    def create_guild(_id=1234567890, name="guild"):
        return Guild.create(id=_id, name=name)

    def test_create(self):
        guild = self.create_guild()
        assert str(guild) == "guild"
        assert guild.id == 1234567890


class TestRole(ModelTest):
    @staticmethod
    def create_role(_id=1234567890, name="Chaos;Child"):
        return Role.create(id=_id, name=name)

    def test_create(self):
        name = "Chaos;Child"
        guild = TestGuild.create_guild()
        role = self.create_role()
        guild.roles.append(role)
        Session().commit()

        guild = Guild.get(id=guild.id)
        assert len(guild.roles) == 1
        assert str(guild.roles[0]) == name


class TestChannel(ModelTest):
    @staticmethod
    def create_channel(_id=1234567890, user_id=1234567890, name="test-plays-whatever"):
        return Channel.create(id=_id, user_id=user_id, name=name)

    def test_create(self):
        guild = TestGuild.create_guild()
        game = TestGame.create_game()
        channel = self.create_channel()
        channel.game = game
        guild.channels.append(channel)
        Session().commit()

        guild = Guild.get(id=guild.id)
        assert len(guild.channels) == 1
        assert str(guild.channels[0]) == channel.name

        game = Game.get(name=game.name)
        assert len(game.channels) == 1


class TestCategory(ModelTest):
    @staticmethod
    def create_category(
        _id=1234567890, name="test-category", full=False, archival=False
    ):
        return Category.create(id=_id, name=name, full=full, archival=archival)

    def test_create(self):
        category = self.create_category()
        guild = TestGuild.create_guild()
        category.guild = guild
        game = TestGame.create_game()
        category.game = game
        channel = TestChannel.create_channel()
        category.channels.append(channel)
        category.save()

        # Test relationships
        assert len(guild.categories) == 1
        assert guild.categories[0].name == category.name

        assert len(game.categories) == 1
        assert game.categories[0].name == category.name

        assert channel.category == category

