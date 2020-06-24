import logging
import numbers
import os
import shutil
from datetime import datetime

from lab.lab import Lab, Structure
from reporting.utils import ratio, dateIsWithin, Report


def alwaysTrue(* args):
    return True

class Next_Contract_HCERES(Report):
    def __init__(self, lab: Lab, startDate: datetime):
        super().__init__(lab,startDate,startDate)

    def listPersonnels(self,name,writer):
        writer.openSheet(name,'table')
        writer.setLineNumber(16)
        for m in self.lab.yieldMembers(lambda p: p.isPersonnel4HCERES(self.startDate, self.startDate)):
            writer.writeln(m.yieldFieldsForNextContract(self.startDate), insertMode=writer.getCurrentLine()>36)
        writer.closeSheet()

    def genSheets(self,writer,name):
        writer.open(name)
        self.listPersonnels("2.Prévision Personnels",writer)
        writer.close()


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
            "Permanent staff": lambda m,date: m.isPermanentStaff(date),
            "Non-permanent professors and associate professors, including emeritus": lambda m,date: m.isNonPermanentEC(date),
            "Non-permanent full time scientists, including emeritus, post-docs": lambda m,date: m.isNonPermanentScientist(date),
            "PhD Students": lambda m,date: m.isPhDStudent(date),
            "Non-permanent supporting personnel": lambda m,date: m.isCDDIT(date),
            "Non permanent staff": lambda m,date: m.isNonPermanentStaff(date),
            "Total": lambda m,date: m.isStaff(date),
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
            35 :("Edited theses", self.tpubs, lambda p: p.isThesis()),
            36 :("3- Production in conferences / congresses and research seminars",),
            38 :("Articles published in conference proceedings ", self.tpubs, lambda p: p.isConference()),
            39 :("Other products presented in symposia", self.tpubs, lambda p: p.isInvited()),
            40 :("4- Electronic tools and products",),
            41 :("Softwares",self.tsoftwares,alwaysTrue),
            42 :("Databases",None,None),
            61 :("International (outside Europe) grants - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Programmes internationaux")),
            62 :("International (outside Europe) grants - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Programmes internationaux")),
            63 :("ERC grants - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "ERC")),
            64 :("ERC grants - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "ERC")),
            65 :("Other European grants - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Programmes européens hors ERC et hors fonds structurels","Fonds structurels européens (FEDER, Interreg)")),
            66 :("Other European grants - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Programmes européens hors ERC et hors fonds structurels","Fonds structurels européens (FEDER, Interreg)")),
            67 :("National public grants (ANR, PHRC, FUI, DGA, etc.) - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "ANR (hors PIA)","Autres financements publics sur appels à projets")),
            68 :("National public grants (ANR, PHRC, FUI, DGA, etc.) - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "ANR (hors PIA)","Autres financements publics sur appels à projets")),
            69 :("PIA (labex, equipex etc.) grants - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Programme Investissement d'Avenir (PIA)","SATT, BPI (financement de l'innovation)")),
            70 :("PIA (labex, equipex etc.) grants - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Programme Investissement d'Avenir (PIA)","SATT, BPI (financement de l'innovation)")),
            71 :("Local grants (collectivités territoriales) - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Collectivités territoriales","Contrat de Plan État-Région")),
            72 :("Local grants (collectivités territoriales) - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Collectivités territoriales","Contrat de Plan État-Région")),
            73 :("Grants from foundations and charities - coordination", self.tcontracts, lambda c: c.isKindWithRole(True, "Fondations, associations, mécénat")),
            74 :("Grants from foundations and charities - partnership", self.tcontracts, lambda c: c.isKindWithRole(False, "Fondations, associations, mécénat")),
            75 :("10. Visiting senior scientists and postdoc",),
            76 :("Post-docs (total number)", self.tmembers, lambda m: m.isPostDoc(startDate, endDate)),
            77 :("Foreign post-docs", self.tmembers, lambda m: m.isPostDoc(startDate, endDate) and m.citizenship != 'FRANCE'),
            78 :("Visiting scientists (total number)", self.tmembers, lambda m: m.isVisitingScientist(startDate, endDate)),
            79 :("Foreign visiting scientists", self.tmembers, lambda m: m.isVisitingScientist(startDate, endDate) and m.citizenship != 'FRANCE'),
            82 :("IUF Members", self.tcontracts, lambda c: c.isIUF()),
            89 :("1- Socio-economic interactions / Patents",),
            90 :("Invention disclosures",None,None),
            91 :("Filed patents",self.tpatents,alwaysTrue),
            92 :("Accepted patents",self.tpatents,lambda a: a.isAccepted()),
            93 :("Licenced patents", self.tcontracts, lambda c: c.isKind("Ressources provenant de la propriété intellectuelle (brevets, logiciels, activités commerciales)")),
            94 :("2- Socio-economic interactions",),
            95 :("Industrial and R&D contracts", self.tcontracts, lambda c: c.isKind("Contrats de recherche industriels")),
            96 :("Cifre fellowships", self.tcontracts, lambda c: c.isCifre()),
            97 :("Creation of labs with private-public partnerships", self.tcontracts, lambda c: c.isLabcom()),
            98 :("Networks and mixed units",None,None),
            99 :("Start-ups",None,None),
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

    def _yieldStructureData(self, d: Structure):
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
        """Requires that the right number of columns is in the sheet"""
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
        logging.info('generating Annex 4 for '+self.lab.halId)
        writer.editMode = True
        self.genAnnex4forDept(writer,basefilename)

    def genAnnex4forDept(self, writer, basefilename: str, dept: Structure=None):
        if dept is None:
            filename = basefilename+'.docx'
            publist = self.lab.pubs.getPubRecord()
        else:
            filename = basefilename+' - '+dept.halId+'.docx'
            if not os.path.isfile(filename):
                shutil.copyfile(basefilename+'.docx',filename)
            publist = self.lab.pubs.getPubRecord(dept.halId)
        self.deptProdList = [
            ("#Articles","Articles", lambda p: p.isJournal()),
            ("#Books","Monographs, critical editions, translations", lambda p: p.isBook()),
            ("#BookEditions","Management and coordination of scientific books / scientific book edition", lambda p: p.isEditedBook()),
            ("#BookChapters","Book chapters", lambda p: p.isBookChapter()),
            ("#PhDThesis","PhD Thesis", lambda p: p.isThesis()),
            ("#IntConfs","Production in conferences / congresses", lambda p: p.isConference()),
        ]

        self.deptTables = [
            ("#SynthStaff",self.listStaff)
         ]

        self.prod4annex4 = [
            ("#Visiting",76,79),  # Means extract lines 75-79 of self.ProdLines
            ("#PhDProd",114,115),
            ("#Training",117,123),
           #  ('#Softwares', 41, 42),
            ("#Contracts",61,74),
            ('#Patents',91,93),
            ('#Transfer',95,97),
        ]

        writer.numberPrefix = ''
        writer.numberSuffix = '. '
        writer.setLineNumber(0)
        writer.open(filename)
        for tag,label,condition in self.deptProdList:
            writer.openSheet(tag,'bibliography',terse=True,citationStyle='HCERES',numbered=True,resetCount=False)
            total = self.lab.pubs.getStructTotal(None if dept is None else dept.halId, condition) #TODO: update this when lab is a composite of dept
            writer.writeTitle(label+" (Total Number):" + str(total), level=2)
            mainPubs = dept.mainPubs if dept is not None else []
            def inMainPubs(p): return p.getHalId() in mainPubs and condition(p)
            number = publist.getTotalScore(inMainPubs)
            if number > 0:
                writer.writeTitle("Main publications (from the overall 20%)",level=2)
                publist.writePubList(writer,inMainPubs)
#             writer.writeTitle("Other publications",level=3)
#             target(dept).writePubList(writer,lambda p: p.getHalId() not in mainpub and condition(p))
            writer.closeSheet()

        for tag,tabfunction in self.deptTables:
             tabfunction(writer,tag,dept)

        for tag,start,end in self.prod4annex4:
            writer.openSheet(tag,'list')
            writer.setLineNumber(-1)
            for line in range(start,end+1):
                label, function, cond = self.ProdLines.get(line)
                n = "" if function is None else str(function(dept, cond))
                writer.writeTitle((label+":",n),level=2)
                # TODO find a better way to do this...
                assets = 'contracts' if function == self.tcontracts else\
                        'patents' if function == self.tpatents else\
                        'softwares' if function == self.tsoftwares else None
                if assets is not None:
                    for asset in self.lab.yieldAssets(assets,self.startDate,self.endDate,dept,cond):
                        writer.writeln(asset.yieldDetails())
            writer.closeSheet()
        writer.close()

    def genDeptPublicationList(self, writer, basefilename, dept: Structure):
        if dept is None:
            filename = basefilename+'-publications.docx'
            publist = self.lab.pubs.getPubRecord()
        else:
            filename = basefilename+' - '+dept.halId+'-publications.docx'
            publist = self.lab.pubs.getPubRecord(dept.halId)
        writer.numberPrefix = ''
        writer.numberSuffix = '. '
        writer.open(filename)
        writer.writeTitle(dept.halId+" Full Publication List",level=0)
        writer.writeTitle(dept.name+' '+str(self.startDate.year)+"-"+str(self.endDate.year),level=1)
        for tag,label,condition in self.deptProdList:
            writer.openSheet(tag,'bibliography',citationStyle='HCERES',numbered=True)
            publist.writePubList(writer,condition)
            writer.closeSheet()
        writer.close()


    def listStaff(self, writer, sheetname: str, dept: Structure = None):
        writer.openSheet(sheetname,'table')
        writer.writeTitle(("Staff",self.endDate.date(),self.endContract.date()))
        for label, cond in self.SynthStaffLines.items():
            n1 = "" if cond is None else self.tmembers(dept,lambda m: cond(m,self.endDate))
            n2 = "" if cond is None else self.tmembers(dept,lambda m: cond(m,self.endContract))
            writer.writeln((label, n1, n2))
        writer.closeSheet()


