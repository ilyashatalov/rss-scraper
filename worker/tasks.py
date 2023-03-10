from celery import Celery
from datetime import timedelta

from app import app, db
from app.models.Feed import Feed
from app.utils import update_feed
from worker.notifyer import NotificationFactory
from worker.Config import Config

config = Config().get_config()
celery = Celery(app.name, broker=config["CELERY_BROKER_URL"])

celery.conf.beat_schedule["update_feeds"] = {'task': 'worker.tasks.update_feeds',
                                             "schedule": timedelta(seconds=config["SCHEDULE_INTERVAL_SEC"])}


@celery.task(max_retries=config["MAX_RETRIES"], retry_backoff=True, retry_backoff_max=5)
def update_feeds():
    """
    Takes all active feeds and trying to update each one.
    If feed fails - call @retry_fail_feed to retry or fail it
    """
    with app.app_context():
        feeds_for_update = Feed.query.filter_by(active=True).all()
        for feed in feeds_for_update:
            try:
                update_feed(feed.id)
            except Exception as e:
                app.logger.warning(f'Something wrong with feed {feed.name}\n Error: {e}')
                retry_fail_feed(feed.id)
    return True


def retry_fail_feed(feed_id):
    """
    Checks that the number of errors for this feed has not exceeded the value of the variable MAX_RETRIES.
    If it did, makes it inactive and trying to send notification.
    """
    with app.app_context():
        failed = Feed.query.filter_by(id=feed_id).one()
        if failed.errors_count >= config["MAX_RETRIES"]:
            app.logger.info(f'Deactivating feed {failed.name} with id {failed.id} due to errors')
            failed.active = False
            db.session.commit()
            if config["NOTIFICATION"] and failed.owner_email:
                NotificationFactory.create_notification(config["NOTIFICATION_TYPE"],
                                                        "MS_3Ew0Os@shatalov.it",
                                                        f"Auto update from feed {failed.name} turned off due to errors"
                                                        # failed.owner_email,
                                                        ).send_notification()

            return True
        else:
            failed.errors_count += 1
            app.logger.info(f'Feed {failed.name} with id {failed.id} update failed {failed.errors_count} time')
            db.session.commit()
            return False
