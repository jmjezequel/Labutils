import math
from datetime import datetime

from lab.lab import Lab, SubStructure


def dt(year):
    """return a datetime starting that year"""
    return datetime(year, 1, 1)


def dateIsWithin(date, start, end):
    """ return whether date is between start and end, each arg can be either a datetime or just a year as an int"""
    if type(date) is datetime:
        if type(start) is datetime:
            if type(end) is datetime:
                return date >= start and date <= end
            elif type(end) is int:  # end is expressed as a year
                return date >= start and date.year <= end
        elif type(start) is int:  # start is expressed as year
            if type(end) is datetime:
                return date.year >= start and date <= end
            elif type(end) is int:  # end is expressed as a year
                return date.year >= start and date.year <= end
    elif type(date) is int:
        return dateIsWithin(datetime(date, 1, 1), start, end)
    else:
        return False


def ratio(v1, v2):
    return "" if v2 == 0 else str(round(v1 * 100 / v2)) + '%'


def andf2(f1, f2):
    return lambda a, b: f1(a, b) and f2(a, b)


class Report:
    def __init__(self, lab: Lab, startDate: datetime, endDate: datetime):
        self.lab = lab
        self.startDate = startDate
        self.endDate = endDate

    def tmembers(self, struct, cond):
        return self.lab.getMembersCount(self.startDate, self.endDate, struct, cond)

    def tcontracts(self, struct: SubStructure, cond):
        return self.lab.getContracts(self.startDate, self.endDate, struct, cond)

    def mcontracts(self, struct: SubStructure, cond):
        return self.lab.getContractAmount(self.startDate, self.endDate, struct, cond)

    def ratioOfSums(self, struct, c1, c2):
        return ratio(self.tmembers(struct, c1), self.tmembers(struct, c2))

    def ratioOfDiff(self, struct: SubStructure, additionalCondition, baseCondition):
        return ratio(self.tmembers(struct, lambda m: baseCondition(m) and additionalCondition(m)),
                     self.tmembers(struct, baseCondition))

    def tpubs(self, struct: SubStructure, condition):
        return self.lab.pubs.getTotal(None if struct is None else struct.halId, condition)

    def tdocpubs(self, struct: SubStructure, cond):
        """return number of publications for a PhD student who defended her thesis"""
        return self.lab.getTotalOf(self.startDate, self.endDate, lambda m: len(m.getPhDRawPubList()) - 1, struct,
                                   cond)  # -1 to exclude own PhD document

    def mdocpubs(self, struct: SubStructure, cond):
        return self.lab.getMeanOf(self.startDate, self.endDate, lambda m: len(m.getPhDRawPubList()) - 1, struct, cond)

    def mduration(self, struct, cond):
        return math.floor(
            self.lab.getMeanOf(self.startDate, self.endDate, lambda m: m.getThesisDuration(), struct, cond))

    def getMoves(self, date, dept, function, condition, reference):
        """ return whether condition does not hold any longer at date"""
        if reference is None:  # not ask for a ratio
            return function(dept,
                            lambda x: condition(x, self.startDate, self.endDate) and not condition(x, date,
                                                                                                   date))
        return function(dept,
                        lambda x: condition(x, self.startDate, self.endDate) and not condition(x, date, date),
                        lambda x: reference(x, self.startDate, self.endDate) and not reference(x, date, date))

