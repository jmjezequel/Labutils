import numbers
from datetime import datetime

from lab.lab import Lab, SubStructure
from reporting.utils import ratio, dateIsWithin, Report

# 1. Tableau des effectifs / categorie (debut/fin de periode)
#   --> tableau MCF/CR PRU/DR PhD postdocs ITA
#       - inclure les emerites (?)
#   --> provenance des titulaireseffectifs par tutelle
#       - pie chart par tutelle des personnels stables
#       - pie chart pour l'ensemble
#   --> indicateurs diverses
#       - #emerites, ratio de HDR, ratio f/h (permanents/tous), ratio EC
#   --> I/O durant la periode sur le personnel permanent, par tutelle
# 2. Repartition en equipe
#   --> taille respective des equipes
#       - en nombre de permanent, en nombre total
#   --> quelques indicateurs par equipe
#       - ratio de HDR, ratio EC, ratio f/h (permanents/tous)
# 3. Indicateurs de productions
#   --> #HDR soutenues, #PhD soutenues, #stagiaires M1/M2
#       - par annee et total
#   --> #publis ouvrages, journaux, conf. rangA, conf. autres
#       - par annee et total
#       - dont articles issus des theses
#   --> relations avec les autres departements
#       - pourcentage/nombre de publication intra equipe, inter equipe meme dpt, inter dpt
#   --> #brevets, #depots APP
# 4. Activites contractuelles, valorisation
#   --> montant de ressources labo (% du laboratoire), de RP (% du laboratoire)
#       - normalisation par la taille ????
#   --> pie chart sur la distribution du type de contrats selon ventilation HCERES
#       - en nombre total, en montant
#   --> #startup, #labcom, #CIFRE, #contrats bilateraux industrie (hors CIFRE), #projets collab avec partenaires indus

def alwaysTrue(* args):
    return True


class DeptStats(Report):
    def __init__(self, lab: Lab, startDate: datetime, endDate: datetime):
        super().__init__(lab,startDate,endDate)

        self.deptYearlyProdLines = [
            ("HDR defended", self.tmembers, lambda m,year: dateIsWithin(m.getDateHDR(),datetime(year,1,1), datetime(year,12,31))),
            ("PhD defended", self.tmembers,lambda m,year: m.gotPhDduring(datetime(year,1,1), datetime(year,12,31))),
            ("Internships", self.tmembers,lambda m,year: m.isIntern(datetime(year,1,1), datetime(year,12,31))),
            ("Journal publications", self.tpubs, lambda p,year: p.getYear()==year and p.isJournal()),
            # ("...incl intra dept", self.tpubs, lambda p,year: p.getYear()==year and p.isJournal() and self.lab.isIntraDeptCollab(p)),
            # ("...incl inter dept", self.tpubs, lambda p,year: p.getYear()==year and p.isJournal() and self.lab.isInterDeptCollab(p)),
            # ("...incl inter labs", self.tpubs, lambda p,year: p.getYear()==year and p.isJournal() and self.lab.isInterLabCollab(p)),
            # ("...incl internat. collabs", self.tpubs, lambda p,year: p.getYear()==year and p.isJournal() and p.isInternationalCollaboration()),
            ("Intl conf publications", self.tpubs, lambda p,year: p.getYear()==year and p.isConference(True)),
            # ("...incl intra dept", self.tpubs, lambda p,year: p.getYear()==year and p.isConference(True) and self.lab.isIntraDeptCollab(p)),
            # ("...incl inter dept", self.tpubs, lambda p,year: p.getYear()==year and p.isConference(True) and self.lab.isInterDeptCollab(p)),
            # ("...incl inter labs", self.tpubs, lambda p,year: p.getYear()==year and p.isConference(True) and self.lab.isInterLabCollab(p)),
            # ("...incl internat. collabs", self.tpubs, lambda p,year: p.getYear()==year and p.isConference(True) and p.isInternationalCollaboration()),
            ("Books", self.tpubs, lambda p, year: p.getYear() == year and p.isBook()),
            ("Book Chapters", self.tpubs, lambda p, year: p.getYear() == year and p.isBookChapter()),
            ("Edited Books", self.tpubs, lambda p, year: p.getYear() == year and p.isEditedBook()),
            ("Total", self.tpubs, lambda p, year: p.getYear() == year),
        ]

        self.deptHRLines = [
            ("Emeritus", self.tmembers, lambda m,sdate,edate: m.isEmeritus(sdate,edate)),
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
            ("Total Faculties", self.tmembers, (lambda m,sdate,edate: m.isPermanentResearcher(sdate,edate))),
            ("Ratio E/C", self.ratioOfDiff, (lambda m,sdate,edate: m.isEC(sdate,edate)), (lambda m,sdate,edate: m.isPermanentResearcher(sdate,edate))),
            ("Post-Docs", self.tmembers, lambda m,sdate,edate: m.isPostDoc(sdate,edate)),
            ("PhD Students", self.tmembers, lambda m,sdate,edate: m.isPhDStudent(sdate,edate)),
            (" ...from non local masters",  self.ratioOfDiff, (lambda m,sdate,edate: m.getMasterIntitution() not in lab.tutellesENS), (lambda m, sdate, edate: m.isPhDStudent(sdate, edate))),
            (" ...foreign", self.ratioOfDiff, (lambda m,sdate,edate: m.citizenship != 'FRANCE'),(lambda m,sdate,edate: m.isPhDStudent(sdate,edate))),
            ("Total Research Staff", self.tmembers, lambda m,sdate,edate: m.isResearcher(sdate,edate)),
            ("Female Research Staff", self.tmembers, lambda m,sdate,edate: m.isFemale() and m.isResearcher(sdate,edate)),
            ("Male Research Staff", self.tmembers, lambda m,sdate,edate: m.isMale() and m.isResearcher(sdate,edate)),
            ("Female ratio", self.ratioOfDiff, (lambda m,sdate,edate: m.isFemale()), (lambda m,sdate,edate: m.isResearcher(sdate,edate))),
            ("Permanent engineers", self.tmembers, lambda m,sdate,edate: m.isResearchEngineer(sdate,edate)),
            ("Contract engineers", self.tmembers, lambda m,sdate,edate: m.isContractEngineer(sdate,edate)),
            ("Associated members", self.tmembers, lambda m,sdate,edate: m.isAssociatedMember(sdate,edate)),
            ("Visitors", self.tmembers, lambda m,sdate,edate: m.isVisitingScientist(sdate,edate)),
            ("Interns", self.tmembers, lambda m,sdate,edate: m.isIntern(sdate,edate)),
            ("Total staff", self.tmembers, lambda m, sdate, edate: m.isMember(sdate, edate)),
        ]
        
        self.contracts = [
            ("International (outside Europe) grants", self.mcontracts, lambda c: c.isKind("Programmes internationaux")),
            ("ERC grants", self.mcontracts, lambda c: c.isKind("Grants ERC")),
            ("Other European grants", self.mcontracts, lambda c: c.isKind("Programmes Européens hors ERC")),
            ("National public grants (ANR, PHRC, FUI, INCA, etc.)", self.mcontracts,
             lambda c: c.isKind("Appels à projet ANR", "Autres financements sur appels à projets nationaux du MESR")),
            ("PIA (labex, equipex etc.) grants", self.mcontracts, lambda c: c.isKind("Programmes Investissements d'Avenir")),
            ("Local grants (collectivités territoriales)", self.mcontracts, lambda c: c.isKind("Collectivités territoriales")),
            ("Licenced patents", self.mcontracts, lambda c: c.isKind("Licences d'exploitation des brevets, certificat d'obtention végétale")),
            ("Industrial and R&D contracts ", self.mcontracts, lambda c: c.isKind("Contrats de recherche industriels")),
            ("Cifre fellowships", self.mcontracts, lambda c: c.isCifre()),
            ("Creation of labs with private-public partnerships", self.mcontracts, lambda c: c.isLabcom()),
            ("Total", self.mcontracts, alwaysTrue),
        ]

    def yieldYearlyTitle(self, dept: SubStructure=None):
        """ yield a title row with onne column per year and a total"""
        yield dept.halId if dept is not None else self.lab.name
        for year in range(self.startDate.year, self.endDate.year):
            yield year
        yield "Total"


    def genTable(self, writer, name: str, function):
        writer.open(name+'-'+str(self.startDate.year)+"-"+str(self.endDate.year))
        function(writer,self.lab.halId)
        for d in self.lab.depts.values():
            function(writer,d.halId,d)
        writer.close()

    def genReport(self,writer,name=None):
        self.genTable(writer,"Prod",self.listProduction)
        self.genTable(writer,"HR",self.listHR)
        self.genTable(writer,"Tutelles",self.listTutellesHR)
        self.genTable(writer,"Teams",self.listTeamsHR)
        self.genTable(writer,"Contracts",self.listContracts)

    def listProduction(self, writer, sheetname: str, dept: SubStructure = None):
        def yieldDeptYearlyProd(dept: SubStructure, label: str, function, cond):
            yield label
            total = 0
            for year in range(self.startDate.year, self.endDate.year):
                result = function(dept, lambda x: cond(x, year))
                total += result
                yield result
            yield total

        writer.openSheet(sheetname,'table')
        writer.writeTitle(self.yieldYearlyTitle(dept))
        for label, function, cond in self.deptYearlyProdLines:
            writer.writeln(yieldDeptYearlyProd(dept, label, function, cond))
            if function == self.tpubs:
                writer.writeln(yieldDeptYearlyProd(dept, "...incl intra team", self.tpubs,
                 lambda p, year: cond(p,year) and p.isIntraTeam()))
                writer.writeln(yieldDeptYearlyProd(dept, "...incl intra dept", self.tpubs,
                 lambda p, year: cond(p,year) and self.lab.isIntraDeptCollab(p)))
                writer.writeln(yieldDeptYearlyProd(dept, "...incl inter dept", self.tpubs,
                 lambda p, year: cond(p,year) and self.lab.isInterDeptCollab(p)))
                writer.writeln(yieldDeptYearlyProd(dept, "...incl internat. collabs", self.tpubs,
                 lambda p, year: cond(p,year) and p.isInternationalCollaboration()))
        writer.closeSheet()

    def listHR(self, writer, sheetname: str, dept: SubStructure = None):
        def yieldTitle(dept: SubStructure=None):
            yield dept.halId if dept is not None else self.lab.name
            yield self.startDate.year
            yield self.endDate.year
            yield "Delta"
            yield "Departures"
            #        yield "local Promos"
            yield "Ext. Recruits"

        def yieldHR(dept: SubStructure, label, function, condition,
                     reference=None):  # reference only useful in case of ratio
            yield label
            result = _computeFunction(self.startDate, dept, function, condition, reference)
            yield result
            delta = -result if isinstance(result, numbers.Number) else ''
            # result = function(dept, *((lambda x: condition(x,self.endDate)) for condition in conditions))
            result = _computeFunction(self.endDate, dept, function, condition, reference)
            yield result
            delta += result if isinstance(result, numbers.Number) else ''
            yield delta

            yield self.getMoves(self.endDate, dept, function, condition, reference)  # departures
            #        yield "tbd" #TODO promotion
            yield self.getMoves(self.startDate, dept, function, condition, reference)  # Arrivals

        writer.openSheet(sheetname, 'table')
        writer.writeTitle(yieldTitle(dept))
        for args in self.deptHRLines:  # args is a tuple
            writer.writeln(yieldHR(dept, *args))
        writer.closeSheet()


    def listTutellesHR(self, writer, sheetname: str, dept: SubStructure = None):
        def yieldTitle(dept: SubStructure=None):
            yield dept.halId if dept is not None else self.lab.name
            for t in self.lab.getTutelles():
                #           yield t+' '+str(self.startDate.year)
                yield t  # +' '+str(self.endDate.year)
                #           yield t+' Delta'

        def _yieldTutellesHR(dept: SubStructure, label, function, condition,
                             reference=None):  # reference only usefull in case of ratio
            yield label
            for t in self.lab.getTutelles():
                def _condTutelle(m, d1, d2): return condition(m, d1, d2) and m.isEmployeeOf(d1, d2, t)

                def _refTutelles(m, d1, d2): return reference(m, d1, d2) and m.isEmployeeOf(d1, d2, t)

                # result = _computeFunction(self.startDate, dept, function,  _condTutelle, reference)
                # yield result
                # delta = -result if isinstance(result, numbers.Number) else ''
                result = _computeFunction(self.endDate, dept, function, _condTutelle,
                                          None if reference is None else _refTutelles)
                yield result
                # delta += result if isinstance(result, numbers.Number) else ''
                # yield delta

        writer.openSheet(sheetname,'table')
        writer.writeTitle(yieldTitle(dept))
        for args in self.deptHRLines: # args is a tuple
            writer.writeln(_yieldTutellesHR(dept, * args))
        writer.closeSheet()

    def listTeamsHR(self, writer, sheetname: str, dept: SubStructure = None):
        teams = self.lab.getTeams(dept)
        def yieldTitle(dept: SubStructure=None):
            yield dept.halId if dept is not None else self.lab.name
            for t in teams:
                yield t

        def yieldHR(dept: SubStructure, label, function, condition,
                             reference=None):  # reference only usefull in case of ratio
            yield label
            for t in teams:
                def _cond(m, d1, d2): return condition(m, d1, d2) and m.isInTeam(t, d1, d2)

                def _ref(m, d1, d2): return reference(m, d1, d2) and m.isInTeam(t, d1, d2)

                # result = _computeFunction(self.startDate, dept, function,  _cond, reference)
                # yield result
                # delta = -result if isinstance(result, numbers.Number) else ''
                result = _computeFunction(self.endDate, dept, function, _cond,
                                          None if reference is None else _ref)
                yield result
                # delta += result if isinstance(result, numbers.Number) else ''
                # yield delta

        writer.openSheet(sheetname,'table')
        writer.writeTitle(yieldTitle(dept))
        for args in self.deptHRLines: # args is a tuple
            writer.writeln(yieldHR(dept, * args))
        writer.closeSheet()

    def listContracts(self, writer, sheetname: str, dept: SubStructure = None):
        def yieldDeptYearlyProd(dept: SubStructure, label: str, function, cond):
            yield label
            total = 0
            for year in range(self.startDate.year, self.endDate.year):
                result = function(dept, lambda c: cond(c) and c.isStarting(datetime(year,1,1),datetime(year,12,31)))
                total += result
                yield result
            yield total

        writer.openSheet(sheetname,'table')
        writer.writeTitle(self.yieldYearlyTitle(dept))
        for label, function, cond in self.contracts:  # we're not using function
            writer.writeln(yieldDeptYearlyProd(dept, '(#) '+label, self.tcontracts, cond))
            writer.writeln(yieldDeptYearlyProd(dept, '(€) '+label, self.mcontracts, cond))
        writer.closeSheet()


def _computeFunction(date,dept,function,condition,reference):
    if reference is None:
        return function(dept, lambda x: condition(x,date,date))
    return function(dept, lambda x: condition(x,date,date), lambda x: reference(x,date,date))

