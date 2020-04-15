import numbers
from datetime import datetime

from lab.lab import Lab, Structure
from reporting.utils import ratio, dateIsWithin, Report

def alwaysTrue(* args):
    return True


class SemEval(Report):
    def __init__(self, lab: Lab, startDate: datetime, endDate: datetime):
        super().__init__(lab,startDate,endDate)

        self.deptHRLines = [
            ("DR / Professors", self.tmembers, lambda m, sdate, edate: m.isRangA(sdate, edate)),
            ("CR / Associate professors", self.tmembers, lambda m, sdate, edate: m.isRangB(sdate, edate)),
            ("Permanent engineers", self.tmembers, lambda m, sdate, edate: m.isResearchEngineer(sdate, edate)),
            ("Temporary engineers", self.tmembers, lambda m, sdate, edate: m.isContractEngineer(sdate, edate)),
            ("Post-Docs", self.tmembers, lambda m, sdate, edate: m.isPostDoc(sdate, edate)),
            ("PhD Students", self.tmembers, lambda m, sdate, edate: m.isPhDStudent(sdate, edate)),
            ("Total", self.tmembers, lambda m, sdate, edate: m.isResearcher(sdate, edate) or m.isResearchEngineer(sdate, edate) or m.isContractEngineer(sdate, edate)),
        ]

    def listHR(self, writer, sheetname: str, team: Structure, date: datetime):
        def yieldTitle():
            yield " "
            yield "Inria"
            yield "CNRS"
            yield "University"
            yield "Others"
            yield "Total"

        def yieldHR(team: Structure, date: datetime, label: str, function, condition):
            total = 0
            yield label
            print(label, 'Inria')
            result = function(team, lambda x: x.isEmployeeOf(date,date,"INRIA") and condition(x,date,date))
            total += result
            yield result
            print(label, 'CNRS')
            result = function(team, lambda x: x.isEmployeeOf(date,date,"CNRS") and condition(x,date,date))
            total += result
            yield result
            print(label, 'ENS')
            result = function(team, lambda x: x.isEmployeeOf(date,date,*self.lab.tutellesENS) and condition(x,date,date))
            total += result
            yield result
            print(label, 'other')
            result = function(team, lambda x: not x.isEmployeeOf(date,date,*self.lab.getTutelles()) and condition(x,date,date))
            total += result
            yield result
            yield total

        writer.openSheet(sheetname, 'table')
        writer.writeTitle(yieldTitle())
        for args in self.deptHRLines:  # args is a tuple
            writer.writeln(yieldHR(team, date, *args))
        writer.closeSheet()

    def listEvolution(self, writer, teamId: str):
        team = self.lab.getTeamByName(teamId)
        writer.open(teamId)
        self.listHR(writer,"HR"+str(self.startDate.year),team,self.startDate)
        self.listHR(writer,"HR"+str(self.endDate.year),team,self.endDate)
        writer.close()

