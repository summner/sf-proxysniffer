#!/usr/bin/env python2.7

import twisted_proxy
from twisted_proxy import ShakeItProxy, ShakeHandler
from twisted.internet import reactor


class TestHandler( ShakeHandler ):
    def handleResponsePart(self, buffer):
        print buffer
    def handleHeader(self, key, value):
        print key, value
        



pat = "http://s[0-9]\.sfgame\.pl/request.*"
twisted_proxy.install_shake_handler(pat, TestHandler)




ShakeItProxy(reactor, 8080, 8080, "wro-proxy.eu.tieto.com")
reactor.run()


