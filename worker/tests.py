from pytest import raises

from celery.exceptions import Retry
from app.models.Feed import Feed
# for python 2: use mock.patch from `pip install mock`.
from unittest.mock import patch
from app import app, db
from worker.tasks import update_feeds

TEST_FEED_OK = {"name": "feedburner",
                "url": "https://feeds.feedburner.com/tweakers/mixed",
                "owner_email": "ilya@shatalov.it"}

TEST_FEED_BROKEN = {"name": "broken_feed",
                    "url": "https://feeds.feedburne.com",
                    "owner_email": "ilya@shatalov.it"}


def test_success(celery_app, celery_worker):
    test_feed_ok = Feed(**TEST_FEED_OK)
    test_feed_broken = Feed(**TEST_FEED_BROKEN)
    with app.app_context():
        db.session.add(test_feed_ok)
        db.session.add(test_feed_broken)
        db.session.commit()
        db.session.refresh(test_feed_ok)
        db.session.refresh(test_feed_broken)

    update_feeds().delay()

    # @patch('proj.tasks.Product.order')
    # @patch('proj.tasks.send_order.retry')
    # def test_failure(self, send_order_retry, product_order):
    #     product = Product.objects.create(
    #         name='Foo',
    #     )
    #
    #     # Set a side effect on the patched methods
    #     # so that they raise the errors we want.
    #     send_order_retry.side_effect = Retry()
    #     product_order.side_effect = OperationalError()
    #
    #     with raises(Retry):
    #         send_order(product.pk, 3, Decimal(30.6))
