import re
sfURIre = re.compile(u".*req=(?P<hash>.{32})(?P<id>.+?)\&.*rnd=(?P<rnd>[0-9]+).*")
sfgamePat = re.compile("http://s[0-9]\.sfgame\.pl/request.*")


class SFParseException(Exception):
    def __init__(self, uri, other_info=""):
        self.uri=uri
        self.other_info= other_info
    def __str__(self):
        return repr("URL: %s \nOther: %s " % (self.uri, self.other_info))

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

class
