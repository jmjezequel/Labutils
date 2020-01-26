import json
import requests
import sys
import datetime
import os
import re
import time
import codecs
from pathlib import Path
import tempfile

fields = "halId_s,docType_s,invitedCommunication_s,peerReviewing_s,conferenceTitle_s,journalTitle_s,bookTitle_s,audience_s,authFullName_s,title_s,producedDateY_i,rteamStructAcronym_s,deptStructAcronym_s,labStructAcronym_s"

def getSetFrom(iterable):
    if iterable == None:
        return set()
    return set(iterable)


def getAbbrevAuthorName(fullname,sep=' '):
    words = fullname.split(sep)
    firstNames = words[0].split('-')
    if len(firstNames)==1: 
        result = firstNames[0][0]
    else:  #deal with composed first names
        result = '.-'.join(w[0] for w in firstNames)
    result += '. '
    n = len(words)
    for i in range(1,n-1): # abbrev. middle names
        if words[i].lower() in ['de','del','le','van','von']:
            result += words[i]+' '
            i += 1
        else:
            result += words[i][0]+'. '
    if n > 1:
        result += words[n-1] # last name if any
    return result        

class Publication:
    ''' facade object for the dictionary returned by getpub from Hal'''
    def __init__(self, pubdict):
        self.pub = pubdict
        self._halId = self.pub.get("halId_s")
        self._teams = getSetFrom(self.pub.get("rteamStructAcronym_s"))
        self._depts = getSetFrom(self.pub.get("deptStructAcronym_s"))
        self._labs = getSetFrom(self.pub.get("labStructAcronym_s"))
        
    def getDate(self):
        return self.pub.get("producedDateY_i")

    def getHalId(self):
        return self._halId

    def getTeams(self):
        return self._teams

    def getDepts(self):
        return self._depts

    def getLabs(self):
        return self._labs

    def getAuthors(self):
        return self.pub.get("authFullName_s")

    def getTitle(self):
        return self.pub.get("title_s")[0]

    def getVenue(self):
        if self.isJournal() or self.isOutreach():
            return self.pub.get("journalTitle_s")
        if self.isConference():
            return self.pub.get("conferenceTitle_s")
        if self.isBookChapter():
            return self.pub.get("bookTitle_s")
        return None
        
    def isInternational(self):
        audience = self.pub.get("audience_s")
        return audience == "2"
    
    def isInvited(self):
        invited = self.pub.get("invitedCommunication_s")
        return invited == '1' 
    
    def isPeerReviewing(self):
        peer = self.pub.get("peerReviewing_s")
        return peer == '1' 
    
    def isJournal(self):
        return self.pub.get("docType_s") == "ART" and self.isPeerReviewing()
    
    def isOutreach(self):
        return self.pub.get("docType_s") == "ART" and not self.isPeerReviewing()
    
    def isConference(self):
        return self.pub.get("docType_s") == "COMM" and self.isPeerReviewing()
    
    def isBookChapter(self):
        return self.pub.get("docType_s") == "COUV"

    def isBook(self):
        return self.pub.get("docType_s") == "OUV"

    def isEditedBook(self):
        return self.pub.get("docType_s") == "DOUV"
    
    def getAbbrevAuthors(self):
        authors = self.getAuthors()
        nb = len(authors)
        if nb==0:
            return ""
#         if nb==1: # only useful when puttin a 'and' before the last author
#             return getAbbrevAuthorName(authors[0])
        return ', '.join(getAbbrevAuthorName(a) for a in authors)
            
    def yieldAsBibRef(self):
        yield self.getAbbrevAuthors()+'. '
        yield self.getTitle()
        v = self.getVenue()
        if v != None:
            yield '. '+v
        yield ', '+str(self.getDate())+'.'
        
    def print(self, wfile):
        print (self.asString().encode('UTF-8'),file=wfile)
        # print("--------", file = wfile)
        # for a in self.pub:
        #     print(a+"="+str(self.pub.get(a)), file = wfile)

 
    def asString(self):
        return ''.join(self.yieldAsBibRef())
#         result = "--------\n"
#         for a in self.pub:
#             result = result+a+"="+str(self.pub.get(a))+'\n'
#         return result

    def printAsJson(self, wfile):
        print(self.pub.encode("utf-8"), wfile)
 
class PubSet:
    '''stores a set of publications indexed by their HalId'''
    def __init__(self):
        self.pubs = dict() # where the key is the HalId

    def addPub(self, pub):
        self.pubs[pub.getHalId()] = pub
           
    def getNumberFor(self, pubFilter):
        result = 0
        for k in self.pubs:
            if pubFilter(self.pubs[k]):
                result += 1
        return result

    def getNumber(self):
        return len(self.pubs)

    def merge(self, otherPubSet):
        self.pubs.update(otherPubSet.pubs)

#    def print(self, wfile):
#        print (self.asString(),file=wfile)
        # print("--------", file = wfile)
        # print(self.date, file = wfile)
        # for k in self.pubs:
        #     self.pubs[k].print(wfile)

    def asString(self, condition, startingNumber=1):
#        result = "--------\n" # + str(self.date)+'\n'
        result = ""
        count = startingNumber
        for pub in filter(condition,self.pubs.values()):
            if count>0:
                result = result+'['+str(count)+'] '
                count += 1
            result = result+pub.asString()+'\n'
        return (result, count)

class PubRecord:
    '''stores PubSets indexed per year for a Structure of name "name"'''
    def __init__(self, name):
        self.name = name
        self.slices = dict() # dict(date, PubSet)

    def addPub(self, pub):
        date = pub.getDate()
        slice = self.slices.get(date)
        if (slice == None):
            slice = PubSet()
            self.slices[date] = slice
        # log("===> adding ",pub.getHalId()," (",date,") publication into ",self.name)
        slice.addPub(pub)

    def getName(self):
        return self.name
        
    def getDateStart(self):
        return self.slices.keys()[0]

    def getDateEnd(self):
        last = len(self.slices)-1
        return self.slices.keys()[last]

    def getPubs(self, date):
        return self.slices.get(date, PubSet()) #if not exist yet, return  new one

    def getScoreFor(self, date, pubFilter):
        ''' returns how many publications do match defaultPubFilter for the date'''
        return self.getPubs(date).getNumberFor(pubFilter)
 
    def getTotalScore(self, pubFilter):
        ''' returns how many publications do match defaultPubFilter forall considered date'''
        result = 0
        for date in self.slices.keys():
            result = result + self.getScoreFor(date, pubFilter)
        return result
 
    def merge(self, otherPubRecord):
        for date in otherPubRecord.slices.keys():
            pubs = self.getPubs(date)
            if not date in self.slices:
                self.slices[date] = pubs
            pubs.merge(otherPubRecord.getPubs(date))

    def asString(self, filter, startingNumber=1):
        # result = "### "+self.name+'\n'
        result = ""
        count = startingNumber
        for k in sorted(self.slices.keys()):
            bloc, count = self.slices[k].asString(filter,count)
            result = result+bloc
        return (result, count)
    
def filterTrue(pub):
    return True

def filterByVenue(pub,venue):
    return isVenueNameMatch(pub.getVenue(),venue)

def filterPubByVenues(pub, journals, conferences):
        if pub.isJournal() and isVenueNameMatchIn(pub.getVenue(), journals):
            return True
        if pub.isConference() and isVenueNameMatchIn(pub.getVenue(), conferences):
            return True
        return False

class ProgressionReporter:
    '''To be subclassed if use of a GUI to show progress bar'''
    def initialize(self,size):
        pass
    def step(self):
        return True
    def terminate(self):
        pass
    def message(self,txt):
        log(txt)

class StructPubRecords:
    '''store PubRecords for a set of structs over a period, with optional defaultPubFilter'''
    def __init__(self, structList, startYear, endYear, pubFilter=filterTrue):
        self.startYear = startYear
        self.endYear = endYear
        self.structs = dict() # of (structName, PubRecord)
        for t in structList:
            if t != '':
                self.structs[t] = PubRecord(t)
        self.consolidated = PubRecord("Total") # stores the consolidated consolidated
        self.defaultPubFilter = pubFilter
        
    def getStructureNumber(self):
        return len(self.structs)

    def addPublicationByVenue(self, pub):
        ''' Deprecated '''
        readteams = pub.getTeams()
        if (len(readteams) == 0):
            log("***WARNING: no identified team for this publication")
            pub.print(sys.stdout)
            return
        for t in readteams:
            if (t in self.teams):
                self.teams[t].addPub(pub)
                break

    def readByVenues(self,collection, kind, venues):
        ''' Deprecated '''
        log("###Doing: ",venues)
        dateRange = "["+str(self.startYear)+" TO "+str(self.endYear)+"]"
        for pubs in getPubByVenues(collection,kind,venues,dateRange):
            for p in pubs:
                self.addPublicationByVenue(Publication(p))

    def readByStructures(self, collection, structureKind, progresscallback=ProgressionReporter()):
        # dateRange = "["+str(self.startYear)+" TO "+str(self.endYear)+"]"
        # now one request by year to allow simpler cache management
        nbreq = len(self.structs)*(self.endYear-self.startYear+1)
        progresscallback.initialize(nbreq)
        for t in self.structs.keys():
            for year in range(self.startYear,self.endYear+1):
                structPubs = getPubByStructureKind(collection,structureKind,t,year)
                if not progresscallback.step():
                    # computation should stop here
                    log("Aborting readByStructures")
                    return
                progresscallback.message(t+" publications for "+str(year)+": got "+str(len(structPubs)))
                
                self.addPublicationByStructure(self.structs[t],structPubs)
            self.consolidated.merge(self.structs[t])
        progresscallback.terminate()

    def abortRequest(self):
        pass

    def addPublicationByStructure(self, struct, halpublist):
        for pub in halpublist:
            struct.addPub(Publication(pub)) 

    def getStructScore(self, struct, date,filter=None):
        ''' returns struct's number of publications matching filter for date'''
        return self.structs[struct].getScoreFor(date,filter if filter != None else self.defaultPubFilter)

    def getTotal(self, struct=None, filter=filterTrue):
        ''' returns total matching filter'''
        if struct==None:
            return self.getConsolidatedTotal(filter)
        return self.getStructTotal(struct,filter)

    def getStructTotal(self, struct,filter=None):
        ''' returns struct's total of publications matching filter'''
        return self.structs[struct].getTotalScore(filter if filter != None else self.defaultPubFilter)

    def getConsolidatedScore(self,date,filter=None):
       ''' returns consolidated number of publications matching filter for date'''
       return self.consolidated.getScoreFor(date,filter if filter != None else self.defaultPubFilter)

    def getConsolidatedTotal(self,filter=None):
        ''' returns consolidated total number of publications matching filter'''
        return self.consolidated.getTotalScore(filter if filter != None else self.defaultPubFilter)

    def yieldDates(self):
        yield "Struct"
        for d in range(self.startYear,self.endYear+1):
            yield str(d)
        yield "Total"

    def yieldScores(self, struct):
        yield struct
        for d in range(self.startYear,self.endYear+1):
            yield str(self.getStructScore(struct, d))
        yield str(self.getStructTotal(struct))

    def yieldConsolidatedScore(self):
        yield "Total"
        for d in range(self.startYear,self.endYear+1):
            yield str(self.getConsolidatedScore(d))
        yield str(self.getConsolidatedTotal())


    def yieldStructureNames(self):
        yield str(self.startYear)+"-"+str(self.endYear)
        for s in self.structs:
            yield s
        
    def yieldScoreForVenue(self, venueName):
        ''' yield how many publications by struct do match venueName'''
        yield venueName
        for s in self.structs:
            yield str(self.structs[s].getTotalScore(lambda pub: filterByVenue(pub,venueName)))


    def printAsCSV(self,wfile):
#         print (*(l for l in self.yieldDates()),sep=';',file=wfile)
#         for t in self.structs.keys():
#             print (*(n for n in self.yieldScores(t)),sep=';',file=wfile)
#        print (*(n for n in self.yieldConsolidatedScore()),sep=';',file=wfile)
        for l in self.getAsTabularData(';'):
            print(l,file=wfile)
      
    def getAsTabularData(self, sep='\t'):
        yield sep.join(self.yieldDates())
        for t in self.structs.keys():
            yield sep.join(self.yieldScores(t))
        yield sep.join(self.yieldConsolidatedScore())
              
    def printAsTxt(self, wfile):
        for l, count in self.getAsTxt():
            print(l,wfile)
      
    def getAsTxt(self, filter=None):
        if filter==None:
            filter = self.defaultPubFilter
        for t in self.structs.keys():
            yield self.structs[t].asString(filter)
      
    def save(self,basedir):
        os.makedirs(basedir, exist_ok=True)
        scorefilename = basedir+"/score.csv"
#        bdfilename = basedir+"/breakdown.csv"
        txtfilename = basedir+"/publications.txt"
        self.printAsCSV(open(scorefilename, 'w+'))
#        self.printScorePerVenueAsCSV(open(bdfilename, 'w+'), journals, conferences)
        self.printAsTxt(open(txtfilename, 'w+', encoding='utf-8'))

    def yieldScorePerVenue(self,journals,conferences,sep='\t'):
        yield sep.join(self.yieldStructureNames())
        for v in journals:
            yield sep.join(self.yieldScoreForVenue(v))
        for v in conferences:
            yield sep.join(self.yieldScoreForVenue(v))
      

    def printScorePerVenueAsCSV(self,wfile,journals,conferences):
#         print (*(n for n in self.yieldStructureNames()),sep=';',file=wfile)
#         for v in journals:
#             print (*(n for n in self.yieldScorePerVenue(v)),sep=';',file=wfile)
#         for v in conferences:
#             print (*(n for n in self.yieldScorePerVenue(v)),sep=';',file=wfile)
        for l in self.yieldScorePerVenue(journals,conferences,';'):
            print(l,file=wfile)
     



# return a list of publications, each in the form of a dict
def getPub(collection, dateRange, parameters):
    url = "https://api.archives-ouvertes.fr/search/"
    if collection != None and collection != '':
        url = url + collection+"/"
    url = url+"?"+parameters+"&fq=producedDateY_i:"+str(dateRange)+"&rows=9999&wt=json&fl="+fields
    log(url)
    response = requests.get(url, timeout=20)
    response.raise_for_status()# If the response was successful, no Exception will be raised
    return json.loads(response.text).get("response").get("docs")

# return a list of publications, each in the form of a dict
# implement cache management
def getPubByStructureKind(collection, structkind, structAccronym, date):
    if isInCache(structAccronym,date):
        structPubs = getPubFromCache(structAccronym,date)
        # time.sleep(1)
    else:
        structPubs = getPub(collection, date, "q="+structkind+"_t:"+structAccronym)
        writeHalStructPubs(structAccronym,date,structPubs) # write to cache
    return structPubs

# e.g. collection=IRISA, author=jezequel,jean-marc 
def getPubByAuthor(collection, author, date):
    return getPubByStructureKind(collection, "authFullName", author, date)

# e.g. collection=IRISA, teamName=diverse date="2012 TO 2019"
def getPubByTeam(collection, teamName, date):
    return getPubByStructureKind(collection, "rteamStructAcronym", teamName, date)

# e.g. collection=IRISA, teamName=diverse date="2012 TO 2019"
# Deprecated
def getPubByDept(collection, deptName, date):
    return getPubByStructureKind(collection, "deptStructAcronym", deptName, date)

# e.g. collection=IRISA, teamName=diverse date="2012 TO 2019"
def getPubByLab(labName, date):
    return getPubByStructureKind(None, "labStructAcronym", labName, date)

# e.g. collection=IRISA, kind=conferenceTitle|journalTitle venue=POPL 
# Deprecated
def getPubByVenue(collection, kind, venue, date):
    result = getPub(collection, date, "q="+kind+"_t:"+venue)
    # need to filter result because HAL is sloppy on the matching
    for p in result:
       if isVenueNameMatch(p.get(kind+"_s"),venue):
            yield p
       else:
            log("*** ",p.get(kind+"_s")," does not match: ",venue)

def writeHalStructPubs(structName, year, halStructPubs):
   with open(getCachedFilename(structName,year), 'w') as outfile:  
      json.dump(halStructPubs, outfile, sort_keys=True, indent=4)

def getPubFromCache(structName, year):
    with open(getCachedFilename(structName,year), 'r') as infile:
        return json.load(infile)

def getCachedFilename(structName, year):
    return halcachedir+"/"+re.sub('\W+','', structName)+"-"+str(year)+".json"

def isInCache(structName, year):
    return os.path.exists(getCachedFilename(structName,year))

def isVenueNameMatchIn(read,venueList):
    if read == None:
        return False
    for venue in venueList:
        if isVenueNameMatch(read,venue):
            return True
    return False

def isVenueNameMatch(read,wanted):
    if read == None:
        return False
    if wanted == '*':
        return True
    r = read.replace("Int.", "International").replace("Conf.", "Conference").replace("Trans.", "Transactions").replace("&","and").replace(",","").casefold()
    w = wanted.replace("&","and").casefold()
    return r.find(w) >=0

def getPubByVenues(collection, kind, venues, date):
    for v in venues:
        # print("###Doing: "+v)
        yield getPubByVenue(collection, kind, v, date)

def getStructPubRecordsFromJson(jsonArgs, progresscallback):
    startYear = jsonArgs.get("startYear", 1900)
    endYear = jsonArgs.get("endYear", datetime.datetime.today().year)
    collection = jsonArgs.get("collection",'')
    structureKind = jsonArgs.get("structureKind","rteamStructAcronym")
    teams = jsonArgs.get("teams")
    conferences = jsonArgs.get("conferences",[])
    journals = jsonArgs.get("journals",[])

    result = StructPubRecords(teams, startYear, endYear, lambda pub: filterPubByVenues(pub, journals, conferences))
#    result.readByVenues(collection,"conferenceTitle",conferences)
#    result.readByVenues(collection,"journalTitle",journals)
    result.readByStructures(collection,structureKind,progresscallback)
    return result



#result = StructPubRecords(['CAIRN', 'CELTIQUE', 'CIDRE', 'EMSEC', 'DiverSe', 'TAMIS'], 2016, 2019)

#result.readByVenues("IRISA","conferenceTitle",AStarSecurityConfs+ASecurityConfs)
#result.readByVenues("IRISA","journalTitle",ASecurityJournals)

#   for pubs in getPubByVenues("IRISA","conferenceTitle",AStarSecurityConfs,date):

def getBaseDir(filename):
    return filename.split('.')[0]

halcachedir = tempfile.gettempdir()+'/halcache'
os.makedirs(halcachedir, exist_ok=True)
logfile = open(halcachedir+"/hal.log",'w+', encoding='utf-8')

def log(* args):
    '''print a log both on stdout and on the logfile'''
    msg = ''.join(str(x) for x in args)
    print(msg)
    print(msg,file=logfile)
    
def clearCache():
    for path in Path(halcachedir).glob('*.json'):
        path.unlink()



def main():
    jsonfilename = sys.argv[1]
    dirname = getBaseDir(jsonfilename)

    f = open(jsonfilename)
    args = json.load(f)
    f.close()

    result = getStructPubRecordsFromJson(args, ProgressionReporter())
    result.save(dirname)

if __name__ == "__main__":
    # execute only if run as a script
    main()

