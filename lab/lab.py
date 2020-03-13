import json

from lab.assets import Contract, Software, Patent, Asset
from lab.employees import *


class SubStructure:
    """ the inner structure of a Lab, that typically is the granularity of HCERES evaluation (kind = department,
    axis or team) """
    def __init__(self, number: int, acronym: str, name: str, halId: str, isSupport = False):
        self.number = number
        self.acronym = acronym
        self.name = name
        self.halId = halId
        self.isSupport = isSupport
        self.contracts = []  # Not used yet
        self.panels: List[str] = [] # HCERES panel names
        self.mainPubs: List[str] = []  # halId of selected publications

    def getFullName(self):
        return self.name+' ('+self.acronym+')'

    def addContract(self, contract):
        self.contracts.append(contract)


class Lab:
    """A research Lab, made of several substructures and containing members.
    Typically a UMR in the french system"""
    def __init__(self, name: str, halstructkind: str):
        self.name = name
        self.halId = name
        self.halstructkind = halstructkind
        self.members = dict() # dict(key,Person)
        self.membersByName = dict() #dict(fullName,person) used s a cache to access members by names
        self.teams = dict() # dict(teamname, DeptNumber)
        self.tutellesENS = []
        self.tutellesEPST = []
        self.tutellesAutres = []
        self.aliasTutelles = dict()
        self.depts: Dict[str,SubStructure] = dict()  # the key is the halid of the structure
        self.supportServices: Dict[str,SubStructure] = dict()  # the key is the halid of the structure
        self._substructs = None
        self.contracts = []
        self.softwares = []
        self.patents = []
        self.pubs = None


    def getSubStructures(self):
        if self._substructs is None:
            self._substructs = { ** self.depts, ** self.supportServices}
        return self._substructs

    def getTutelleFromAlias(self,alias):
        return None if alias is None else self.aliasTutelles.get(alias.upper(), alias)
    
    def getTutelles(self):
        return self.tutellesENS + self.tutellesEPST + self.tutellesAutres
    
    def getByKey(self, key: str ) -> Person:
        """ return a person from key"""
        return self.members.get(key)
                       
    def getByName(self, firstName: str, lastName: str = '') -> Person:
        """ return a person with firstName, lastName. If lastName='' consider fisrtName contains full name"""
        return self.membersByName.get(getFullName(firstName, lastName))
                               
    def getDeptOfTeam(self, team):
        """ return Department of team"""
        return self.teams.get(team,-1)

    def getTeams(self, dept: SubStructure=None):
        if dept is None:
            return self.teams.keys()
        result = []
        for t,d in self.teams.items():
            if d == dept.number:
                result.append(t)
        return result

    def getDeptPanel(self,dept):
        return self.panels.get(dept)

    def isIntraDeptCollab(self, pub):
        teams = pub.getTeams()
        if len(teams) < 2:
            return False
        depts = [0] * (len(self.depts)+1)
        for team in teams:
            d = self.getDeptOfTeam(team)
            if d>=0:
                depts[d] += 1
                if depts[d] > 0:
                    return True
        return False
    
    def isInterDeptCollab(self, pub):
        result = 0
        for dept in pub.getDepts():
            if dept in self.depts:
                result += 1
        return result > 1
    
    def isInterLabCollab(self, pub): #TODO: find a better heuristic (maybe following affiliation in HAL?)
        teams = pub.getTeams()
        if len(teams)>1:
            for t in teams:
                if self.getDeptOfTeam(t) < 0: # unknown team, assumed to be foreign
                    return True
        depts = pub.getDepts()
        if len(depts)>1:
            for d in depts:
                if not d in self.depts:  # unknown dept, assumed to be foreign
                    return True
        labs = pub.getLabs()
        return len(labs)>1 #more than one lab
#         for author in pub.getAuthors():
#             a = unicodedata.normalize('NFKD', author).encode('ascii','ignore').upper()
#             if self.getByName(a) == None: #unknow, must be international guy
#                 return True
#         return False
    
    def addContract(self,dict):
        """ register a contract provided as a dict"""
        self.contracts.append(Contract(dict))

    def addSoftware(self,dict):
        """ register a Software provided as a dict"""
        self.softwares.append(Software(dict))

    def addPatent(self,dict):
        """ register a Patent provided as a dict"""
        self.patents.append(Patent(dict))

    def addPerson(self,key,firstName,lastName,birthdate,gender,citizenship):
        person = Person(firstName,lastName,birthdate,gender,citizenship)
        person.lab = self
        self.members[key] = person
        self.membersByName[getFullName(firstName, lastName)] = person
        return person
        
    def sanityCheck(self, * checks):
        """ perform a few checks on the read data"""
        pb = 0
        for m in self.members.values():
            for check in checks:
                msg = check(m)
                if msg != "" :
                    pb += 1
                    logging.warning(m.getName()+": "+msg)
        return pb

    def getAssets(self, asset: str, startDate, endDate, struct: SubStructure=None, condition=alwaysTrue): # condition(Person,d1,d2)->boolean
        """ returns total number of assets matching condition at a certain date for struct, or if struct is None
        for the Lab """
        def cond(a: Asset): return a.isWithin(startDate, endDate, struct) and condition(a)
        result = 0
        for x in filter(cond, getattr(self,asset)):
            result += 1
        return result

    def getContractAmount(self, startDate, endDate, struct: SubStructure=None, condition=alwaysTrue): # condition(Person,d1,d2)->boolean
        """ returns total amount of contracts matching condition at a certain date for struct, or if struct is None
        for the Lab """
        def cond(c: Contract): return c.isStarting(startDate, endDate, struct) and condition(c)
        result = 0
        for contract in filter(cond,self.contracts):
            result += contract.getAmount()
        return result


    def getMembersCount(self, startDate: datetime, endDate: datetime, struct: SubStructure=None, condition=alwaysTrue): # condition(Person)->boolean
        ''' returns total matching condition at a certain date'''
        return self.countMembersSuchThat(lambda m: m.isMember(startDate,endDate,struct) and condition(m))

    def countMembersSuchThat(self,condition):
        ''' return how many members are selected by condition'''
        result = 0
        for m in filter(condition,self.members.values()):
            result += 1
        return result
            
    # def getMean(self, startdate, endDate, prop, struct=None, condition=alwaysTrue):
    #     ''' returns mean of prop for members matching condition'''
    #     return self.getMeanOf(prop,lambda m: m.isMember(startdate,endDate,struct) and condition(m))

    def getMeanOf(self, startDate,endDate, prop, struct: SubStructure=None,  condition=alwaysTrue):
        """ return mean value of prop for members selected by condition"""
        result = 0
        n = 0
        for m in filter(lambda m: m.isMember(startDate,endDate,struct) and condition(m), self.members.values()):
            value = prop(m)
            if value is not None and value != "":
                result += value
                n += 1
        return round(result / n, 1) if n > 0 else 0

    def getTotalOf(self, startDate,endDate, prop, struct: SubStructure=None, condition=alwaysTrue):
        """ return total value of prop for members selected by condition"""
        result = 0
        for m in filter(lambda m: m.isMember(startDate,endDate,struct) and condition(m), self.members.values()):
            value = prop(m)
            if value is not None and value != "":
                result += value
        return result

    def yieldMembers(self,condition):
        # for key in sorted(self.members.keys()):
        for m in filter(condition,self.members.values()):
            yield m

    def yieldAssets(self, asset: str, startDate, endDate, struct: SubStructure, condition):
        def cond(a: Asset): return a.isWithin(startDate, endDate, struct) and condition(a)
        for x in filter(cond,getattr(self,asset)):
            yield x

    def savePropertyAsJson(self,outputDir,property):
        p = getattr(self, property)
        if len(p) > 0:
            with open(outputDir + property + ".json", 'w') as jsonfile:
                json.dump(p, jsonfile, cls=LabEncoder, indent=2)

    def saveAsJson(self,outputDir):
        for property in ('members','depts','contracts','softwares','patents'):
            self.savePropertyAsJson(outputDir,property)

class LabEncoder(json.JSONEncoder):
    def default(self, obj):
       if isinstance(obj, datetime):
            return obj.date().isoformat()
       if isinstance(obj, Lab):
            return obj.name
       return obj.__dict__
#       return json.JSONEncoder.default(self, obj)

