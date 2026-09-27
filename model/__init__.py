from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from model.projeto import Projeto  # noqa: E402,F401
