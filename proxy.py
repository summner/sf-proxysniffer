#!/usr/bin/python
import SocketServer
import SimpleHTTPServer
import urllib
import re
import sys
import shutil
import cStringIO

PORT = 8080

def matchSFUrl( path ):
    match = re.compile("http://s[0-9]\.sfgame\.pl/.*").match(path)
    if not match:
        return False
    else:
        return True


class CopyOpener( urllib.FancyURLopener ):
    __conditional_list = [ 'User-Agent', 'Referer', 'Accept', 'Accept-Language',
                           'Accept-Charset', 'Etag'
        #                   'Keep-Alive',
          #                 'Proxy-Connection',
                           #'Cache-Control',
                           'Cookie' ]
    def conditionalCopyHeaders(self, headers):
        self.addheaders = []
        for pos in self.__conditional_list:
            val = headers.get(pos)
            if val:
                self.addheaders.append((pos, val))
        print self.addheaders
        
    def openWithHeaders(self, url, headers):
        self.conditionalCopyHeaders(headers)
##        
##        self.addheaders = [ ('User-Agent', headers.get('User-Agent')),
##                            ('Referer', headers.get('Referer')),
##                            ('Accept', headers.get('Accept')),
##                           # ('Accept-Encoding', headers.get('Accept-Encoding')),
##                            ('Accept-Language', headers.get('Accept-Language')),
##                            ('Accept-Charset', headers.get('Accept-Charset')),
##                            ('Keep-Alive: 115', headers.get('Keep-Alive'))]
##        cookie = headers.get('Cookie')
##        if cookie and False:
##            self.addheaders.append(('Cookie', cookie))
        
       # print self.addheaders
        #print "Url:",url
        
        return self.open(url)
        
class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
    __opener = CopyOpener()
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        #print self.headers
        dataobj = CopyOpener().openWithHeaders(self.path, self.headers)
        print self.path
        print self.headers
        #print sfdata.readlines()
        
        if matchSFUrl( self.path )  and False :
            sfdata = cStringIO.StringIO()
            shutil.copyfileobj(dataobj, sfdata)
            
            print "request has arrived " + self.path
            print sfdata.getvalue()
            sfdata.seek(0)
            dataobj = sfdata
            dataobj.seek(0)
            
        
        self.copyfile(dataobj, self.wfile)
        
    def log_message(self, format, *args):
        pass #got to hell message :]
class MyServer( SocketServer.ThreadingTCPServer ):
    allow_reuse_address=True
httpd = MyServer(('', PORT), Proxy)


print "serving at port", PORT
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print "Bye"
    httpd.shutdown()
    sys.exit(0)


