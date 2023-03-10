from app import app as flask_app
from app import db
from app.models.Feed import Feed
from app.models.Item import Item
import pytest, json

test_feed = {"name": "feedburner",
             "url": "https://feeds.feedburner.com/tweakers/mixed",
             "owner_email": "ilya@shatalov.it"}

test_item1 = {"title": "Spotify brengt TikTok-achtige ontdekkingsfeed uit in thuisscherm ",
              "url": "https://tweakers.net/nieuws/207426/spotify-brengt-tiktok-achtige-ontdekkingsfeed-uit-in-thuisscherm.html",
              "remote_id": "https://tweakers.net/nieuws/207426"
              }
test_item2 = {"title": " Nederlandse regering breidt exportverbod voor ASML-duv-machines uit",
              "url": "https://tweakers.net/nieuws/207424/nederlandse-regering-breidt-exportverbod-voor-asml-duv-machines-uit.html",
              "remote_id": "https://tweakers.net/nieuws/207427"
              }


@pytest.fixture()
def app():
    app = flask_app

    # set up db
    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.drop_all()
    # clean up


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def test_follow_feed(client):
    response = client.post('/feeds/follow',
                           data=json.dumps(test_feed),
                           content_type='application/json')
    assert response.status_code == 201
    assert response.json['success']


def test_unfollow_feed(app, client):
    first_feed = Feed(**test_feed)
    with app.app_context():
        db.session.add(first_feed)
        db.session.commit()
        db.session.refresh(first_feed)
    response = client.post(f'/feeds/{first_feed.id}/unfollow')
    assert response.status_code == 200
    assert response.json['success']
    response = client.post(f'/feeds/{first_feed.id}/unfollow')
    assert response.status_code == 404
    assert not response.json['success']


def test_set_active_feed(app, client):
    first_feed = Feed(**test_feed)
    first_feed.active = False
    first_feed.errors_count = 10
    with app.app_context():
        db.session.add(first_feed)
        db.session.commit()
        db.session.refresh(first_feed)
    id = first_feed.id
    response = client.post(f'/feeds/{id}/set_active')
    assert response.status_code == 200
    assert response.json['success']
    with app.app_context():
        updated_feed = Feed.query.filter_by(id=id).first()
    assert updated_feed.active
    assert updated_feed.errors_count == 0


def test_set_read(app, client):
    first_feed = Feed(**test_feed)
    new_item = Item(**test_item1)
    with app.app_context():
        db.session.add(first_feed)
        db.session.commit()
        db.session.refresh(first_feed)
        feed_id = first_feed.id
        new_item.feed_id = feed_id
        db.session.add(new_item)
        db.session.commit()
        db.session.refresh(new_item)
    item_id = new_item.id
    response = client.patch(f'/items/{item_id}',
                            data=json.dumps({"unread": False}),
                            content_type='application/json')
    assert response.status_code == 200
    assert response.json['success']
    with app.app_context():
        updated_item = Item.query.filter_by(id=item_id).first()
    assert not updated_item.unread


def test_unread_items(app, client):
    first_feed = Feed(**test_feed)
    new_item1 = Item(**test_item1)
    new_item2 = Item(**test_item2)
    with app.app_context():
        db.session.add(first_feed)
        db.session.commit()
        db.session.refresh(first_feed)
        feed_id = first_feed.id
        new_item1.feed_id = feed_id
        new_item1.unread = False
        new_item2.feed_id = feed_id
        db.session.add(new_item1)
        db.session.add(new_item2)
        db.session.commit()
        db.session.refresh(new_item1)
        db.session.refresh(new_item2)
    response = client.get(f'/items?unread=true')
    assert response.json['success']
    assert response.status_code == 200
    assert len(response.json['message']) == 1
    assert response.json['message'][0]['title'] == test_item2["title"]
