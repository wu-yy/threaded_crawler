#-*- coding=utf-8 -*-
try:
    import cPickle as pickle
except ImportError:
    import pickle
import zlib
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.binary import Binary


class MongoCache:
    def __init__(self, client=None, expires=timedelta(days=30)):
        self.client = MongoClient('127.0.0.1', 27017) if client is None else client
        # create collection to store cached webpages,
        # which is the equivalent of a table in a relational database
        self.db = self.client.cache
        self.db.webpage.create_index('timestamp', expireAfterSeconds=expires.total_seconds())

    def __contains__(self, url):
        try:
            self[url]
        except KeyError:
            return False
        else:
            return True

    def __getitem__(self, url):
        record = self.db.webpage.find_one({'_id': url})
        if record:
            return record['result']
            #return pickle.loads(zlib.decompress(record['result']))
        else:
            raise KeyError(url + ' does not exist')

    def __setitem__(self, url, result):
        record = {'result': result, 'timestamp': datetime.utcnow()}
        #record = {'result': Binary(zlib.compress(pickle.dumps(result))), 'timestamp': datetime.utcnow()}
        self.db.webpage.update({'_id': url}, {'$set': record}, upsert=True)

    def clear(self):
        self.db.webpage.drop()

if __name__=='__main__':
    cache=MongoCache()
    cache.clear()
    url='http://example.com/view/hello.html'
    result={'html':'...','code':'200'}
    cache[url]=result
    print cache[url]