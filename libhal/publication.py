import logging

PUBYEAR = 'producedDateY_i'
PUBMONTH = 'producedDateM_i'
HALURL = 'https://hal.archives-ouvertes.fr/'

def getSetFrom(iterable):
    if iterable == None:
        return set()
    return set(iterable)

def getLastNameInitial(fullname):
    words = fullname.split(' ')
    return words[len(words)-1][0]

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


def _isInterX(set1,set2) -> bool:
    """Whether the intersection of set1 and set2 has a cardinality > 1"""
    if len(set1) < 2 or len(set2) < 2:
        return False
    count = 0
    for t in set1:
        if t.upper() in set2:
            count += 1
    return count > 1


MONTH_NAMES = {
    False: ['','January ','February ','March ','April ','May ','June ','July ','August ','September ','October ','November ','December '],
    True : ['','Jan. ','Fev. ','Mar. ','Apr. ','May ','Jun. ','Jul. ','Aug. ','Sep. ','Oct. ','Nov. ','Dec. ']
    }

class Publication:
    """ facade object for the dictionary returned by getpub from Hal"""
    def __init__(self, pubdict):
        self.pub = pubdict
        self.code = 'O'
        self._halId = self.pub.get("halId_s")
        self._teams = getSetFrom(self.pub.get("rteamStructAcronym_s"))
        self._depts = getSetFrom(self.pub.get("deptStructAcronym_s"))
        self._labs = getSetFrom(self.pub.get("labStructAcronym_s"))
        self._countries = getSetFrom(self.pub.get("instStructCountry_s"))
        # produced = self.pub.get("producedDateY_i")
        # if produced is not None and produced != self.getYear():
        #     logging.warning('Publication '+self._halId+' produced='+str(produced)+', published='+str(self.getYear()))

    def getYear(self):
        return self.pub.get(PUBYEAR)

    def getMonth(self):
        return self.pub.get(PUBMONTH,0)

    def getHalId(self):
        return self._halId

    def getCitationKey(self,keyStyle):
        if keyStyle == 'HCERES':
            return self.getHCERESkey()
        if keyStyle == 'HAL':
            return self.getHalId()
        return ''
       
    def getHCERESkey(self):
        initials = ''
        for a in self.getAuthors()[:3]:  # take only first 3 ones
            initials += getLastNameInitial(a)
        return '['+self._getDeptCodes(2)+'-'+self.code+'-'+str(self.getYear())+'-'+str(self.getMonth())+'-'+initials+'] '

    def getTeams(self):
        return self._teams

    def isIntraTeam(self):
        return len(self.getTeams()) == 1

    def isInterTeams(self,teams) -> bool:
        """Whether this publication involves at least 2 of the teams from teams"""
        return _isInterX(self._teams,teams)

    def getDepts(self):
        return self._depts

    def isIntraDept(self):
        return len(self.getDetps()) == 1

    def isInterDepts(self,depts) -> bool:
        """Whether this publication involves at least 2 of the depts from depts"""
        return _isInterX(self._depts,depts)

    def _getDeptCodes(self,size: int)->str:
        """return a String made of the 'size' last characters of each dept"""
        result = ''
        for d in self._depts:
            last = len(d)-size
            result += d[last:]
        return result

    def getLabs(self):
        return self._labs

    def getAuthors(self):
        return self.pub.get("authFullName_s")

    def getTitle(self):
        return self.pub.get("title_s")[0]
    
    def getCountries(self):
        return self._countries
    
    def getPublishers(self):
        p = self.pub.get("publisher_s")
        if p == None:
            return ''
        return ' & '.join(p)
    

    def getVenue(self):
        if self.isJournal() or self.isOutreach():
            return self.pub.get("journalTitle_s")
        if self.isConference():
            return self.pub.get("conferenceTitle_s")
        if self.isBookChapter():
            return self.pub.get("bookTitle_s")
        return ""
        
    def isInternationalAudience(self):
        return self.pub.get("audience_s") == "2"
    
    def isInternationalCollaboration(self):
        return len(self._countries)>1
    
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
    
    def isConference(self,internationalOnly=False):
        return self.pub.get("docType_s") == "COMM" and self.isPeerReviewing() and (self.isInternationalAudience() or not internationalOnly)
    
    def isBookChapter(self):
        return False

    def isBook(self):
        return False
    
    def isThesis(self):
        return False

    def isEditedBook(self):
        return False
    
    def getFormatedAuthors(self, terse=False, maxTerseNumber=6):
        authors = self.getAuthors()
        count = len(authors)
        if count <= 0:
            return ""
        if terse:
            count = min(count, maxTerseNumber)
            result = getAbbrevAuthorName(authors[0])
            for n in range(1,count):
                result += ', '
                result += getAbbrevAuthorName(authors[n])
            if count < len(authors):
                result += ' et al'
            return result+'. '
        else:
            result = authors[0]
            for n in range(1,count):
                result += ', ' if n < count-1 else ' and '
                result += authors[n]
            return result+'. '

    def __iter__(self):
        yield self.getHalId()+':'
        yield self.getFormatedAuthors(True)
        yield self.getTitle()+','
        v = self.getVenue()
        if v != None and v != '':
            yield v+','
        yield str(self.getYear())+'.'
         
    def asString(self):
        return ' '.join(self)
#         result = "--------\n"
#         for a in self.pub:
#             result = result+a+"="+str(self.pub.get(a))+'\n'
#         return result

    def write(self,writer,citationStyle=None,**kwargs):
        """ use writer to output this publication in biblio form.
        If citationStyle is not known it is interpreted as a function of this instance, e.g. pub.getHalId"""
        if citationStyle is not None:
            writer.append(self.getCitationKey(citationStyle),key=True)
        terse = kwargs.get('terse',False)
        writer.append(self.getFormatedAuthors(terse),authors=True)
        writer.append(self.getTitle(),title=True)
        self._writeSpecifics(writer,terse) # specifics are dealt with in subclassses
        p = self.getPublishers()
        if p != '':
            writer.append(p+', ')    
        writer.append(MONTH_NAMES[terse][self.getMonth()]+str(self.getYear())+'. ')
        writer.append(self.getHalId(), href=HALURL+self.getHalId())

    def _writeSpecifics(self,writer,terse=False):
        pass


    def printAsJson(self, wfile):
        print(self.pub.encode("utf-8"), wfile)
 
class PubWithVenue(Publication):
    def __init__(self, pubdict):
        super().__init__(pubdict)
    def _writeSpecifics(self,writer,terse=False):
        writer.append(self.getVenue()+', ',venue=True)
 
class Article(PubWithVenue):
    def __init__(self, pubdict):
        super().__init__(pubdict)
        self.code = 'J'


class Communication(PubWithVenue):
    def __init__(self, pubdict):
        super().__init__(pubdict)
        self.code = 'I'

class Book(Publication):
    def __init__(self, pubdict):
        super().__init__(pubdict)
        self.code = 'B'
    def isBook(self):
        return True
    
class BookChapter(PubWithVenue):
    def __init__(self, pubdict):
        super().__init__(pubdict)
        self.code = 'C'
    def isBookChapter(self):
        return True

class EditedBook(Publication):
    def __init__(self, pubdict):
        super().__init__(pubdict)
        self.code = 'E'
    def isEditedBook(self):
        return True
        
class Thesis(Publication):
    def __init__(self, pubdict):
        super().__init__(pubdict)
        self.code = 'T'
    def isThesis(self):
        return True


publicationTypes = {
    "ART":Article,
    "COMM":Communication,
    "OUV":Book,
    "COUV":BookChapter,
    "DOUV":EditedBook,
    "THESE":Thesis,
    "OTHER":Publication
    }     

def getPublicationFrom(dict):
    '''factory method to create a publication with the relevant subtype according to field "docType_s" in dict'''
    type = dict.get("docType_s","OTHER")
    constructor = publicationTypes.get(type,Publication)
    return constructor(dict)
