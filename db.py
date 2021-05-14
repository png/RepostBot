from pymongo import MongoClient
import urllib.parse


class Database:
    def __init__(self, username, password, collection):
        username = urllib.parse.quote_plus(username)
        password = urllib.parse.quote_plus(password)

        client = MongoClient(
            'mongodb://%s:%s@127.0.0.1/?authSource=%s' % (username, password, collection))
        db = getattr(client, collection)
        self.cursor = db.Messages
