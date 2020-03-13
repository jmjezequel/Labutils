import math
from datetime import datetime

class Asset(dict):
    """Base class for Contracts, Software, Patents etc.
    all with an internal representation as a dict read from excel"""
    def __init__(self, *args, **kwargs):
        super(Asset, self).__init__(*args, **kwargs)
        self.__dict__ = self # allow to acces field x with either self.x or self['x']
        for k,v in self.__dict__.items():
            if isinstance(v,str): # strip strings
                self.__dict__[k] = v.strip()

    def isWithin(self, startDate: datetime, endDate: datetime, struct=None):
        pass

    def yieldDetails(self):
        pass

class Contract(Asset):
    """ data from a contract where fields are initialized through a dict"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def isWithin(self,startDate: datetime,endDate: datetime,struct=None):
        """Whether this contract is for dept 'struct' and existed between the dates"""
        okdept = True if struct is None else struct.halId == self.Departement_scientifique
        return okdept and self.Date_de_debut_prise_deffet <= endDate and self.Date_de_fin_echeance >= startDate

    def isStarting(self,startDate: datetime,endDate: datetime,struct=None):
        """Whether this contract is for dept 'struct' and started between the dates"""
        okdept = True if struct is None else struct.halId == self.Departement_scientifique
        return okdept and self.Date_de_debut_prise_deffet <= endDate and self.Date_de_debut_prise_deffet >= startDate

    def isKind(self,*args):
        """ return whether this contract is of HCERES kind in args"""
        return self.Categorie_HCERES in args

    def isKindWithRole(self,leader: bool,*args):
        """ return whether this contract is of HCERES kind in args with coordination career 'role' """
        coord = leader == (self.PorteurPartenaire == 'Porteur')
        return self.isKind(*args) and coord

    def getAmount(self):
        return 0 if self.Montant_total_du_contrat is None else self.Montant_total_du_contrat

    def isCifre(self): return self.Nom_du_type_de_Programme == 'CIFRE'

    def isLabcom(self): return self.Nom_du_type_de_Programme == 'Labcom'

    def isIUF(self): return self.Nom_du_type_de_Programme == 'IUF'

    def yieldDetails(self):
        # yield self.Acronyme
        yield self.Intitule_objet
        yield '('+str(round(self.getAmount()/1000))+' k€)'

class IPAsset(Asset):
    """ data from an IP Asset where fields are initialized through a dict"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def isWithin(self,startDate: datetime,endDate: datetime,struct=None):
        """Whether this asset is for dept 'struct' and existed between the dates"""
        okdept = True if struct is None else struct.halId in self.Depts
        return okdept and self.Date_de_depot <= endDate and self.Date_de_depot >= startDate

    def yieldDetails(self):
        # yield self.Acronyme
        yield self.Libelle_dossier
        # yield '('+self.N_depot+')'


class Software(IPAsset):
    """ data from a Software where fields are initialized through a dict"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Patent(IPAsset):
    """ data from a Patent where fields are initialized through a dict"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def isAccepted(self):
        return self.N_depot is not None