import ssl
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from logging.config import dictConfig
from flasgger import Swagger

load_dotenv()

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }}})

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SWAGGER'] = {
    'title': 'RSS Scraper API Docs v0.1',
}
swagger = Swagger(app)
db = SQLAlchemy(app)

from app.models.Feed import Feed
from app.models.Item import Item

with app.app_context():
    db.create_all()

from app.views.feeds import get_all_feeds, get_feed_items, follow_feed, unfollow_feed, update_feed, \
    force_all_feeds_update, force_feed_update
from app.views.items import set_read, get_all_items
