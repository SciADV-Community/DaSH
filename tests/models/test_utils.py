import pytest
from dash.consts import Engines
from dash.models.utils import get_engine


class TestGetEngine():
    @pytest.fixture
    def mock_config(self, monkeypatch):
        def _mock_config(attr: str, value: any):
            monkeypatch.setattr(f"dash.models.utils.config.{attr}", value)

        return _mock_config

    def test_sqlite(self, mock_config):
        mock_config("DATABASE_CONFIG", {
            "engine": Engines.SQLite,
            "options": {
                "filename": "playthrough.db"
            }
        })
        engine = get_engine()
        assert str(engine.url) == "sqlite:///playthrough.db"

    def test_mysql(self, mock_config):
        db = "playthroughBot"
        mock_config("DATABASE_CONFIG", {
            "engine": Engines.MySQL,
            "options": {
                "user": "user",
                "password": "pass",
                "url": "localhost",
                "db": db
            }
        })
        engine = get_engine()
        assert str(engine.url).startswith("mysql://")
        assert str(engine.url).endswith(f"/{db}")

    def test_postgre(self, mock_config):
        db = "playthroughBot"
        mock_config("DATABASE_CONFIG", {
            "engine": Engines.PostgreSQL,
            "options": {
                "user": "user",
                "password": "pass",
                "url": "localhost",
                "db": db
            }
        })
        engine = get_engine()
        assert str(engine.url).startswith("postgresql://")
        assert str(engine.url).endswith(f"/{db}")

