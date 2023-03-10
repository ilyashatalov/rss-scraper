from flask import jsonify
from webargs.flaskparser import use_args, use_kwargs

from app import app, db
from app.models.Item import Item
from app.validation_schemas import set_read_schema, get_all_items_schema
from app.utils import prepare_response

no_item_msg = "Item with id {} not found"


@app.patch('/items/<item_id>')
@use_kwargs(set_read_schema)
def set_read(item_id, unread):
    """
    Read/unread item
    ---
    parameters:
      - name: unread
        in: body
        type: json
        required: true
        example: {unread: false}
    responses:
        200:
            description: Success status
        404:
            description: Item with id not found

    """
    item = Item.query.filter_by(id=item_id).first()
    if not item:
        return jsonify(prepare_response(False, no_item_msg.format(item_id))), 404
    if unread == "true":
        item.unread = True
    else:
        item.unread = False
    db.session.commit()
    return jsonify(prepare_response(True)), 200


@app.get('/items')
@use_args(get_all_items_schema, location="querystring")
def get_all_items(args):
    """
     List all items for all feeds
     ---
     parameters:
       - name: unread
         description: Filter by unread field
         in: querystring
         type: boolean
         required: false
         example: true
     responses:
         200:
             description: List of items
             schema:
                 $ref: '#/definitions/FeedItemsResponse'
     """
    if "unread" in args:
        items = Item.query.filter_by(unread=args["unread"]).order_by(
            Item.last_updated.desc()).all()
    else:
        items = Item.query.order_by(Item.last_updated.desc()).all()

    item_list = [item.to_dict() for item in items]

    return jsonify(prepare_response(True, item_list)), 200


@app.get('/items/<item_id>')
def get_one_item(item_id):
    """
     Get one item by id
     ---
     parameters:
       - name: id
         description: Item id
         in: url
         type: integer
         required: true
         example: 1
     definitions:
         ItemResponse:
             type: object
             properties:
                 message:
                     "$ref": '#/definitions/Item'
                 success:
                     type: boolean
     responses:
         200:
             description: Item
             schema:
                 $ref: '#/definitions/ItemResponse'
         404:
             description: File with id not found
     """
    item = Item.query.filter_by(id=item_id).first()
    if not item:
        return jsonify(prepare_response(False, no_item_msg.format(item_id))), 404
    return jsonify(prepare_response(True, item.to_dict()))
