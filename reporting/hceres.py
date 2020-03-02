import logging
import numbers
from datetime import datetime

from lab.lab import Lab, SubStructure
from reporting.utils import ratio, dateIsWithin, Report


class EvalHCERES(Report):
    def __init__(self, lab: Lab, startDate: datetime, endDate: datetime, endContract: datetime):
        super().__init__(lab,startDate,endDate)
        self.endContract = endContract
        self.SynthStaffLines = {
            "Full professors and similar positions": lambda m,date: m.isPR(date),
            "Assistant professors and similar positions": lambda m,date: m.isMCF(date),
            "Full time research directors (Directeurs de recherche) and similar positions": lambda m,date: m.isDR(date),
            "Full time research associates (Chargés de recherche) and similar positions": lambda m,date: m.isCR(date),
            "Other scientists": None,
            "High school teachers": None,
            "Supporting personnel": lambda m,date: m.isITA(date),
            "Permanent staff": None,
            "Non-permanent professors and associate professors, including emeritus": lambda m,date: m.isNonPermanentEC(date),
            "Non-permanent full time scientists, including emeritus, post-docs": lambda m,date: m.isNonPermanentScientist(date),
            "PhD Students": lambda m,date: m.isPhDStudent(date),
            "Non-permanent supporting personnel": lambda m,date: m.isCDDIT(date)
            }

        self.ProdLines = {
            18 :("1. Articles",),
            19 :("Scientific articles (total number)", self.tpubs, lambda p: p.isJournal()),
            28 :("2- Books",),
            29 :("Monographs, critical editions, translations (total number)", self.tpubs, lambda p: p.isBook()),
            31 :("Management and coordination of scientific books", self.tpubs, lambda p: p.isEditedBook()),
            32 :("... in English or another foreign language", self.tpubs, lambda p: p.isEditedBook() and p.isInternationalAudience()),
            33 :("Book chapters (total number)", self.tpubs, lambda p: p.isBookChapter()),
            34 :("... chapters in English or another foreign language", self.tpubs, lambda p: p.isBookChapter() and p.isInternationalAudience()),
            36 :("3- Production in conferences / congresses and research seminars",),
            38 :("Articles published in conference proceedings ", self.tpubs, lambda p: p.isConference()),
            39 :("Other products presented in symposia", self.tpubs, lambda p: p.isInvited()),
            40 :("4- Electronic tools and products",),
            61 :("International (outside Europe) grants - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Programmes internationaux")),
            62 :("International (outside Europe) grants - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Programmes internationaux")),
            63 :("ERC grants - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Grants ERC")),
            64 :("ERC grants - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Grants ERC")),
            65 :("Other European grants - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Programmes Européens hors ERC")),
            66 :("Other European grants - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Programmes Européens hors ERC")),
            67 :("National public grants (ANR, PHRC, FUI, INCA, etc.) - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Appels à projet ANR","Autres financements sur appels à projets nationaux du MESR")),
            68 :("National public grants (ANR, PHRC, FUI, INCA, etc.) - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Appels à projet ANR","Autres financements sur appels à projets nationaux du MESR")),
            69 :("PIA (labex, equipex etc.) grants - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Programmes Investissements d'Avenir")),
            70 :("PIA (labex, equipex etc.) grants - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Programmes Investissements d'Avenir")),
            71 :("Local grants (collectivités territoriales) - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Collectivités territoriales")),
            72 :("Local grants (collectivités territoriales) - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Collectivités territoriales")),
            73 :("Grants from foundations and charities - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Fondations associations caritatives, Institut Carnot, RTRA, RTRS")),
            74 :("Grants from foundations and charities - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Fondations, associations caritatives, Institut Carnot, RTRA, RTRS")),
            75 :("10. Visiting senior scientists and postdoc",),
            76 :("Post-docs (total number)", self.tmembers, lambda m: m.isPostDoc(startDate, endDate)),
            77 :("Foreign post-docs", self.tmembers, lambda m: m.isPostDoc(startDate, endDate) and m.citizenship != 'FRANCE'),
            78 :("Visiting scientists (total number)", self.tmembers, lambda m: m.isVisitingScientist(startDate, endDate)),
            79 :("Foreign visiting scientists", self.tmembers, lambda m: m.isVisitingScientist(startDate, endDate) and m.citizenship != 'FRANCE'),
            82 :("IUF Members", self.tcontracts, lambda c: c.isIUF()),
            89 :("1- Socio-economic interactions / Patents",),
            90 :("Invention disclosures",),
            91 :("Filed patents",),
            92 :("Accepted patents",),
            93 :("Licenced patents", self.tcontracts, lambda c: c.isKind("Licences d'exploitation des brevets, certificat d'obtention végétale")),
            94 :("2- Socio-economic interactions",),
            95 :("Industrial and R&D contracts ", self.tcontracts, lambda c: c.isKind("Contrats de recherche industriels")),
            96 :("Cifre fellowships", self.tcontracts, lambda c: c.isCifre()),
            97 :("Creation of labs with private-public partnerships", self.tcontracts, lambda c: c.isLabcom()),
            98 :("Networks and mixed units",),
            99 :("Start-ups",),
            110:("1- Educational outputs",),
            111:("Books", self.tpubs, lambda p: p.isBook() and not p.isInternationalAudience()),
            112:("E-learning, MOOCs, multimedia courses, etc.",),
            113:("2- Scientific productions (articles, books, etc.) from theses",),
            114:("Scientific productions (articles, books, etc.) from theses",self.tdocpubs,lambda m: m.gotPhDduring(startDate, endDate)),
            115:("Mean number of publications per student (Biology & Science and technology only)",self.mdocpubs,lambda m: m.gotPhDduring(startDate, endDate)),
            116:("3- Training",),
            117:("Habilitated (HDR) scientists", self.tmembers, lambda m: m.getDateHDR() != "" or m.isRangA(endDate)),
            118:("HDR obtained during the period", self.tmembers, lambda m: dateIsWithin(m.getDateHDR(),startDate, endDate)),
            119:("PhD students (total number)", self.tmembers, lambda m: m.isPhDStudent(startDate, endDate)),
            120:("PhD students benefiting from a specific doctoral contract, including Cifre", self.tmembers, lambda m: m.isPhDStudent(startDate, endDate)),
            121:("Defended PhDs", self.tmembers, lambda m: m.gotPhDduring(startDate, endDate)),
            122:("Mean PhD duration", self.mduration, lambda m: m.gotPhDduring(startDate, endDate)),
            123:("Internships (M1, M2)", self.tmembers, lambda m: m.isIntern(self.startDate, self.endDate))
            }

        self.paritylines = {
            "Parity":None,
            "Number of women in the unit and in each team":lambda m: m.isFemale() and m.isMember(endDate,endDate),
            "Number of men in the unit and in each team":lambda m: m.isMale() and m.isMember(endDate,endDate),
            "Number of women among university lecturer-researchers":lambda m: m.isFemale() and m.isPermanentResearcher(endDate),
            "Number of men among university lecturer-researchers":lambda m: m.isMale()  and m.isPermanentResearcher(endDate)
            }

    def listStructuration(self,name,writer):
        writer.openSheet(name,'table')
        writer.setLineNumber(18)
        for d in self.lab.depts.values():
            writer.writeln(self._yieldStructureData(d))
        writer.setLineNumber(45)
        for d in self.lab.supportServices.values():
            writer.writeln(self._yieldStructureData(d))
        writer.closeSheet()

    def _yieldStructureData(self, d: SubStructure):
        date = self.endDate
        yield ""
        yield d.getFullName()
        yield "" # responsable
        for p in d.panels:
            yield p
        # Effectifs Enseignants-chercheurs
        yield self.lab.getMembersCount(date, date, d, lambda m: m.isEC(date, date))
        # Effectifs Chercheurs EPST et cadres scientifiques EPIC permanents
        yield self.lab.getMembersCount(date, date, d, lambda m: m.isChercheur(date, date))
        # Effectifs doctorants
        yield self.lab.getMembersCount(date, date, d, lambda m: m.isPhDStudent(date, date))
        # Effectifs ITA, BIATSS et personnels non-scientifiques des EPIC permanents
        yield self.lab.getMembersCount(date, date, d, lambda m: m.isITA(date, date))


    def listPersonnels(self,name,writer):
        writer.openSheet(name,'table')
        writer.setLineNumber(17)
        for m in self.lab.yieldMembers(lambda p: p.isPersonnel4HCERES(self.startDate, self.endDate)):
            writer.writeln(m.yieldFields(self.endDate), insertMode=writer.getCurrentLine()>37)
        writer.closeSheet()

    def listPhDStudents(self,name,writer):
        writer.openSheet(name,'table')
        writer.setLineNumber(16)
        for m in self.lab.yieldMembers(lambda p: p.isPhDStudent(self.startDate, self.endDate)):
            writer.writeln(m.yieldFieldsForPhD(self.endDate), insertMode=writer.getCurrentLine()>36)
        writer.closeSheet()

    def listSynthStaff(self,name,writer):
        '''Requires that the right number of columns is in the sheet'''
        writer.openSheet(name,'table')
        writer.setLineNumber(8)
        writer.writeTitle(self._yieldSynthTitle(),always=True)
        for title,filter in self.SynthStaffLines.items():
            writer.writeln(self._yieldSynthData('',filter,self.endDate,self.endContract))
        writer.closeSheet()

    def _yieldSynthTitle(self):
        yield "Active staff"
        for t in self.lab.tutellesENS:
            yield t
        for t in self.lab.tutellesEPST:
            yield t
        endD = str(self.endDate.date())
        endC = str(self.endContract.date())
        yield ""
        yield ""
        yield self.lab.name + "-" + endD
        yield self.lab.name + "-" + endC
        for d in self.lab.depts:
            yield d+"-"+endD
            yield d+"-"+endC

    def _yieldSynthData(self,label,dateFilter,date,endContract):
        ''' yield data for the Synth sheet. dateFilter(Person,date)->boolean'''
        def yieldTutelles(tutelles):
            for t in tutelles:
                n = 0 if dateFilter== None else self.lab.countMembersSuchThat(lambda m: m.isEmployeeOf(date, date, t) and dateFilter(m, date))
                yield "" if n == 0 else n

        yield label
        yield from yieldTutelles(self.lab.tutellesENS)
        yield from yieldTutelles(self.lab.tutellesEPST)
        #yieldTutelles(self.labo.tutellesAutres,2)
        yield ""
        yield ""
#        yield ""
        yield 0 if dateFilter == None else self.lab.countMembersSuchThat(lambda m: dateFilter(m, date))
        yield 0 if dateFilter == None else self.lab.countMembersSuchThat(lambda m: dateFilter(m, endContract))
        for d in self.lab.depts.values():
            yield 0 if dateFilter is None else self.lab.getMembersCount(date, date, d, lambda m: dateFilter(m, date))
            yield 0 if dateFilter is None else self.lab.getMembersCount(date, date, d, lambda m: m.getEndDate() >= endContract and dateFilter(m, endContract))

    def listProductionsStats(self,name,writer):
        writer.openSheet(name,'table')
        writer.writeTitle(self._yieldProductionStatsTitle())
        for line,args in self.ProdLines.items():
            writer.setLineNumber(line)
            writer.writeln(self._yieldConsolidatedData(* args))
        writer.closeSheet()

    def _yieldProductionStatsTitle(self):
        yield ""
        yield(str(self.startDate.year)+"-"+str(self.endDate.year))
        yield self.lab.name
        for d in self.lab.depts:
            yield d

    def _yieldConsolidatedData(self, label, function=None, cond=None):
        yield "" #sheet starts in B
        yield(label)
        if cond == None:
            yield " "
        else:
            yield function(None, cond)
        for d in self.lab.depts.values():
            if cond is None:
                yield " "
            else:
                yield function(d, cond)

    def listParity(self,name,writer):
        writer.openSheet(name,'table')
        writer.setLineNumber(28)
        for title,filter in self.paritylines.items():
            writer.writeln(self._yieldParityData(title,filter,self.endDate))
        writer.closeSheet()

    def _yieldParityData(self,label,filter,date):
        yield ""
        yield label
        yield "" if filter is None else self.lab.getMembersCount(date, date, None, filter)
        for d in self.lab.depts.values():
            yield "" if filter is None else self.lab.getMembersCount(date, date, d, filter)

    def genSheets(self,writer,name):
        writer.open(name)
        self.listStructuration("2. Structuration de l'unité",writer)
        self.listPersonnels("3.1 Liste des personnels",writer)
        self.listPhDStudents("3.2 Liste des doctorants",writer)
        self.listSynthStaff("3.3 Synth staff unit ",writer)
        self.listProductionsStats("4. Research Prod & Activ  ",writer)
        self.listParity("5. Org & Life of the unit ",writer)
        writer.close()

    def genAnnex4(self,writer,basefilename):
        for d in self.lab.depts.values():
            logging.info('generating Annex 4 for '+d.halId)
            writer.editMode = True
            self.genAnnex4forDept(writer,basefilename,d)
            writer.editMode = False
            self.genDeptPublicationList(writer,basefilename,d)

    def genAnnex4forDept(self, writer, basefilename: str, dept: SubStructure):
        filename = basefilename+' - '+dept.halId+'.docx'
        publist = lambda d: self.lab.pubs.getPubRecord(d.halId)
        self.deptProdList = [
            ("#Articles",publist, lambda p: p.isJournal()),
            ("#Books",publist, lambda p: p.isBook()),
            ("#BookEditions",publist, lambda p: p.isEditedBook()),
            ("#BookChapters",publist, lambda p: p.isBookChapter()),
            ("#IntConfs",publist, lambda p: p.isConference()),
            ("#PhDThesis",publist, lambda p: p.isThesis())
        ]
        # self.deptTables = [
        #     ("#ProductionNumbers",self.listProduction)
        # ]

        self.prod4annex4 = [
            ("#Visiting",76,79),  # Means extract lines 75-79 of self.ProdLines
            ("#Training",117,123),
            ("#Contracts",61,74)
        ]

        writer.numberPrefix = ''
        writer.numberSuffix = '. '
        writer.open(filename)
        for tag,target,condition in self.deptProdList:
            writer.openSheet(tag,'bibliography',terse=True,citationStyle='HCERES',numbered=True,resetCount=False)
            writer.writeTitle("Total " + tag +": " + str(self.lab.pubs.getStructTotal(dept.halId, condition)), level=2)
            writer.writeTitle("Main publications (in the overall 20%)",level=2,bold=True)
            target(dept).writePubList(writer,lambda p: p.getHalId() in dept.mainPubs and condition(p))
#             writer.writeTitle("Other publications",level=3)
#             target(dept).writePubList(writer,lambda p: p.getHalId() not in mainpub and condition(p))
            writer.closeSheet()
        # for tag,tabfunction in self.deptTables:
        #     tabfunction(writer,dept,tag)

        for tag,start,end in self.prod4annex4:
            writer.openSheet(tag)
            writer.setLineNumber(-1)
            for line in range(start,end+1):
                label, function, filter = self.ProdLines.get(line)
                writer.writeln((label,": ",str(function(dept,filter))))
                writer.closeSheet()
        writer.close()

    def genDeptPublicationList(self,writer,basefilename,dept: SubStructure):
        filename = basefilename+' - '+dept.halId+'-publications.docx'
        writer.numberPrefix = ''
        writer.numberSuffix = '. '
        writer.open(filename)
        writer.writeTitle(dept.halId+" Full Publication List",level=0)
        writer.writeTitle(dept.name+' '+str(self.startDate.year)+"-"+str(self.endDate.year),level=1)
        for tag,target,condition in self.deptProdList:
            writer.openSheet(tag,'bibliography',citationStyle='HCERES',numbered=True)
            target(dept).writePubList(writer,condition)
            writer.closeSheet()
        writer.close()




