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
    def openWithHeaders(self, url, headers):
        
        
        self.addheaders = [ ('User-Agent', headers.get('User-Agent')),
                            ('Referer', headers.get('Referer')),
                            ('Accept', headers.get('Accept')),
                            #('Accept-Encoding', headers.get('Accept-Encoding')),
                            ('Accept-Language', headers.get('Accept-Language')),
                            ('Accept-Charset', headers.get('Accept-Charset'))]

       # print self.addheaders
        
        
        return self.open(url)
        
class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
    __opener = CopyOpener()
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        #print self.headers
        dataobj = CopyOpener().openWithHeaders(self.path, self.headers)
       

        #print sfdata.readlines()
        
        if matchSFUrl( self.path ):
            sfdata = cStringIO.StringIO()
            shutil.copyfileobj(dataobj, sfdata)
            
            print "request has arrived " + self.path

            sfdata.seek(0)
            dataobj = sfdata
            
        
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


