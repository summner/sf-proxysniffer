#!/usr/bin/env python2.7

import urlparse
from urllib import quote as urlquote

from twisted.web import proxy, http
from twisted.internet import reactor
from twisted.python import log
import sys

import re
from datetime import datetime

import gzip, cStringIO

log.startLogging(sys.stdout)

    

sfgamePat = re.compile("http://s[0-9]\.sfgame\.pl/.*")

class SF:
    def __init__(self, uri, command, headers, baseData):
        self.created = datetime.now()
        self.req_uri = uri
        self.command = command
        self.headers = headers
        self.baseData = baseData
        self.buffer = cStringIO.StringIO()
    def handlePart( self, buffer):
        print type(buffer)
        self.buffer.write(buffer)
       

    def handleEnd(self):        
        if self.buffer:
            self.buffer.seek(0)
            gzipper = gzip.GzipFile(fileobj=self.buffer)
            gz = gzipper.read()
            print gz


class ProxyClientT ( proxy.ProxyClient ):
    def __init__(self, command, rest, version, headers, data, father):
        proxy.ProxyClient.__init__(self, command, rest, version, headers, data, father)
        self.sf = None
        if sfgamePat.match(rest):
            self.sf = SF(rest, command, headers, data)



    def handleHeader(self, key, value):
        proxy.ProxyClient.handleHeader(self,key,value)
        if self.sf:
            print "header:", key, value

    def handleResponsePart(self, buffer ):
        proxy.ProxyClient.handleResponsePart(self, buffer)
        if self.sf:
            self.sf.handlePart(buffer)

    def handleResponseEnd(self):
        proxy.ProxyClient.handleResponseEnd(self)
        if self.sf:
            self.sf.handleEnd()


class ProxyClientFactoryT ( proxy.ProxyClientFactory ):
    protocol = ProxyClientT

class ProxyRequestT ( proxy.ProxyRequest ):
    protocols = {'http': ProxyClientFactoryT}

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
        clientFactory = class_(self.method, self.uri, self.clientproto, headers,
                               s, self)
#self.reactor.connectTCP(host, port, clientFactory)
        self.reactor.connectTCP("wro-proxy.eu.tieto.com", 8080, clientFactory)
    
class ProxyT( proxy.Proxy ):
    requestFactory=ProxyRequestT

class ProxyFactory(http.HTTPFactory):
    protocol = ProxyT

#    def __init__(self, *args, **kw):
#      http.HTTPFactory.__init__(self,*args, **kw)

    
            
reactor.listenTCP(8080, ProxyFactory())
reactor.run()
