import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)

app.config.from_object(Config)
CORS(app, origins=[app.config['APP_URL']])
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app.api import FlyApi

api = FlyApi(app, prefix='/api')
api.initialize_routes()

from app import routes, models
