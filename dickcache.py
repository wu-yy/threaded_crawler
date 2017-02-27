#-*- coding=utf-8 -*-
import  os
import re
import urlparse
import shutil
import zlib
from datetime import datetime, timedelta
try:
    import cPickle as pickle
except ImportError:
    import pickle
from link_crawler import link_crawler

class DiskCache:
    def __init__(self,cache_dir='cache',expires=timedelta(days=30),compress=True):
        self.cache_dir=cache_dir
        self.expires=expires
        self.compress=compress

    #从URL 中建立文件名
    def url_to_path(self,url):
        #建立缓存的系统路径从这个URL
        components=urlparse.urlsplit(url)
        path=components.path
        if not path:
            path='/index.html'
        elif path.endswith('/'):
            path+='index.html'

        filename=components.netloc+path+components.query

        filename=re.sub('[^/0-9a-zA-Z\-.,; ]','_',filename)

        filename='/'.join(segment[:255] for segment in filename.split('/'))

        return os.path.join(self.cache_dir,filename)

    # 根据文件名存取数据
    def __getitem__(self, url):
        #载入数据从disk中根据这个url
        path=self.url_to_path(url)
        if os.path.exists(path):
            with open(path,'rb')as fp:
                data=fp.read()
                if self.compress:
                    data=zlib.decompress(data)
                result,timestamp=pickle.loads(data)
                if self.has_expired(timestamp):
                    raise KeyError(url+'has expired')
                return result
        else:
            #URL还没有被缓存进入cache中
            raise KeyError(url+'does not exits')

    def __setitem__(self, url, result):
        #从这个url中缓存数据进入cache
        path=self.url_to_path(url)
        folder=os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)

        data=pickle.dumps((result,datetime.utcnow()))
        if self.compress:
            data=zlib.compress(data)

        with open(path,'wb') as fp:
            fp.write(data)

    def __delitem__(self, url):
        #删除这个key的结果
        path=self.url_to_path(url)
        try:
            os.remove(path)
            os.removedirs(os.path.dirname(path))
        except OSError:
            pass

    def has_expired(self,timestamp):
        return datetime.utcnow()>timestamp+self.expires


    def clear(self):
        #删除所有的cache缓存
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

if __name__ == '__main__':
    link_crawler('http://example.webscraping.com/', '/(index|view)',max_depth=1, cache=DiskCache(compress=False))
    #cache=DiskCache()
    #print cache['http://example.webscraping.com/view/Afghanistan-1']

