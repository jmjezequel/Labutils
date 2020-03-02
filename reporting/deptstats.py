import numbers
from datetime import datetime

from lab.lab import Lab, SubStructure
from reporting.utils import ratio, dateIsWithin, Report

class DeptStats(Report):
    def __init__(self, lab: Lab, startDate: datetime, endDate: datetime, endContract: datetime):
        super().__init__(lab,startDate,endDate)

        self.deptYearlyProdLines = [
            ("PhD defended", self.tmembers,lambda m,year: m.gotPhDduring(datetime(year,1,1), datetime(year,12,31))),
            ("HDR defended", self.tmembers, lambda m,year: dateIsWithin(m.getDateHDR(),datetime(year,1,1), datetime(year,12,31))),
            ("Journal publications", self.tpubs, lambda p,year: p.getYear()==year and p.isJournal()),
            ("...incl intra dept", self.tpubs, lambda p,year: p.getYear()==year and p.isJournal() and self.lab.isIntraDeptCollab(p)),
            ("...incl inter dept", self.tpubs, lambda p,year: p.getYear()==year and p.isJournal() and self.lab.isInterDeptCollab(p)),
            ("...incl inter labs", self.tpubs, lambda p,year: p.getYear()==year and p.isJournal() and self.lab.isInterLabCollab(p)),
            ("...incl internat. collabs", self.tpubs, lambda p,year: p.getYear()==year and p.isJournal() and p.isInternationalCollaboration()),
            ("Intl conf publications", self.tpubs, lambda p,year: p.getYear()==year and p.isConference(True)),
            ("...incl intra dept", self.tpubs, lambda p,year: p.getYear()==year and p.isConference(True) and self.lab.isIntraDeptCollab(p)),
            ("...incl inter dept", self.tpubs, lambda p,year: p.getYear()==year and p.isConference(True) and self.lab.isInterDeptCollab(p)),
            ("...incl inter labs", self.tpubs, lambda p,year: p.getYear()==year and p.isConference(True) and self.lab.isInterLabCollab(p)),
            ("...incl internat. collabs", self.tpubs, lambda p,year: p.getYear()==year and p.isConference(True) and p.isInternationalCollaboration())
        ]

        self.deptHRLines = [
            # ("Emeritus", self.tmembers, lambda m,sdate,edate: m.isEmeritus(sdate,edate)),
            ("DR", self.tmembers, lambda m,sdate,edate: m.isDR(sdate,edate)),
            ("PR", self.tmembers, lambda m,sdate,edate: m.isPR(sdate,edate)),
            ("RangA Females", self.ratioOfDiff, (lambda m,sdate,edate: m.isFemale()), (lambda m,sdate,edate: m.isRangA(sdate,edate))),
            ("CR", self.tmembers, lambda m,sdate,edate: m.isCR(sdate,edate)),
            ("MCF", self.tmembers, lambda m,sdate,edate: m.isMCF(sdate,edate)),
            ("RangB Females", self.ratioOfDiff, (lambda m,sdate,edate: m.isFemale()), (lambda m,sdate,edate: m.isRangB(sdate,edate))),
            ("RangB HDR", self.ratioOfDiff, (lambda m,sdate,edate: m.getDateHDR() !=""), (lambda m,sdate,edate: m.isRangB(sdate,edate))),
            ("Females among RangB HDR", self.ratioOfDiff, (lambda m,sdate,edate: m.isFemale()), (lambda m,sdate,edate: m.getDateHDR() !="" and m.isRangB(sdate,edate))),
            ("HDR among RangB Females", self.ratioOfDiff, (lambda m,sdate,edate: m.getDateHDR() !=""), (lambda m,sdate,edate: m.isFemale() and m.isRangB(sdate,edate))),
            ("HDR among RangB Males", self.ratioOfDiff, (lambda m,sdate,edate: m.getDateHDR() !=""), (lambda m,sdate,edate: m.isMale() and m.isRangB(sdate,edate))),
            ("Post-Docs", self.tmembers, lambda m,sdate,edate: m.isPostDoc(sdate,edate)),
            ("PhD Students", self.tmembers, lambda m,sdate,edate: m.isPhDStudent(sdate,edate)),
            (" ...from non local masters",  self.ratioOfDiff, (lambda m,sdate,edate: m.getMasterIntitution() not in lab.tutellesENS), (lambda m, sdate, edate: m.isPhDStudent(sdate, edate))),
            (" ...foreign", self.ratioOfDiff, (lambda m,sdate,edate: m.citizenship != 'FRANCE'),(lambda m,sdate,edate: m.isPhDStudent(sdate,edate))),
            ("Total Research Staff", self.tmembers, lambda m,sdate,edate: m.isResearcher(sdate,edate)),
            ("Female Research Staff", self.tmembers, lambda m,sdate,edate: m.isFemale() and m.isResearcher(sdate,edate)),
            ("Male Research Staff", self.tmembers, lambda m,sdate,edate: m.isMale() and m.isResearcher(sdate,edate)),
            ("Female ratio", self.ratioOfDiff, (lambda m,sdate,edate: m.isFemale()), (lambda m,sdate,edate: m.isResearcher(sdate,edate))),
            ("Permanent engineers", self.tmembers, lambda m,sdate,edate: m.isResearchEngineer(sdate,edate)),
            ("Contract engineers", self.tmembers, lambda m,sdate,edate: m.isContractEngineer(sdate,edate))
        ]

    def genReport(self,writer,name=None):
        writer.open("Prod-"+str(self.startDate.year)+"-"+str(self.endDate.year))
        self.listProduction(writer)
        for d in self.lab.depts.values():
            self.listProduction(writer,d)
        writer.close()
        writer.open("HR-"+str(self.startDate.year)+"-"+str(self.endDate.year))
        self.listHR(writer)
        for d in self.lab.depts.values():
            self.listHR(writer, d)
        writer.close()

    def listProduction(self,writer,dept: SubStructure=None,sheetname=None):
        if sheetname is None:
            sheetname = dept.halId if dept is not None else self.lab.name
        writer.openSheet(sheetname,'table')
        writer.writeTitle(self.yieldDeptYearlyProdTitle(dept.halId if dept != None else self.lab.name))
        for args in self.deptYearlyProdLines: # args is a tuple
            writer.writeln(self.yieldDeptYearlyProd(dept, * args))
        writer.closeSheet()

    def yieldDeptYearlyProdTitle(self,dept):
        yield dept
        for year in range(self.startDate.year,self.endDate.year):
            yield year
        yield "Total"

    def yieldDeptYearlyProd(self,dept: SubStructure,label: str,function=None,filter=None):
        yield(label)
        total = 0
        for year in range(self.startDate.year,self.endDate.year):
            result = function(dept, lambda x: filter(x,year))
            total += result
            yield result
        yield total

    def listHR(self,writer,dept: SubStructure=None,sheetname=None):
        if sheetname == None:
            sheetname = dept.halId if dept != None else self.lab.name
        writer.openSheet(sheetname,'table')
        writer.writeTitle(self.yieldHRTitle(dept.halId if dept != None else self.lab.name))
        for args in self.deptHRLines: # args is a tuple
            writer.writeln(self.yieldHR(dept, * args))
        writer.closeSheet()

    def yieldHRTitle(self,dept):
        yield dept
        yield self.startDate.year
        yield self.endDate.year
        yield "Delta"
        yield "Departures"
#        yield "local Promos"
        yield "Ext. Recruits"

    def yieldHR(self,dept: SubStructure,label,function,condition,reference=None): #reference only usefull in case of ratio
        yield(label)
        def compute(date,dept,function,condition,reference):
            if reference == None:
                return function(dept, lambda x: condition(x,date,date))
            return function(dept, lambda x: condition(x,date,date), lambda x: reference(x,date,date))
        result = compute(self.startDate, dept, function, condition, reference)
        yield result
        delta = -result if isinstance(result, numbers.Number) else ''
        #result = function(dept, *((lambda x: condition(x,self.endDate)) for condition in conditions))
        result = compute(self.endDate, dept, function, condition, reference)
        yield result
        delta += result if isinstance(result, numbers.Number) else ''
        yield delta
        def getMoves(date,dept,function,condition,reference):
            ''' return whether condition does not hold any longer at date'''
            if reference == None: # not ask for a ratio
                return function(dept, lambda x: condition(x,self.startDate,self.endDate) and not condition(x,date,date))
            return function(dept,
                            lambda x: condition(x,self.startDate,self.endDate) and not condition(x,date,date),
                            lambda x: reference(x,self.startDate,self.endDate) and not reference(x,date,date))
        yield getMoves(self.endDate, dept, function, condition, reference) #departures
#        yield "tbd" #TODO promotion
        yield getMoves(self.startDate, dept, function, condition, reference) #Arrivals
