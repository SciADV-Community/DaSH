import pytest
from dash.models import Session, Game


@pytest.mark.usefixtures("init_db")
class ModelTest:
    def teardown_method(self):
        Session.remove()


class TestGame(ModelTest):
    def test_create(self):
        name = "sample game"
        Game.create(name=name)
        game = Game.get(name=name)
        assert game.name == name
