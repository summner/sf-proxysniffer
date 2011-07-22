#!/usr/bin/env python2.7

import urlparse
from urllib import quote as urlquote

from twisted.web import proxy, http

from twisted.internet import reactor
from twisted.python import log
import sys

import re
import threading
from datetime import datetime

import gzip, cStringIO

log.startLogging(sys.stdout)

    

sfgamePat = re.compile("http://s[0-9]\.sfgame\.pl/request.*")
sfURIre = re.compile(u".*req=(?P<hash>.{32})(?P<id>.+?)\&.*rnd=(?P<rnd>[0-9]+).*")
t= u"http://s8.sfgame.pl/request.php?req=33d2FS09VQ82T6K423G99f14096812ddd4010&random=%2&rnd=26672031"

class SFParseException(Exception):
    def __init__(self, uri, other_info=""):
        self.uri=uri
        self.other_info= other_info
    def __str__(self):
        return repr("URL: %s \nOther: %s " % (self.uri, self.other_info))

tavern = "010"
arena = "011"



class BasePageParser:
    callback=None

    def __init__(self):
        pass
    
    def preparse_numbers(self, data):
        return data.split("/") 

    def parsing_muscle(self, uri, data):
        return None
    
    def parse(self, uri, data):
        ret = self.parsing_muscle(uri, data)

        if ret and self.callback:
            self.callback(ret, uri, self)
        
        return ret

class CollectingParser( BasePageParser ):
    push_lock = threading.Lock() 
    collection = []

    def __init__(self, parser=None):
        BasePageParser.__init__(self)
        self.parser = parser
    
    def parsing_muscle(self, uri, data):
        if self.parser:
            page_data = self.parser.parse(uri, data)
        else:
            page_data = data
            
        if self.push_lock.acquire():
            self.collection.append(page_data)
            self.push_lock.release()

        #print
        if self.push_lock.acquire(False):
            for i in range(len(self.collection)):
                j = i + 2
                if j < len(self.collection):
                    cnt=0
                    for a, b in zip(self.collection[i], self.collection[j]):
                        if a != b:
                            pass #print "ole!", cnt, a, b
                        cnt += 1
            self.push_lock.release()
        
       

class TavernParser( BasePageParser ):
    def parsing_muscle(self, uri, data):
        base = self.preparse_numbers(data)
        current_gold = base[13]
        adv = []
        adv.append(( int(base[280]), int(base[283]), int(base[241]) ))
        adv.append(( int(base[281]), int(base[284]), int(base[242]) ))
        adv.append(( int(base[282]), int(base[285]), int(base[243]) ))
        high_exp = 0
        res_exp = 0
        high_gold = 0
        for i in range( len(adv) ):
            exp, gold, time = adv[i]
            t_exp = exp/time
            t_gold = gold/time
            if t_exp > high_exp:
                res_exp = i
                high_exp = t_exp
            
        print current_gold
        print
        print
        print res_exp+1
        print
        print
        cnt =0 
        return base
        


matchParser = [  (re.compile("010"), TavernParser()), (re.compile(".*"), BasePageParser()) ]

class SF:
    def __init__(self, uri, raw_data ):
        self.created = datetime.now()
        self.raw_data = raw_data
        self.uri = uri

        match = sfURIre.match(uri)
        if match:
            if match.group("id"):
                self.page_id = match.group("id")
            else:
                raise SFParseException(uri, "Paged ID not matched")
        else:
            raise SFParseException(uri, "not matched the re")
        self.buffer = cStringIO.StringIO()
        self.parser = self.findParser(self.page_id)
        print "aha", self.page_id
    
    def findParser( self, id ):
        for pat, parser in matchParser:
            if pat.match(id):
                return parser
        return None
            
        
    def handlePart( self, buffer):
        print type(buffer)
        self.buffer.write(buffer)
       

    def handleEnd(self):        
        if self.buffer:
            self.buffer.seek(0)
            gzipper = gzip.GzipFile(fileobj=self.buffer)
            gz = gzipper.read()
            if gz and self.parser:
                self.parser.parse(self.uri, gz)


class ShakeProxyClient ( proxy.ProxyClient ):
    def __init__(self, command, rest, version, headers, data, father):
        proxy.ProxyClient.__init__(self, command, rest, version, headers, data, father)
        self.sf = None
        if sfgamePat.match(self.father.uri):
            self.sf = SF(self.father.uri, {"father_uri": self.father.uri, "uri": rest, "cmd": command, "headers": headers, "data": data})

    def handleHeader(self, key, value):
        proxy.ProxyClient.handleHeader(self,key,value)
        if self.sf:
            pass
            #print "header:", key, value

    def handleResponsePart(self, buffer ):
        proxy.ProxyClient.handleResponsePart(self, buffer)
        if self.sf:
            self.sf.handlePart(buffer)

    def handleResponseEnd(self):
        proxy.ProxyClient.handleResponseEnd(self)
        if self.sf:
            self.sf.handleEnd()


class ShakeProxyClientFactory ( proxy.ProxyClientFactory ):
    protocol = ShakeProxyClient

class ShakeProxyThroughProxyRequest ( proxy.ProxyRequest ):
    protocols = {'http': ShakeProxyClientFactory }

    def process(self):
        parsed = urlparse.urlparse(self.uri)
        protocol = parsed[0]
        host = parsed[1]
        port = self.ports[protocol]
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        rest = urlparse.urlunparse(('', '') + parsed[2:])
        if not rest:
            rest = rest + '/'
        class_ = self.protocols[protocol]
        headers = self.getAllHeaders().copy()
        if 'host' not in headers:
            headers['host'] = host
        self.content.seek(0, 0)
        s = self.content.read()
        clientFactory = class_(self.method, rest, self.clientproto, headers,
                               s, self)
#        self.reactor.connectTCP(host, port, clientFactory)
        self.reactor.connectTCP("wro-proxy.eu.tieto.com", 8080, clientFactory)
class ShakeProxyThroughProxy( proxy.Proxy ):
    requestFactory = ShakeProxyThroughProxyRequest


class ShakeProxyRequest ( proxy.ProxyRequest ):
    protocols = {'http': ShakeProxyClientFactory }
    
class ShakeProxy( proxy.Proxy ):
    requestFactory = ShakeProxyRequest

class ShakeProxyFactory(http.HTTPFactory):
    protocol = ShakeProxy

#    def __init__(self, *args, **kw):
#      http.HTTPFactory.__init__(self,*args, **kw)

                
reactor.listenTCP(8080, ShakeProxyFactory())
reactor.run()
