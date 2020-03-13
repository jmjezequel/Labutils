import json
import requests
import logging
import sys
import datetime
import os
import re
import time
import codecs
from pathlib import Path
import tempfile
from libhal.publication import Publication,getPublicationFrom

fields = "halId_s,instStructCountry_s,docType_s,invitedCommunication_s,peerReviewing_s,conferenceTitle_s,journalTitle_s,bookTitle_s,audience_s,authFullName_s,title_s,producedDateY_i,producedDateM_i,publisher_s,rteamStructAcronym_s,deptStructAcronym_s,labStructAcronym_s"
# label_bibtex yields a full bibtex ref
# change producedDateY_i by publicationDateY_i and publicationDateM_i
# country_s yields the country where the pub took place


    
class PubSet:
    """stores a set of publications indexed by their HalId"""
    def __init__(self):
        self.pubs = dict() # where the key is the HalId

    def __iter__(self): self.pubs.__iter__()

    def addPub(self, pub: Publication):
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

    def writePubList(self,writer,condition):
        for pub in filter(condition,self.pubs.values()):
            writer.writeln(pub)

    def asString(self, condition, startingNumber=1):
        '''Deprecated'''
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
    """stores PubSets indexed per year for a Structure of name "name\""""
    def __init__(self, name):
        self.name = name
        self.slices = dict() # dict(date, PubSet)

    def addPub(self, pub: Publication):
        date = pub.getYear()
        slice = self.slices.get(date)
        if (slice == None):
            slice = PubSet()
            self.slices[date] = slice
        # loggin.info("===> adding ",pub.getHalId()," (",date,") publication into ",self.name)
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
        """ returns how many publications do match defaultPubFilter for the date"""
        return self.getPubs(date).getNumberFor(pubFilter)
 
    def getTotalScore(self, pubFilter):
        """ returns how many publications do match defaultPubFilter forall considered date"""
        result = 0
        for date in self.slices.keys():
            result = result + self.getScoreFor(date, pubFilter)
        return result
 
    def merge(self, other: 'PubRecord'):
        for date in other.slices.keys():
            pubs = self.getPubs(date)
            if not date in self.slices:
                self.slices[date] = pubs
            pubs.merge(other.getPubs(date))

    def writePubList(self, writer, condition):
        for k in sorted(self.slices.keys()):
            self.slices[k].writePubList(writer, condition)

    def asString(self, filter, startingNumber=1):
        '''Deprecated'''
        # result = "### "+self.name+'\n'
        result = ""
        count = startingNumber
        for k in sorted(self.slices.keys()):
            bloc, count = self.slices[k].asString(filter,count)
            result = result+bloc
        return (result, count)
    
def alwaysTrue(* args):
    return True

def filterByVenue(pub,kind,venue):
    if kind=='journal' and pub.isJournal():
        return isVenueNameMatch(pub.getVenue(),venue)
    if kind=='conference' and pub.isConference():
        return isVenueNameMatch(pub.getVenue(),venue)
    return False

def filterPubByVenues(pub, journals, conferences):
        if pub.isJournal() and isVenueNameMatchIn(pub.getVenue(), journals):
            return True
        if pub.isConference() and isVenueNameMatchIn(pub.getVenue(), conferences):
            return True
        return False

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


class ProgressionReporter:
    """To be subclassed if use of a GUI to show progress bar"""
    def initialize(self,size):
        pass
    def step(self):
        return True
    def terminate(self):
        pass
    def message(self,* args):
        logging.info(* args)


class StructPubRecords:
    """store PubRecords for a set of structs over a period"""
    def __init__(self, structList, startYear, endYear):
#    result.readByVenues(collection,"conferenceTitle",conferences)):
        self.startYear = startYear
        self.endYear = endYear
        self.structs = dict()  # of (structName, PubRecord)
        for t in structList:
            if t != '':
                self.structs[t] = PubRecord(t)
        self.consolidated = PubRecord("Total") # stores the consolidated total
        
    def getStructureNumber(self):
        return len(self.structs)

    def addPublicationByVenue(self, pub):
        ''' Deprecated '''
        readteams = pub.getTeams()
        if (len(readteams) == 0):
            logging.warning("no identified team for this publication")
            pub.print(sys.stdout)
            return
        for t in readteams:
            if (t in self.teams):
                self.teams[t].addPub(pub)
                break

#     def readByVenues(self,collection, kind, venues):
#         ''' Deprecated '''
#         loggin.info("###Doing: ",venues)
#         dateRange = "["+str(self.startYear)+" TO "+str(self.endYear)+"]"
#         for pubs in getPubByVenues(collection,kind,venues,dateRange):
#             for p in pubs:
#                 self.addPublicationByVenue(getPublicationFrom(p))

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
                    logging.info("Aborting readByStructures")
                    return
                progresscallback.message(t+" publications for "+str(year)+": got "+str(len(structPubs)))
                
                self.addPublicationByStructure(self.structs[t],structPubs)
            self.consolidated.merge(self.structs[t])
        progresscallback.terminate()

    def abortRequest(self):
        pass

    def addPublicationByStructure(self, struct, halpublist):
        for pub in halpublist:
            struct.addPub(getPublicationFrom(pub)) 

    def getPubRecord(self,struct=None):
        if struct is None:
            return self.consolidated
        return self.structs[struct]
    
    def getStructScore(self, struct, date, condition):
        """ returns struct's number of publications matching filter for date"""
        return self.structs[struct].getScoreFor(date,condition)

    def getTotal(self, struct=None, condition=alwaysTrue):
        """ returns total matching filter"""
        return self.getStructTotal(struct,condition)

    def getStructTotal(self, struct,condition):
        """ returns struct's total of publications matching filter"""
        if struct is None:
            return self.getConsolidatedTotal(condition)
        return self.structs[struct].getTotalScore(condition)

    def getConsolidatedScore(self,date,condition):
        """ returns consolidated number of publications matching filter for date"""
        return self.consolidated.getScoreFor(date,condition)

    def getConsolidatedTotal(self,condition):
        """ returns consolidated total number of publications matching filter"""
        return self.consolidated.getTotalScore(condition)

    def yieldDates(self):
        yield "Struct"
        for d in range(self.startYear,self.endYear+1):
            yield str(d)
        yield "Total"

    def yieldScores(self, struct, condition):
        yield struct
        for d in range(self.startYear,self.endYear+1):
            yield str(self.getStructScore(struct, d, condition))
        yield str(self.getStructTotal(struct, condition))

    def yieldConsolidatedScore(self,condition):
        yield "Total"
        for d in range(self.startYear,self.endYear+1):
            yield str(self.getConsolidatedScore(d,condition))
        yield str(self.getConsolidatedTotal(condition))


    def yieldStructureNames(self):
        yield str(self.startYear)+"-"+str(self.endYear)
        for s in self.structs:
            yield s
        
    def writeScorePerYear(self, writer, journals, conferences):
        condition = lambda pub: filterPubByVenues(pub,journals,conferences)
        writer.openSheet("ScorePerYear",'table')
        writer.writeTitle(self.yieldDates())
        for t in self.structs.keys():
            writer.writeln(self.yieldScores(t,condition))
        writer.writeln(self.yieldConsolidatedScore(condition))
        writer.closeSheet()

    def yieldScoreForVenue(self, venueKind, venueName):
        """ yield how many publications by struct do match venueName"""
        yield venueName
        for s in self.structs:
            yield str(self.structs[s].getTotalScore(lambda pub: filterByVenue(pub,venueKind,venueName)))

    def writeBreakdownPerVenue(self, writer, journals, conferences):
        writer.openSheet("BreakdownPerVenue",'table')
        writer.writeTitle(self.yieldStructureNames())
        for venue in journals:
            writer.writeln(self.yieldScoreForVenue('journal',venue))
        for venue in conferences:
            writer.writeln(self.yieldScoreForVenue('conference',venue))
        writer.closeSheet()
              
    def writePubList(self,writer, journals, conferences):
        condition = lambda pub: filterPubByVenues(pub,journals,conferences)
        for pubRecord in self.structs.values():
            writer.openSheet(pubRecord.name)
            pubRecord.writePubList(writer,condition)
            writer.closeSheet()
    
    def save(self, name, writer, journals, conferences, *args): #arg is a function of self
        ''' write results for eg writePubList, writeScorePerVenue, writeScorePerYear'''
        writer.open(name)
        if len(args) == 0: # save all
            args = (self.writePubList,self.writeBreakdownPerVenue,self.writeScorePerYear)
        for f in args:
            f(writer,journals,conferences)
        writer.close()


# return a list of publications, each in the form of a dict
def getPub(collection, dateRange, parameters):
    url = "https://api.archives-ouvertes.fr/search/"
    if collection != None and collection != '':
        url = url + collection+"/"
    url = url+"?"+parameters+"&fq=producedDateY_i:"+str(dateRange)+"&rows=9999&wt=json&fl="+fields
    logging.info(url)
    response = requests.get(url, timeout=20)
    response.raise_for_status()# If the response was successful, no Exception will be raised
    return json.loads(response.text).get("response").get("docs")

# return a list of publications, each in the form of a dict
# implement cache management
def getPubByStructureKind(collection, structkind, structAccronym, startYear, endYear=None):
    date = startYear if endYear is None else "[" + str(startYear) + " TO " + str(endYear) + "]"
    if isInCache(structAccronym,date):
        structPubs = getPubFromCache(structAccronym,date)
        # time.sleep(1)
    else:
        structPubs = getPub(collection, date, "q="+structkind+"_t:"+structAccronym)
        writeHalStructPubs(structAccronym,date,structPubs) # writePubList to cache
    return structPubs

# e.g. collection=IRISA, author=jezequel,jean-marc 
def getPubByAuthor(collection, author, startYear, endYear=None):
    return getPubByStructureKind(collection, "authFullName", author, startYear, endYear)

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
            logging.warning("*** ",p.get(kind+"_s")," does not match: ",venue)

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
#     conferencesOnlyFrom = jsonArgs.get("conferences")
#     journalsOnlyFrom = jsonArgs.get("journals")

    result = StructPubRecords(teams, startYear, endYear)
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
# logfile = open(halcachedir+"/hal.log",'w', encoding='utf-8')
# logger = logging.getLogger(__name__)

# def log(* args):
#     '''print a log both on stdout and on the logfile'''
#     msg = ' '.join(str(x) for x in args)
#     print(msg)
#     print(msg,file=logfile)
    
def clearCache():
    for path in Path(halcachedir).glob('*.json'):
        path.unlink()


def setuplog(logfilename=None):
    if logfilename == None:
        logfilename = halcachedir+"/hal.log"
    logging.root.handlers = []
    logging.basicConfig(
        #level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(logfilename,mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
            ]
        )
    
def main():
    jsonfilename = sys.argv[1]
    dirname = getBaseDir(jsonfilename)

    setuplog()
    f = open(jsonfilename)
    args = json.load(f)
    f.close()

    result = getStructPubRecordsFromJson(args, ProgressionReporter())
    result.save(dirname)

if __name__ == "__main__":
    # execute only if run as a script
    main()

