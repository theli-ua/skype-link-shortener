#!/usr/bin/python
# -*- coding: utf-8 -*-
# enable X11 multi-threading
#from Skype4Py.api.posix_x11 import threads_init
#threads_init()
# use X11 based API instead of D-Bus
#from Skype4Py.api.posix_x11 import SkypeAPI

import Skype4Py
import signal
import sys
import re

import httplib2
import urllib

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        raise ImportError("You need to have a json parser, easy_install simplejson")

class Googl:
    """Access Goo.gl url shorten"""

    def __init__(self, key=None, baseurl="https://www.googleapis.com/urlshortener/v1/url",
                        user_agent="python-googl"):
        self.key = key
        self.conn = httplib2.Http()
        self.baseurl = baseurl
        self.user_agent = user_agent

    def _request(self, url="", method="GET", body="", headers=None, userip=None):
        """send request and parse the json returned"""
        if not url:
            url = self.baseurl
        elif not url.startswith("http"):
            url = "%s?%s" % (self.baseurl, url)
        if self.key is not None:
            url +=  "%s%s" % ( ("?" if "?" not in url else "&"), "key=%s" % self.key)
        if userip:
            url +=  "%s%s" % ( ("?" if "?" not in url else "&"), "userip=%s" % userip)
        if headers is None:
            headers = {}
        if "user-agent" not in headers:
            headers['user-agent'] = self.user_agent
        return json.loads(self.conn.request(url, method, body=body, headers=headers)[1])

    def shorten(self, url, userip=None):
        """shorten the url"""
        body =json.dumps(dict(longUrl=url))
        headers = {'content-type':'application/json'}
        return self._request(method="POST", body=body, headers=headers, userip=userip)

    def expand(self, url, analytics=False, userip=None):
        """expand the url"""
        data = dict(shortUrl=url)
        if analytics:
            data['projection'] = 'FULL'
        if userip:
            data['userip'] = userip
        url = urllib.urlencode(data)

        return self._request(url)

def signal_handler(signal, frame):
        print 'You pressed Ctrl+C!'
        sys.exit(0)
# Fix Skype4Py spelling issue
Skype4Py.Skype._SetEventHandlerObj = Skype4Py.Skype._SetEventHandlerObject

class SkypeHandler:

    def __init__(self):

        self.client = self.get_client()
        
        self.client.Attach()

        self.googl = Googl()

        _octet = r'(?:2(?:[0-4]\d|5[0-5])|1\d\d|\d{1,2})'
        _ipAddr = r'%s(?:\.%s){3}' % (_octet, _octet)
        # Base domain regex off RFC 1034 and 1738
        _label = r'[0-9a-z][-0-9a-z]*[0-9a-z]?'
        _domain = r'%s(?:\.%s)*\.[0-9a-z][-0-9a-z]+' % (_label, _label)
        _urlRe = r'(\w+://(?:\S+@)?(?:%s|%s)(?::\d+)?(?:/[^\])>\s]*)?)' % (_domain,
                                                                           _ipAddr)
        urlRe = re.compile(_urlRe, re.I)
        _httpUrlRe = r'(https?://(?:\S+@)?(?:%s|%s)(?::\d+)?(?:/[^\])>\s]*)?)' % \
                     (_domain, _ipAddr)
        httpUrlRe = re.compile(_httpUrlRe, re.I)

        self.url_re = urlRe

    def shorten(self, m):
        url = m.group(1)
        if url.startswith('http://goo.gl/'):
            return url
        res = self.googl.shorten(url)
        if 'id' in res:
            return res['id']
        return url
        
    def get_client(self):
        """ Reveice Skype4Py.Skype instance
        ** Maybe launch Skype if not launched?
        """
        #skype = Skype4Py.Skype(Events=self, Api=SkypeAPI({}))
        skype = Skype4Py.Skype(Events=self)


        if not skype.Client.IsRunning:
            skype.Client.Start()

        return skype

    def MessageStatus(self, msg, status):
        """ Skype event handler """
        print status, msg.Body
        if status not in ['SENT', 'RECEIVED']:
        #if status != 'RECEIVED':
            return

        if msg.Chat.MyRole in ['MASTER', 'CREATOR']:
            body = msg.Body
            body = re.sub(self.url_re, self.shorten, body)
            if msg.Body != body:
                msg.Body = body
        sys.exit(1)

if __name__ == '__main__':
    SkypeHandler()
    # Allow Ctrl+C while running
    #signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal_handler)
    print 'Press Ctrl+C'
    signal.pause()
