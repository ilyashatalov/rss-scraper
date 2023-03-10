from dataclasses import dataclass
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin

from app import db


@dataclass
class Item(db.Model, SerializerMixin):
    serialize_rules = ('-remote_id', )

    feed_id = db.Column(db.Integer, db.ForeignKey('feed.id'), nullable=False)
    id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    url = db.Column(db.String, unique=True, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    unread = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    remote_id = db.Column(db.String, unique=True, nullable=False)

    def __init__(self, title, url, remote_id):
        self.title = title
        self.url = url
        self.remote_id = remote_id
