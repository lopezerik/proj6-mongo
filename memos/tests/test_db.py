import flask
import nose
import arrow
from pymongo import MongoClient
from flask_main import humanize_arrow_date
import config
import sys

# tests tough cases like tomorrow, weeks, and yesterday
def test_humanize():
    tom = arrow.utcnow().to('local')
    week = tom.shift(days=7)
    week = week.replace(hour=0, minute=0)
    yest = tom.shift(days=-1)
    yest = yest.replace(hour=0, minute=0)
    tom = tom.shift(days=1)
    tom = tom.replace(hour=0, minute=0)
    test1 = humanize_arrow_date(tom)
    test2 = humanize_arrow_date(week)
    test3 = humanize_arrow_date(yest)
    
    assert test1 == "Tomorrow"
    assert test2 == "in 1 week(s)"
    assert test3 == "Yesterday"

CONFIG = config.configuration()

MONGO_CLIENT_URL = "mongodb://{}:{}@{}:{}/{}".format(
    CONFIG.DB_USER,
    CONFIG.DB_USER_PW,
    CONFIG.DB_HOST, 
    CONFIG.DB_PORT, 
    CONFIG.DB)
app = flask.Flask(__name__)
app.secret_key = CONFIG.SECRET_KEY
####
# Database connection per server process
###

try: 
    dbclient = MongoClient(MONGO_CLIENT_URL)
    db = getattr(dbclient, CONFIG.DB)
    collection = db.dated

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)

# tests adding/removing, also sort by date
def test_add_and_remove():
    text = "This is a nose test entry"
    date = "1970-01-01"
    memo = {"type": "nose_memo",
            "date": date,
            "text": text
            }
    text_future = "This is a sort test entry"
    date_future = "1999-12-31"
    future_memo = {"type": "nose_memo",
                    "date": date_future,
                    "text": text_future
                    }
    collection.insert(memo)
    collection.insert(future_memo)
    records = [ ]
    # added .sort to get items in order
    for record in collection.find( { "type": "nose_memo" } ).sort([("date", -1)]):
        record['date'] = arrow.get(record['date']).isoformat()
        del record['_id']
        records.append(record)
    assert records[0]['text'] == "This is a sort test entry"
    assert records[1]['text'] == "This is a nose test entry"
    collection.remove(memo)
    collection.remove(future_memo)

