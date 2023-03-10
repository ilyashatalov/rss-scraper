from dataclasses import dataclass
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin

from app import db


@dataclass
class Feed(db.Model, SerializerMixin):
    serialize_rules = ('-items',)

    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    url = db.Column(db.String, unique=True, nullable=False)
    items = db.relationship("Item")
    last_updated = db.Column(db.DateTime)
    active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    errors_count = db.Column(db.Integer, server_default='0', nullable=False)
    owner_email = db.Column(db.String, unique=False, nullable=True)

    def __init__(self, name, url, owner_email=None):
        self.name = name
        self.url = url
        if owner_email:
            self.owner_email = owner_email

    def touch(self):
        self.last_updated = datetime.utcnow()
        db.session.commit()
