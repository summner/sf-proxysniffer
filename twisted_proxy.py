#!/usr/bin/env python2.7

import urlparse
from urllib import quote as urlquote
from twisted.web import proxy, http
from twisted.python import log
from twisted.internet import reactor

import re, sys, threading
import gzip, cStringIO

from datetime import datetime

#log.startLogging

handlerPatterns=[]

def install_shake_handler(uri_pattern, handler):
    handlerPatterns.append((re.compile(uri_pattern), handler))


class ShakeHandler:
    def __init__(self, uri):
        pass
    def handleHeader(self, key, value):
        pass
    def handleResponsePart(self, buffer):
        pass
    def handleResponseEnd(self):
        pass
        

class ShakeProxyClient ( proxy.ProxyClient ):
    def __init__(self, command, rest, version, headers, data, father):
        proxy.ProxyClient.__init__(self, command, rest, version, headers, data, father)
        self.handler = None

        for pat, handler in handlerPatterns:
            if pat.match( self.father.uri ):
                self.handler = handler(self.father.uri)
                break
        #TODO: add handling of outgoing data for POST requests                                           

    def handleHeader(self, key, value):
        proxy.ProxyClient.handleHeader(self,key,value)
        if self.handler:
            self.handler.handleHeader(key, value)            

    def handleResponsePart(self, buffer ):
        proxy.ProxyClient.handleResponsePart(self, buffer)
        if self.handler:
            self.handler.handleResponsePart(buffer)

    def handleResponseEnd(self):
        proxy.ProxyClient.handleResponseEnd(self)
        if self.handler:
            self.handler.handleResponseEnd()


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
        clientFactory = class_(self.method, self.uri, self.clientproto, headers,
                               s, self)
        
        self.reactor.connectTCP(out_proxy_host, out_proxy_port, clientFactory)


class ShakeProxyThroughProxy( proxy.Proxy ):
    requestFactory = ShakeProxyThroughProxyRequest


class ShakeProxyRequest ( proxy.ProxyRequest ):
    protocols = {'http': ShakeProxyClientFactory }
    
class ShakeProxy( proxy.Proxy ):
    requestFactory = ShakeProxyRequest

class ShakeProxyFactory(http.HTTPFactory):
    protocol = ShakeProxyThroughProxy
    def __init__(self, proxy_class = ShakeProxy ):
        protocol = proxy_class
        http.HTTPFactory.__init__(self)

#    def __init__(self, *args, **kw):
#      http.HTTPFactory.__init__(self,*args, **kw)

in_proxy_port = 8080        
out_proxy_host = "wro-proxy.eu.tieto.com"
out_proxy_port = 8080

class ShakeItProxy:
    def __init__(self, reactor, in_port=8080, out_port=8080, out_host=None):
        in_proxy_port=in_port
        out_proxy_port = out_port
        out_proxy_host = out_host
        if out_port and out_host:
            reactor.listenTCP(in_proxy_port, ShakeProxyFactory(ShakeProxyThroughProxy) )
        
                            

#reactor.listenTCP(8080, ShakeProxyFactory())
#reactor.run()
