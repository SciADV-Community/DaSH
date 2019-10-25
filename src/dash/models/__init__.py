from sqlalchemy.orm import sessionmaker, scoped_session

Session = scoped_session(sessionmaker())

from .utils import get_engine
from .models import Game
