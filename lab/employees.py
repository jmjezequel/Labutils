from datetime import datetime, timedelta
import math
import re
import unicodedata
import logging
from dataclasses import dataclass
from typing import Dict, List
from libhal import hal


def alwaysTrue(* args):
    return True   

def dt(year):
    """return a datetime starting that year"""
    return datetime(year,1,1)

def getFullName(* args):
    """ concatenate args, eg firstName, lastName into "firstName lastName\""""
    return ' '.join(str(arg) for arg in args)

CT='CT'                 #  Contrat à durée déterminée (catégorie non précisée)
CDI='CDI'
DOCTORANT='DOCTORANT'
STAGIAIRE='STAGIAIRE'
POSTDOC='POST-DOC'      #Ch_aut    Post-doctorant
CHCONTRACTUEL='Ch_contractuel'  #    Ch_aut    Chercheur contractuel
CHINVITE='CH_INVITÉ'    #Ch_aut    Visiteur étranger : professeur invité et chercheur associé, ayant séjourné au moins 1 mois au sein de l'unité
CHASSOCIE='CH_ASSOCIÉ'  #Ch_aut    Chercheur associé
ECC='ECC'               #EC_aut    Enseignant-chercheur contractuel (dont contrats LRU)

@dataclass
class Diploma:
    """represent a diploma of type grade, from place, obtained at date date"""
    grade: str
    date: datetime
    place: str = ''


class Status():
    def __init__(self, team: str, d: str, category: str, bap:str):
        self.team = team
        self.dept = d
        self.bap = bap
        self.category = category

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    def isAmong(self, *categories):
        return self.category in categories

    def isITA(self):
        return False

    def isEmeritus(self):
        return False

    def isPhD(self):
        return self.category == DOCTORANT

    def isCDDIT(self):
        return self.category == CT

    def get(self, key):
        result = getattr(self, key, '')
        return result if result != None else ''

    def getForContractDate(self, key, date=None):
        ''' return value of key for date, or '' if does not exist for this date'''
        return self._getForDate(key, self.startContract, self.endContract, date)

    def getForStructDate(self, key, date=None):
        ''' return value of key for date, or '' if does not exist for this date'''
        return self._getForDate(key, self.startStructure, self.endStructure, date)

    def _getForDate(self, key, startDate, endDate, date):
        ''' return value of key for date, or '' if does not exist for this date'''
        result = self.get(key)
        if date == None or date >= startDate and date <= endDate:
            return result
        return ''

    def getDuration(self):
        ''' return a datetime.timedelta object storing the duration in this status'''
        return self.endContract - self.startContract


class Person:
    # firstName: str
    # lastName: str
    # gender: str
    # birthdate: datetime
    # citizenship: str
    # career: List[Status] = []  # successive (or simultaneous) status/roles played by this person in the lab
    # diplomas: Dict[str, Diploma] = dict()  # dict of <str,Diploma>, key is diploma level eg PhD
    # lab = None

    def __init__(self, firstName, lastName, birthdate, gender, citizenship):
        self.firstName = firstName
        self.lastName = lastName
        self.birthdate = birthdate
        self.gender = gender
        self.citizenship = citizenship
        self.career: List[Status] = []  # successive (or simultaneous) status/roles played by this person in the lab
        self.diplomas: Dict[str, Diploma] = dict()  # dict of <str,Diploma>, key is diploma level eg PhD
        self.lab = None

    def isFemale(self):
        return self.gender == 'F'
    
    def isMale(self):
        return self.gender == 'M'
    
    def getName(self):
        return getFullName(self.firstName,self.lastName)

    def getRawPubList(self, startYear: int, endYear: int):
        """return the list of raw publications for the period, under the form of a list of dict"""
        return hal.getPubByAuthor(None, '"' + self.getName() + '"', startYear, endYear)

    def getPhDRawPubList(self):
        """return the list of raw publications for the period, under the form of a list of dict"""
        start = self.get('debutThese')
        if start == "":
            logging.error(self.getName()+ " has no PhD starting date (needed in Employee.getPhDRawPubList)")
            return []
        startYear = start.year
        return self.getRawPubList(startYear,startYear+4)

    def hasStatus(self, status, first, last=None):
        ''' return whether this person has has this status (as a function) at some point over the period first...last'''
        if last == None:
            last = first
        for s in self.career:
            if status(s) and s.endContract>=first and s.startContract<=last:
                return True
        return False

    def hasBeen(self, first, last, * status):
        ''' return whether this person has had one these status at some point over the period first...last'''
        if last is None:
            last = first
        for s in self.career:
            if s.isAmong(* status) and s.endContract>=first and s.startContract<=last:
                return True
        return False

    def get(self, key, date=None, statusCondition=alwaysTrue):
        ''' return first valid value of key at date date respecting statusCondition. 
        career are stored in reverse order of endStructure (see cleanUp) so most recent is first here
        if date==None, does not care of dates
        if not, search based on strutureDates'''
        for a in filter(statusCondition,self.career):
            v = a.getForStructDate(key,date)
            if v != '':
                return v
        return ''

    def getLongest(self, key):
        ''' return longest valid value of key'''
        longest = timedelta(days=0)
        result = ""
        for a in self.career:
            if a.getDuration() > longest:
                v = a.get(key)
                if v != '':
                    result = v
                    longest = a.getDuration()
        return result

    def getStartDate(self):
        result = datetime.today()
        for a in self.career:
            if a.startContract < result:
                result = a.startContract
        return result

    def getEndDate(self):
        result = dt(1)
        for a in self.career:
            if a.endContract > result:
                result = a.endContract
        return result
    
    def getStayDuration(self):
        ''' return a datetime.timedelta object storing the duration of the stay in the lab'''
        return self.getEndDate() - self.getStartDate()

    def isShortTermVisitor(self, nbdays):
        ''' return whether this person stayed less than nbdays days in the lab'''
        return self.getStayDuration() < timedelta(days=nbdays)

    def getMasterIntitution(self):
        master = self.diplomas.get('Master')
        return master.place if master is not None else ""
    
    def isMember(self, first, last, struct=None):
        ''' whether this person was in struct: SubStructure (or in None, the lab) at some point over the period first...last'''
        for a in self.career:
            within = a.endStructure>=first and a.startStructure<=last
            if within and (struct is None or a.getForStructDate('dept') == struct.halId):
                return True 
        return False

    
    def isPersonnel4HCERES(self, first, last):
        ''' whether this person should be listed in "3.1 Liste des personnels" for the HCERES report for the period firstYear...lastYear'''
        return self.isMember(first, last) and not (self.isShortTermVisitor(124) or self.isPhDStudent(first, last))
#         for a in self.career:
#             if not a.isAmong(DOCTORANT) and a.endContract>=first and a.startContract<=last and a.endContract-a.startContract>datetime.timedelta(124):
#                 return True
#         return False
     
    def isEmployeeOf(self, first, last, * employers):
        ''' return whether this person has been hired by employer at some point over the period first...last'''
        return self.hasStatus(lambda s: s.get('employer') in employers, first, last)
    
    def isVisitingScientist(self, first, last=None):
        ''' return whether this person has been a Visiting Scientits at some point over the period first...last'''
        return self.hasBeen(first, last, CHINVITE)
    
    def isIntern(self, first, last=None):
        ''' return whether this person has been an Intern at some point over the period first...last'''
        return self.hasBeen(first, last, STAGIAIRE)
    
    def isEmeritus(self, first, last=None):
        """ return whether this person has been an Intern at some point over the period first...last"""
        return self.hasBeen(first, last, 'PREM', 'DREM')
    
    def isPhDStudent(self, first, last=None):
        """ return whether this person has been a PhD student at some point over the period first...last"""
        return self.hasBeen(first, last, DOCTORANT)

    def gotPhDduring(self, first, last=None):
        """ return whether this person has defended a PhD at some point over the period first...last"""
        phd = self.diplomas.get('PhD')
        if phd is None:
            return False
        defense = phd.date
        if defense == '':
            return False
        last = first if last is None else last
        return defense >= first and defense <= last and self.hasBeen(first, last, DOCTORANT)

    def isPostDoc(self, first, last=None):
        """ return whether this person has been a postdoc at some point over the period first...last"""
        return self.hasBeen(first, last, POSTDOC)

    def isCDDIT(self, first, last=None):
        """ return whether this person has been a CDD IT at some point over the period first...last"""
        return self.hasBeen(first, last, CT)

    def isAssociatedMember(self, first, last=None):
        """ return whether this person has been a Non-permanent professors and associate professors, including
        emeritus over the period first...last """
        return self.hasBeen(first, last, CHASSOCIE)

    def isNonPermanentEC(self, first, last=None):
        """ return whether this person has been a Non-permanent professors and associate professors, including
        emeritus over the period first...last """
        return self.hasBeen(first, last, 'PREM', ECC)

    def isNonPermanentScientist(self, first, last=None):
        """ return whether this person has been a Non-permanent full time scientists, including emeritus, post-docs
        over the period first...last """
        return self.hasBeen(first, last, 'DREM', CHCONTRACTUEL, POSTDOC)

    def isNonPermanentStaff(self, first, last=None):
        """ return whether this person has been a Non-permanent staff
        over the period first...last """
        return self.hasBeen(first, last, 'DREM', 'PREM', ECC, CHCONTRACTUEL, POSTDOC, CT, DOCTORANT)

    def isPermanentStaff(self, first, last=None):
        """ return whether this person has been a permanent staff
        over the period first...last """
        return self.isPermanentResearcher(first, last) or self.isITA(first, last)

    def isStaff(self, first, last=None):
        """ return whether this person has been in the staff
        over the period first...last """
        return self.isPermanentStaff(first, last) or self.isNonPermanentStaff(first, last)


    def isPR(self, first, last=None):
        ''' return whether this person has been a PR at some point over the period first...last'''
        return self.hasBeen(first, last, 'PR')

    def isMCF(self, first, last=None):
        ''' return whether this person has been a MCF at some point over the period first...last'''
        return self.hasBeen(first, last, 'MCF') and not self.isRangA(first, last)
 
    def isEC(self, first, last=None):
        ''' return whether this person has been a PR or MdC at some point over the period first...last'''
        return self.isPR(first, last) or self.isMCF(first, last)

    def isRangA(self, first, last=None):
        ''' return whether this person has been a PR/DR at some point over the period first...last'''
        return self.isDR(first, last) or self.isPR(first, last)

    def isRangB(self, first, last=None):
        ''' return whether this person has been a CR/MCF at some point over the period first...last'''
        return self.isCR(first, last) or self.isMCF(first, last)

    def isDR(self, first, last=None):
        ''' return whether this person has been a DR at some point over the period first...last'''
        return self.hasBeen(first, last, 'DR')

    def isCR(self, first, last=None):
        ''' return whether this person has been a CR at some point over the period first...last'''
        return self.hasBeen(first, last, 'CR') and not self.isRangA(first, last)
 
    def isChercheur(self, first, last=None):
        ''' return whether this person has been a DR or CR at some point over the period first...last'''
        return self.isDR(first, last) or self.isCR(first, last)

    def isPermanentResearcher(self, first, last=None):
        ''' return whether this person has been a DR or CR or PR or MCF at some point over the period first...last'''
        return self.isEC(first, last) or self.isChercheur(first, last)

    def isResearcher(self, first, last=None):
        ''' return whether this person has been a Researcher at some point over the period first...last'''
        return self.isPermanentResearcher(first, last) or self.isPostDoc(first, last) or self.isPhDStudent(first, last)

    def isResearchEngineer(self, first, last=None):
        ''' return whether this person has been a ResearchEngineer at some point over the period first...last'''
        return self.hasStatus(lambda s: s.isAmong('IR','IE','AI') and s.bap=='E', first, last)

    def isContractEngineer(self, first, last=None):
        ''' return whether this person has been a ResearchEngineer at some point over the period first...last'''
        return self.hasStatus(lambda s: s.isAmong(CT) and s.bap=='E', first, last)

    def isITA(self, first, last=None):
        ''' return whether this person has been a ITA at some point over the period first...last'''
        return self.hasStatus(lambda s: s.isITA(), first, last)

    def getCorpsGrade(self, date):
        '''return Corps-grade of this person, excluding her DOCTORANT period'''
        last = min(date,self.getEndDate())
        return self.get('category',last, lambda s: not s.isPhD())
    
    def getBAP(self, date):
        ''' return BAP of this person or panel for scientists'''
        first = dt(1)
        last = min(date,self.getEndDate())
        bap = self.get('bap',last)
        if bap=='S' or bap=='R' or self.isPostDoc(date):
            deptId = self.getDeptId(last)
            if deptId is not None:
                return self.lab.getSubStructures().get(deptId).panels[0]
        return "BAP "+self.get('bap',last)

    def getDateHDR(self):
        hdr = self.diplomas.get('HDR')
        return "" if hdr is None else hdr.date

    def getThesisDuration(self):
        ''' return the Thesis duration in #months, or empty String if none'''
        phd = self.diplomas.get('PhD')
        if phd is None or phd.date is None or phd.date == "":
            return ""
        start = self.get('debutThese')
        if start == "":
            return ""
        duration = math.floor((phd.date-start) / timedelta(days=30)) # duration in months
        return duration 
    
    def getTeam(self, date):
        '''return in which Team this person was at this date'''
        for a in self.career:
            result = a.getForStructDate('team', date)
            if result != '':
                return result
        return None
    
    def isInTeam(self, team, first, last, statusCondition=alwaysTrue):
        '''return this person was in this team at some point during this period'''
        for a in filter(statusCondition,self.career):
            if a.getForStructDate('team') == team and a.endStructure>=first and a.startStructure<=last:
                return True 
        return False
               
    def getDeptId(self, date):
        """return the dept Id of the dept where this person was at this date"""
        for a in self.career:
            result = a.getForStructDate('dept', date)
            if result != '':
                return result
        return None
    
#     def isWithin(self, struct, first, last, statusCondition=alwaysTrue):
#         '''return this person was in this dept at some point during this period'''
#         for a in filter(statusCondition,self.career):
#             if a.getForStructDate('dept') == struct and a.endStructure>=first and a.startStructure<=last:
#                 return True 
#         return False
               
  
# > 4 mois hors doctorants
# Nom Prénom "H/F" "Corps-grade"    "Type d'emploi(vide)"    "N° dept" "Date de naissance (JJ/MM/AAAA)"    "Panels disciplinaires / Branches d'Activités Profession. (BAP)"    "HDR (OUI/NON)" "Etablissement ou organisme employeur"    "Code UAI de l'établissement ou organisme employeur)"    "Date d'arrivée dans l'unité(MM/AA)"    "Date de départ de l'unité(MM/AA)"       
    def yieldFields(self,lastDate):
        yield self.lastName
        yield self.firstName
        yield 'H' if self.gender == 'M' else 'F'
        yield self.getCorpsGrade(lastDate)
        yield ""
        yield self.getLongest('dept')
        yield self.birthdate.date() if self.birthdate != None else ''
        yield self.getBAP(lastDate)
        yield "NON" if self.getDateHDR() == "" else str(self.getDateHDR().year)
#        yield self.get('employer', None, lambda s: not s.isAmong(DOCTORANT))
        yield self.get('employer')
        yield ""
        yield self.getStartDate().date()
        yield "" if self.getEndDate().year==2099 else self.getEndDate().date()
        yield ""

# pour doctorants
#Nom    Prénom    "H/F"    "N° dept"    "Établissement ayant délivré le master (ou diplôme équivalent)"    Directeur de thèse    Co-directeur de thèse    "Date de début de thèse(JJ/MM/AAAA)"    "Date de soutenance(JJ/MM/AAAA)"    Durée de la thèse en nombre de mois    "Devenir du doctorant"    "Financement du doctorant"
    def yieldFieldsForPhD(self,lastDate):
        yield self.lastName
        yield self.firstName
        yield 'H' if self.gender == 'M' else 'F'
        yield self.getLongest('dept')
        yield self.getMasterIntitution()
        yield self.get('directeur')
        yield self.get('codirecteur')
        start = self.get('debutThese')
        yield start.date()
        phd = self.diplomas.get('PhD')
        if phd is None: #not defended (yet)
            yield "Abandon" if self.get('etatThese')=='Abandonnée' else ""
            yield " "
        else:
            yield phd.date.date()
            yield math.floor((phd.date-start) / timedelta(days=30)) # duration in months
        yield self.get('devenir')
        yield self.getLongest('financement')
                

    def addStatus(self,s):
        if s not in self.career: # avoid duplicates
            self.career.append(s) 
            logging.info(self.getName()+" added as "+s.category+
             ": "+str(s.startContract.year)+"-"+str(s.endContract.year))
            return True
        logging.info(self.getName()+" status NOT added because already there")
        return False


class PhDStatus(Status):
    def isPhD(self):
        return True

class PermResearcher(Status):
    pass

class Emeritus(PermResearcher):
    def isEmeritus(self):
        return True

        
class ITAStatus(Status):
    def isITA(self):
        return True


STATUSTYPES = {
        'PREM':Emeritus,
        'DREM':Emeritus,
        'PR':PermResearcher,
        'DR':PermResearcher,
        'MCF':PermResearcher,
        'CR':PermResearcher,
        POSTDOC:Status,
        CHCONTRACTUEL:Status,
        CHINVITE:Status,
        CHASSOCIE:Status,
        DOCTORANT:PhDStatus,
        CDI:Status,
        ECC:Status,
        'IR':ITAStatus,
        'IE':ITAStatus,
        'AI':ITAStatus,
        'TCH':ITAStatus,
        'AJT':ITAStatus,
        CT:Status,
        STAGIAIRE: Status
}

