import feedparser
from datetime import datetime
from app.models.Feed import Feed
from app.models.Item import Item
from app import app, db


def prepare_response(success, message=None):
    result = {"success": success}
    if message:
        result["message"] = message
    return result


def update_feed(feed_id):
    """
    :param feed_id: Feed id to be updated
    :return: True if everything was ok

    The function has three parts (it's not divided by more funcs because these
    parts are not reusable at the moment):
        1) It parses feed by url
        2) Checks if there are new updates from last_updated feed in our app
        3) Compare feed items by remote id and if there are any new items - adds it to our app
    """
    feed = Feed.query.filter_by(id=feed_id).one()
    app.logger.info(f"Trying to parse feed {feed.name} with url {feed.url}")
    feedparsed = feedparser.parse(feed.url)
    if "bozo_exception" in feedparsed.keys():
        raise Exception(feedparsed.bozo_exception)

    # Check for new items by date in feed
    datetime_str = '%a, %d %b %Y %H:%M:%S %Z'
    feedparsed_date_parsed = datetime.strptime(feedparsed.updated, datetime_str)
    if feed.last_updated and feedparsed_date_parsed < feed.last_updated:
        app.logger.info(f"Seems feed {feed.name} hasn't new items from last update. Skipping...")
        return True

    # retrieve the remote_id field of all users feeds values() method
    list_of_remote_ids = [remote_id for (remote_id,) in db.session.query(Item.remote_id).all()]
    any_new = False
    for e in feedparsed.entries:
        # check if item from feed don't exist it our db
        if e.id not in list_of_remote_ids:
            any_new = True
            entry = Item(title=e.title, url=e.link, remote_id=e.id)
            feed.items.append(entry)
    db.session.commit()
    if any_new:
        app.logger.info(f"Feed {feed.name} was successfully updated")
        feed.touch()
    else:
        app.logger.info(f"No new items in Feed {feed.name} was founded")
    return True


def update_all_feeds():
    feeds = Feed.query.all()
    for feed in feeds:
        update_feed(feed.id)
    return True
