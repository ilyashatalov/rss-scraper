from webargs import fields, validate

follow_feed_schema = {
    "name": fields.Str(required=True, validate=validate.Length(min=3)),
    "url": fields.Url(required=True),
    "owner_email": fields.Str(required=False),
}

set_read_schema = {
    "unread": fields.Bool(required=True),
}

get_all_items_schema = {
    "unread": fields.Bool(required=False),
}
