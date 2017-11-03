"""
Flask web app connects to Mongo database.
Keep a simple list of dated memoranda.

Representation conventions for dates: 
   - We use Arrow objects when we want to manipulate dates, but for all
     storage in database, in session or g objects, or anything else that
     needs a text representation, we use ISO date strings.  These sort in the
     order as arrow date objects, and they are easy to convert to and from
     arrow date objects.  (For display on screen, we use the 'humanize' filter
     below.) A time zone offset will 
   - User input/output is in local (to the server) time.  
"""

import flask
from flask import g
from flask import render_template
from flask import request
from flask import url_for

import json
import logging

import sys

# Date handling 
import arrow   
from dateutil import tz  # For interpreting local times

# Mongo database
from pymongo import MongoClient

import config
CONFIG = config.configuration()


MONGO_CLIENT_URL = "mongodb://{}:{}@{}:{}/{}".format(
    CONFIG.DB_USER,
    CONFIG.DB_USER_PW,
    CONFIG.DB_HOST, 
    CONFIG.DB_PORT, 
    CONFIG.DB)


print("Using URL '{}'".format(MONGO_CLIENT_URL))


###
# Globals
###

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



###
# Pages
###

@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Main page entry")
  g.memos = get_memos()
  for memo in g.memos: 
      app.logger.debug("Memo: " + str(memo))
  return flask.render_template('index.html')

@app.route("/add_memo")
def add_memo():
    return flask.render_template('add_memo.html')

@app.route("/_save_memo")
def _save_memo():
    # Retrieve info from page and add to database
    text = flask.request.args.get("text")
    date = flask.request.args.get("dat")
    print("save memo date = " + date)
    memo = {"type": "dated_memo",
            "date": date,
            "text": text
            }
    collection.insert(memo)
    # Faux return variable
    status = {"stat": "true"}
    return flask.jsonify(result=status)
    
@app.route("/_del_memo")
def _del_memo():
    # Delete memo with this info from db
    text = flask.request.args.get("text")
    date = flask.request.args.get("dat")
    memo = {"type": "dated_memo",
            "date": date,
            "text": text
            }
    collection.remove(memo)
    # Faux return variable
    status = {"stat": "true"}
    return flask.jsonify(result=status)

@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('page_not_found.html',
                                 badurl=request.base_url,
                                 linkback=url_for("index")), 404

#################
#
# Functions used within the templates
#
#################
def test_yo():
    print("")

@app.template_filter( 'humanize' )
def humanize_arrow_date( date ):
    """
    Date is internal UTC ISO format string.
    Output should be "today", "yesterday", "in 5 days", etc.
    Arrow will try to humanize down to the minute, so we
    need to catch 'today' as a special case. 
    """
    try:
        then = arrow.get(date).to('local').to('utc')
        rnow = arrow.utcnow().to('local')
        # get rid of hours, messes with calculations
        rnow = rnow.replace(hour=0, minute=0, seconds=0)
        if then.date() == rnow.date():
            human = "Today"
        else: 
            human = then.humanize(rnow)
            humanParts = human.split(" ")
            if human == "in a day":
                human = "Tomorrow"
            elif human == "a day ago":
                human = "Yesterday"
            # 'hours' means the date is tomorrow
            elif "hours" in human:
                human = "Tomorrow"
            # if format is of type "in x days", calculate weeks if possible
            elif len(humanParts[1]) < 3:
                if ((int(humanParts[1]) % 7) == 0):
                    human = "in {} week(s)".format(int(int(humanParts[1]) / 7))
    except: 
        print("Excepted")
        human = date
    return human


#############
#
# Functions available to the page code above
#
##############
def get_memos():
    """
    Returns all memos in the database, in a form that
    can be inserted directly in the 'session' object.
    """
    records = [ ]
    # added .sort to get items in order
    for record in collection.find( { "type": "dated_memo" } ).sort([("date", -1)]):
        record['date'] = arrow.get(record['date']).isoformat()
        del record['_id']
        records.append(record)
    return records 


if __name__ == "__main__":
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    app.run(port=CONFIG.PORT,host="0.0.0.0")

    
