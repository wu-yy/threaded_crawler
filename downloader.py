#-*- coding=utf-8 -*-
import re
import urlparse
import urllib2
import time
from datetime import datetime
import robotparser
import Queue
from bs4 import BeautifulSoup
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import  csv
import lxml.html
import  random
import  cssselect
import socket

DEFAULT_AGENT='wswp'
DEFAULT_DELAY=5
DEFAULT_RETRIES=1
DEFAULT_TIMEOUT=60

class Throttle:
    """Throttle downloading by sleeping between requests to same domain
    """

    def __init__(self, delay):
        # amount of delay between downloads for each domain
        self.delay = delay
        # timestamp of when a domain was last accessed
        self.domains = {}

    def wait(self, url):
        domain = urlparse.urlparse(url).netloc
        last_accessed = self.domains.get(domain)

        if self.delay > 0 and last_accessed is not None:
            sleep_secs = self.delay - (datetime.now() - last_accessed).seconds
            if sleep_secs > 0:
                time.sleep(sleep_secs)
        self.domains[domain] = datetime.now()

class Downloader:
    def __init__(self,delay=5,user_agent='wswp',proxies=None,num_retries=1,timeout=60,opener=None,cache=None):
        socket.setdefaulttimeout(timeout)
        self.throttle=Throttle(delay)
        self.user_agent=user_agent
        self.proxies=proxies
        self.num_retries=num_retries
        self.opener=opener
        self.cache = cache

    def __call__(self,url):
        result=None
        if self.cache:
            try:
                result=self.cache[url]
            except KeyError:
                #网址在缓存里面不可用
                pass
        #else:
            #if result is not None and self.num_retries >0 and 500<=result['code']<600:
                #遇到了服务器的故障 并且重新下载
         #       result=None
        if result==None:
            # 结果并没有在cache中
            #所以仍然需要重新下载
            self.throttle.wait(url)
            proxy=random.choice(self.proxies) if self.proxies else None
            headers={'user_agent':self.user_agent}
            result=self.download(url,headers,proxy,self.num_retries)
            if self.cache:
                #保存结果进入cache
                self.cache[url]=result
        return result['html']

    def download(self,url,headers,proxy,num_retries,data=None):
        print 'Downlaoding:',url
        request=urllib2.Request(url,data,headers or{})
        opener=self.opener or urllib2.build_opener()
        if proxy:
            proxy_params={urlparse.urlparse(url).scheme:proxy}
            opener.add_handler(urllib2.ProxyHandler(proxy_params))
        try:
            response=opener.open(request)
            html=response.read()
            code=response.code
        except Exception as e:
            print 'Download error:',str(e)
            html=''
            if hasattr(e,'code'):
                code=e.code
                if num_retries>0 and 500<=code<600:
                    return self.download(url,headers,proxy,num_retries-1,data)
            else:
                code=None
        return {'html':html,'code':code}





