# rss-scraper
RSS Scraper is a test application n which saves RSS feeds to a database and lets a user view and manage feeds they've added to the system through an API.

## Description
Feeds (and feed items) updates in a background task, asynchronously, periodically and in an unattended manner.

Also, there is a notification service that supports any kind of notification type (can be extended, only email supports now)

Technically, it's a flask application with a PostgreSQL database and celery+redis broker for asynchronous tasks.

Please keep in mind some points of my realisation that I made to avoid wasting time because, as I said before, I have full-time work now:
1) I didn't represent all fields of feeds and items; Model expanding is easy but needs time
2) I didn't cover all endpoints with tests but covered some of them to give you an understanding of my approach
3) I didn't have time to finish the test of the background update service, but the service worked well. If it will be a decisive point, I can do it later. 

## Quick Start (Production mode, docker environment)

This repo provides quick start docker-compose file for hassle-free usage.

### Requirements:
* docker engine (https://docs.docker.com/engine/install/)
* docker-compose (https://docs.docker.com/compose/install/)

### Instruction:
1. Clone repo:
    ```bash
    git clone https://github.com/ilyashatalov/rss-scraper.git
    ```
2. Start application:
   ```bash
   docker-compose up -d
   ```
*Don't mind that app and celery services will be errored at start of command. They will start as soon as the container is builded*

It will:
1) Pull Redis and PostgreSQL images from the docker hub.
2) Create persistent docker volume for PostgreSQL,
3) Build container for the main app, celery worker and celery beat.
4) Configure services between each other
5) Forward ports (for main app port 80). 
Postgresql and Redis ports are forwarded too, but you can disable them by commenting on these lines in the docker-compose file—application 
using docker-network for these purposes by default.

You can provide your configuration through the docker-compose file. Pass it as an environment variable to the docker service (this way has the highest priority). You can see an example with 
* app:
    ```bash
    SQLALCHEMY_DATABASE_URI=<sql alchemy url>
    ```
* celery worker and beat (default values are here):
    ```bash
    # SCHEDULER
    MAX_RETRIES=3
    SCHEDULE_INTERVAL_SEC = 10
    
    # Celery
    CELERY_BROKER_URL=redis://localhost:6379/0
    
    # Notifier
    NOTIFICATION=False
    NOTIFICATION_TYPE=email
    SMTP_SERVER=
    SMTP_PORT=
    SMTP_LOGIN=
    SMTP_PASSWORD=
    ```

### API Reference
There are integrated API references in the application that are available on page http://127.0.0.1/apidocs/ after the start of the main app.
### Let's try some URLs
1. Follow feed
    ```bash
    curl -X POST localhost/feeds/follow -H 'Content-Type: application/json' -d '{"name": "first", "url": "https://feeds.feedburner.com/tweakers/mixed"}'
    ```
   Result
    ```json
    {
      "message": {
        "id": 1,
        "name": "first",
        "url": "https://feeds.feedburner.com/tweakers/mixed"
      },
      "success": true
    }
    ```
   If you try to send this request again there are will be an error (url and name should be uniq)
    ```json
    {
      "message": "name or url already exists",
      "success": false
    }
    ```
2. Update items for a feed from a remote source. There are two ways - wait for auto-updating or force update. 
Follow feed method doesn't pull items from feed during /feed/follow request because it could be long or contain errors. The client should manage it.
    ```bash
    curl localhost:5000/feeds/1/update -X POST
    ```
    Result:
    ```json
    {
      "success": true
    }
    ```
3. Get items for this feed
    ```bash
    curl localhost:5000/feeds/1/items
    ```
    Result:
    ```json
    {
      "message": [
        {
          "id": 40,
          "last_updated": "2023-03-10 14:20:33",
          "title": "Videokaart Best Buy Guide - Update maart 2023",
          "unread": true,
          "url": "https://tweakers.net/reviews/10946/videokaart-best-buy-guide-update-maart-2023.html"
        },
        {
          "id": 39,
          "last_updated": "2023-03-10 14:20:33",
          "title": "Tweakers Podcast #259 - Roltelefoons, early access-scams en socialemediaverboden",
          "unread": true,
          "url": "https://tweakers.net/geek/207410/tweakers-podcast-259-roltelefoons-early-access-scams-en-socialemediaverboden.html"
        }, ...
      ],
    "success": true
   }
    ```
4. All items are unread. Let's read one
   ```bash
   curl -X PATCH localhost/items/1 -d '{"unread": "false"}' -H 'Content-Type: application/json'
   ```
   Result:
    ```json
    {
      "success": true
    }
    ```
5. And now we can filter our items with unread flag
    ```bash
    curl localhost/feeds/1/items?unread=false
    ```
    Result
    ```json
    {
      "message": [
        {
          "feed_id": 1,
          "id": 1,
          "last_updated": "2023-03-10 15:17:35",
          "title": "Nintendo toont nieuwe trailer The Super Mario Bros. Movie",
          "unread": false,
          "url": "https://tweakers.net/geek/207496/nintendo-toont-nieuwe-trailer-the-super-mario-bros-movie.html"
        }
      ],
      "success": true
    }
    ```
6. Follow another feed and force update
   ```bash
   curl -X POST localhost/feeds/follow -H 'Content-Type: application/json' -d '{"name": "nu.nl", "url": "http://www.nu.nl/rss/Algemeen"}'
   curl localhost/feeds/2/update -X POST   
   ```
   Read one item from new feed:
   ```bash
   curl -X PATCH localhost/items/41 -d '{"unread": "false"}' -H 'Content-Type: application/json'
   ```
   Get all already read items (from all feeds):
   ```bash
    curl "localhost/items?unread=false"
    ```
   Result
   ```json
    {
      "message": [
        {
          "feed_id": 2,
          "id": 41,
          "last_updated": "2023-03-10 15:32:32",
          "title": "Kabinet schrapt per direct de laatste coronaregels",
          "unread": false,
          "url": "https://www.nu.nl/coronavirus/6252775/kabinet-schrapt-per-direct-de-laatste-coronaregels.html"
        },
        {
          "feed_id": 1,
          "id": 1,
          "last_updated": "2023-03-10 15:17:35",
          "title": "Nintendo toont nieuwe trailer The Super Mario Bros. Movie",
          "unread": false,
          "url": "https://tweakers.net/geek/207496/nintendo-toont-nieuwe-trailer-the-super-mario-bros-movie.html"
        }
      ],
      "success": true
    }
    ```
   
## Development setup
### Requirements
Firstly, you need redis and postgresql servers, so you can use provided docker-compose file again.
Don't forget to change variables in compose-file, e.g. database credentials
```bash
docker-compose up redis db -d
```
Install requirements for project and pytest
```bash
pip install -r requirements.txt pytest
```
Configure environment variables
```bash
cd app
cp env .env
vim .env
cd worker
cp env .env
vim .env
```
### Start app
Start app in dev mode
```bsah
flask run --reload
```
Start celery worker and beat
```bash
celery  -A worker.celery worker -B -l debug
```
### Tests
Take care,  database will be **cleaned up** after every test. So, it's better to use another database for test runs. It's simple with dotenv configuration, just pass it as the environment variable (it will be prioritized). But don't forget to create it before
```bash
SQLALCHEMY_DATABASE_URI="postgresql://rssapp:rssapp@localhost:5432/rssscraper_test" pytest -s -W ignore::DeprecationWarning worker/tests.py
```
Result
```bash
====================================== test session starts ==============================
platform darwin -- Python 3.10.1, pytest-7.2.2, pluggy-1.0.0
rootdir: /Users/ish/Git/github.com/ilyashatalov/rss-scraper
collected 5 items                                                                                                                                                                                                                      

app/tests.py .....

===================================== 5 passed in 0.42s ==================================
```
