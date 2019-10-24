from sqlalchemy.orm import sessionmaker
Session = sessionmaker()

from .utils import get_engine
engine = get_engine()

Session.configure(bind=engine)
