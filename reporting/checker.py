import numbers
from datetime import datetime

from lab.lab import Lab
from lab.employees import STATUSTYPES, Person, Status
from reporting.utils import Report


class Checker(Report):
    def __init__(self, lab: Lab, startDate: datetime, endDate: datetime):
        super().__init__(lab, startDate, endDate)

    def list_dept_members(self, writer, struct):
        for category in STATUSTYPES.keys():
            writer.openSheet(category, 'table')
            writer.writeTitle(('Nom', 'Prénom', 'Genre', 'Equipe', 'Arrivée', 'Départ', 'Employeur'))

            def cond(m: Person):
                return m.isInCategories(self.startDate, self.endDate, struct, category)

            def statusCond(s: Status):
                return s.isMatching(self.startDate, self.endDate, struct) and s.isAmong(category)

            m: Person
            for m in self.lab.yieldMembers(cond):
                start = m.getStartDate(statusCond)
                end = m.getEndDate(statusCond)
                writer.writeln((m.lastName,
                                m.firstName,
                                m.gender,
                                m.getTeam(end),
                                str(start.date()) if start > self.startDate else "",
                                str(end.date()) if end < self.endDate else "",
                                m.get('employer')
                                ))
            writer.closeSheet()

    def list_depts(self, writer):
        for s in self.lab.getSubStructures().values():
            writer.open("HR-" + s.halId)
            self.list_dept_members(writer, s)
            writer.close()
