from flask import jsonify
from webargs.flaskparser import use_args, use_kwargs
from sqlalchemy.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from app import app, db
from app.models.Feed import Feed
from app.models.Item import Item
from app.utils import update_feed, update_all_feeds, prepare_response
from app.validation_schemas import follow_feed_schema, get_all_items_schema

no_feed_msg = "Feed with id {} not found"


@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify(prepare_response(False, messages)), err.code, headers
    else:
        return jsonify(prepare_response(False, messages)), err.code


@app.post('/feeds/follow')
@use_args(follow_feed_schema)
def follow_feed(args):
    """
    Follow new feed
    ---
    parameters:
      - name: name
        in: body
        type: string
        required: true
        example: Test feed
      - name: url
        in: body
        type: string
        required: true
        example: https://feeds.feedburner.com/tweakers/mixed
      - name: owner_email
        in: body
        type: string
        required: false
        default: None
        example: owner@example.com
    definitions:
        FeedResponse:
            type: object
            properties:
                message:
                    $ref: '#/definitions/Feed'
                success:
                    type: boolean
        Feed:
            type: object
            properties:
                id:
                    type: integer
                name:
                    type: string
                url:
                    type: string
                owner_email:
                    type: string
    responses:
        200:
            description: Feed with id
            schema:
                $ref: '#/definitions/FeedResponse'
        400:
            description: Feed with this name or url is already exists

    """
    new_feed = {"name": args["name"], "url": args["url"]}
    if "owner_email" in args:
        new_feed["owner_email"] = args["owner_email"]
    feed = Feed(**new_feed)
    try:
        db.session.add(feed)
        db.session.commit()
        db.session.refresh(feed)
    except IntegrityError as e:
        app.logger.error(e)
        return jsonify(prepare_response(False, "name or url already exists")), 400
    new_feed["id"] = feed.id
    return jsonify(prepare_response(True, new_feed)), 201


@app.post('/feeds/<feed_id>/unfollow')
def unfollow_feed(feed_id):
    """
    Unfollow feed
    ---
    parameters:
      - name: id
        in: url
        type: integer
        required: true
        example: 1
    responses:
        200:
            description: Success status
        404:
            description: Feed with id not found

    """

    feed = Feed.query.filter_by(id=feed_id).first()
    if not feed:
        return jsonify(prepare_response(False, no_feed_msg.format(feed_id))), 404
    db.session.delete(feed)
    db.session.commit()
    return jsonify(prepare_response(True)), 200


@app.post('/feeds/<feed_id>/set_active')
def active_feed(feed_id):
    """
    Make feed active (turn on auto update items)
    ---
    parameters:
      - name: id
        in: url
        type: integer
        required: true
        example: 1
    responses:
        200:
            description: Success status
        404:
            description: Feed with id not found

    """
    feed = Feed.query.filter_by(id=feed_id).first()
    if not feed:
        return jsonify(prepare_response(False, no_feed_msg.format(feed_id))), 404
    feed.active = True
    feed.errors_count = 0
    db.session.commit()
    return jsonify(prepare_response(True)), 200


@app.post('/feeds/<feed_id>/set_inactive')
def inactive_feed(feed_id):
    """
    Make feed inactive (turn off auto update items)
    ---
    parameters:
      - name: id
        in: url
        type: integer
        required: true
        example: 1
    responses:
        200:
            description: Success status
        404:
            description: Feed with id not found
    """
    feed = Feed.query.filter_by(id=feed_id).first()
    if not feed:
        return jsonify(prepare_response(False, no_feed_msg.format(feed_id))), 404
    feed.active = False
    db.session.commit()
    return jsonify(prepare_response(True)), 200


@app.get('/feeds')
def get_all_feeds():
    """
    Get information about all feeds
    ---
    definitions:
        Feeds:
            type: array
            items:
                $ref: '#/definitions/Feed'
        FeedsResponse:
            type: object
            properties:
                message:
                    $ref: '#/definitions/Feeds'
                success:
                    type: boolean

    responses:
        200:
            description: List of feeds
            schema:
                $ref: '#/definitions/FeedsResponse'
    """
    feeds = Feed.query.all()
    feed_list = [feed.to_dict() for feed in feeds]
    return jsonify(prepare_response(True, feed_list))


@app.get('/feeds/<feed_id>')
def get_one_feed(feed_id):
    """
    Get information about one feed
    ---
    definitions:
        FeedFullInfoResponse:
            type: object
            properties:
                message:
                    $ref: '#/definitions/FeedFullInfo'
                success:
                    type: boolean
        FeedFullInfo:
            type: object
            properties:
                id:
                    type: integer
                active:
                    type: boolean
                errors_count:
                    type: integer
                    description: Count of errors while background update
                name:
                    type: string
                url:
                    type: string
                owner_email:
                    type: string
                last_updated:
                    type: string
    responses:
        200:
            description: Feed information
            schema:
                $ref: '#/definitions/FeedFullInfoResponse'
        404:
            description: Feed with id not found
    """
    feed = Feed.query.filter_by(id=feed_id).first()
    if not feed:
        return jsonify(prepare_response(False, no_feed_msg.format(feed_id))), 404
    return jsonify(prepare_response(True, feed.to_dict()))


@app.get('/feeds/<feed_id>/items')
@use_kwargs(get_all_items_schema, location="querystring")
def get_feed_items(feed_id, unread=None):
    """
     Get all items for feed
     ---
     parameters:
       - name: id
         description: Feed id
         in: url
         type: integer
         required: true
         example: 1
       - name: unread
         description: Filter by unread field
         in: querystring
         type: boolean
         required: false
         example: true
     definitions:
         FeedItemsResponse:
             type: object
             properties:
                 message:
                     type: array
                     items:
                         $ref: '#/definitions/Item'
                 success:
                     type: boolean
         Item:
             type: object
             properties:
                 id:
                     type: integer
                 title:
                     type: string
                 url:
                     type: string
                 unread:
                     type: boolean
                 last_updated:
                     type: string
                 feed_id:
                     type: integer
     responses:
         200:
             description: List of feed items
             schema:
                 $ref: '#/definitions/FeedItemsResponse'
         404:
             description: Feed with id not found
     """
    if unread is not None:
        result = Item.query.filter_by(feed_id=feed_id).filter_by(unread=unread).order_by(
            Item.last_updated.desc()).all()
    else:
        result = Item.query.filter_by(feed_id=feed_id).order_by(
            Item.last_updated.desc()).all()

    item_list = [item.to_dict() for item in result]
    return jsonify(prepare_response(True, item_list))


@app.post('/feeds/update')
def force_all_feeds_update():
    """
    Start all feeds update (including inactive)
    ---
    responses:
        200:
            description: Success status
    """
    update_all_feeds()
    return jsonify(prepare_response(True)), 200


@app.post('/feeds/<feed_id>/update')
def force_feed_update(feed_id):
    """
    Force one feed update (not depend on activity)
    ---
    parameters:
      - name: id
        in: url
        description: Feed id
        type: integer
        required: true
        example: 1
    responses:
        200:
            description: Success status
        404:
            description: Feed with id not found
    """
    try:
        update_feed(feed_id)
    except NoResultFound:
        return jsonify(prepare_response(False, no_feed_msg.format(feed_id))), 404
    return jsonify(prepare_response(True)), 200
