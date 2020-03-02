import json
import datetime
import concurrent.futures
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *
import logging

import sys, os 
# this hack should be changed one these lib are distributed with pip
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..','..', 'Utables'))

from libhal import hal
from simplegui import stdapp, model
from ioformats import *
from ioformats import availableWriters

halLogo = """
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
"""
AStarSecurityConfs = ["ACM Symposium on Computer and Communications Security","IEEE Symposium on Security and Privacy","USENIX Security Symposium","International Cryptology Conference","Network and Distributed System Security Symposium"]

ASecurityConfs = ["International Conference on Theory and Applications of Cryptographic Techniques", "Computers & Security", "International Conference on Financial Cryptography and Data Security", "International Conference on The Theory and Application of Cryptology and Information Security", "Cryptographic Hardware and Embedded Systems", "Asia Conference on Computer and Communications Security", "Theory of Cryptography", "Symposium On Usable Privacy and Security", "International Conference on Practice and Theory in Public Key Cryptography", "Fast Software Encryption", "Security and Communication Networks"]

ASecurityJournals = ["IEEE Transactions on Information Forensics and Security", "IEEE Transactions on Dependable and Secure Computing", "IEEE Security & Privacy", "Journal of Cryptology"]

structureChoice = ["authFullName","rteamStructAcronym","deptStructAcronym","labStructAcronym"]
examples = {
    structureChoice[0]: '"Jean-Marc Jezequel" (use the quotes!)', 
    structureChoice[1]: "CAIRN, CELTIQUE, CIDRE, EMSEC, DiverSe, TAMIS", 
    structureChoice[2]: "IMT Atlantique - SRCD, IRISA-D1, IRISA-D2, IRISA-D3, IRISA-D4",
    structureChoice[3]: "IRISA"
}


def listToString(sep,list):
    if list is None:
        return ""
    return sep.join(list)


class PubSelection(model.Model):
    def __init__(self, jsonfilename):
        super().__init__('.json')
        self.startYear = IntVar()
        self.endYear = IntVar()
        self.structureKind = StringVar()
        self.collection = StringVar()
        self.structures = StringVar()
        self.conferences = StringVar()
        self.journals = StringVar()
        if jsonfilename is None:
            self.reset()
        else:
            self.loadFrom(open(jsonfilename))
            self.result = None

    def reset(self):
        super().reset()
        self.result = None
        self.startYear.set(datetime.datetime.today().year)
        self.endYear.set(datetime.datetime.today().year)
        self.structureKind.set(structureChoice[0])
        self.structures.set('')
        self.collection.set('')
        self.conferences.set('')
        self.journals.set('')

    def load(self,file):
        self.loadFromDict(json.load(file))
         
    def loadFromDict(self,dict):
        self.startYear.set(dict["startYear"])
        self.endYear.set(dict["endYear"])
        self.structureKind.set(dict["structureKind"])
        self.structures.set(listToString(',',dict["teams"]))
        if "collection" in dict:
            self.collection.set(dict["collection"])
        else:
            self.collection.set('')
        self.conferences.set(listToString('\n', dict["conferences"]))
        self.journals.set(listToString('\n', dict["journals"]))
         
    def save(self,file):
        json.dump(self.getAsDict(), file, sort_keys=True, indent=4)

    def saveResults(self):
        if self.result is not None:
            # writer = availableWriters['csv']
            writer = availableWriters['docx']
            name = 'hal' if self.filename == None else self.filename
            self.result.save(name,writer,self.getJournals(),self.getConferences())
        
    def getAsDict(self):
        result = {}
        result["startYear"] = self.startYear.get()
        result["endYear"] = self.endYear.get()
        result["structureKind"] = self.structureKind.get()
        result["teams"] = [item.strip() for item in self.structures.get().split(',')]
        result["collection"] = self.collection.get().strip()
        result["conferences"] = self.getConferences()
        result["journals"] = self.getJournals()
        return result

    def getJournals(self):
        return self.journals.get().strip().splitlines()
    
    def getConferences(self):
        return self.conferences.get().strip().splitlines()


class PubStat(stdapp.StdApp):
    def __init__(self, jsonfilename):
        super().__init__("Publication Statistics from HAL")
        self.model = PubSelection(jsonfilename)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        topframe = Frame(self.rootwindow)
        topframe.pack(side=TOP)
        self.createRadiobuttons(topframe, self.model.structureKind,"Structure kind",structureChoice,self.changeModel).pack(side=LEFT)

        middleframe =  Frame(topframe)
        middleframe.pack(side=RIGHT, fill=BOTH, expand=1)

        self.createEntry(middleframe, self.model.structures,"Structure names (separated with ',')",90,self.changeText).pack(side=TOP, fill=BOTH)
        self.createEntry(middleframe, self.model.collection,"Collection name (optional)",50,self.changeText).pack(side=TOP, fill=BOTH)
        self.createLabelledSpinbox(middleframe, self.model.startYear,"From",1970,datetime.datetime.today().year+1,self.changeModel).pack(side=LEFT)
        self.createLabelledSpinbox(middleframe, self.model.endYear,"To",1970,datetime.datetime.today().year+1,self.changeModel).pack(side=LEFT)

        self.logo = PhotoImage(data=halLogo)
        b = Button(middleframe,compound=LEFT,image=self.logo,text=" Get publications from HAL", command=self.getPublis)
        #b.image = logo
        b.pack(side=RIGHT, fill=BOTH, expand=1)



        self.createTextBox(self.rootwindow, self.model.conferences, "Conferences (one per line)",10,80,self.changeText).pack()
        self.createTextBox(self.rootwindow, self.model.journals, "Journals (one per line)",10,80,self.changeText).pack()

    def getPublis(self):
        if self.model.structures.get().strip() == '':
            messagebox.showerror("Empty Structure","No Selected Structure (person, team, dept or lab)")
            return
        self.model.result = None
        progressWindow =  stdapp.ProgressWindow(self.rootwindow, "Asking HAL...", self.abortHAL)
        try:
            self.future = self.executor.submit(hal.getStructPubRecordsFromJson,self.model.getAsDict(),progressWindow)
            self.future.add_done_callback(self.showResult)
        except Exception as err:
            messagebox.showerror("Error with HAL",err)

    def abortHAL(self):
        if self.future.cancel():
            logging.info("Cancelling HAL request upon user demand")
        self.future = None
        self.model.result = None

    def saveResults(self):
        self.model.saveResults()

    def showResult(self,futureResult): 
        if self.future is None:
            return
        result = futureResult.result()
        if result is None:
            return
        self.model.result = result
        top = Toplevel(self.rootwindow,height=50,width=600)
        top.title("HAL Publication Statistics for "+self.model.structures.get())
        
        notebook = self.createNotebook(top)
        writer = guiwriters.GuiWriter(self)
        writer.open(notebook)
        result.writeScorePerYear(writer,self.model.getJournals(),self.model.getConferences())
        result.writeBreakdownPerVenue(writer,self.model.getJournals(),self.model.getConferences())
        writer.numbered = True
        result.writePubList(writer,self.model.getJournals(),self.model.getConferences())      
        writer.close()

        bottom = Frame(top).pack(side=BOTTOM)
        dismiss = Button(top, text="Close", command=top.destroy)
        dismiss.pack(side=BOTTOM, expand=1)#fill=BOTH, 
        save = Button(top, text="Save Results", command=self.saveResults)
        save.pack(side=BOTTOM, expand=1)

        
#     def showBreakdown(self): 
#         result = self.model.result
#         if result == None:
#             self.warning("No publications read. Please get them from HAL first.")
#             return
#         
#         top = Toplevel(self.rootwindow)
#         top.title("HAL Publication Breakdown for "+self.model.structures.get())
# 
#         text = ScrolledText(top)
#         text.pack()
#         # TODO use a GuiWriter for that
#         for l in result.yieldScorePerVenue(self.model.getJournals(),self.model.getConferences()):
#             text.insert(END,l+"\n")
#         text.config(state=DISABLED)
# 
#         dismiss = Button(top, text="Close", command=top.destroy)
#         dismiss.pack(side=BOTTOM)
#         
    def changeModel(self):
        self.model.dirty = True
        self.model.result = None

    def changeText(self, origin):
        self.changeModel()

    def about(self):
        return "This is a simple Python program to compute publication stats from HAL for different types of structures (teams, departments, labs) on a given period of time for selected venues. Released by Jean-Marc Jezequel on LGPL licence (2019)"

    def configOtherMenus(self,menubar):
        self.toolmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Tools', menu=self.toolmenu)
        self.toolmenu.add_command(label='Get publications from HAL', command=self.getPublis)
 #       self.toolmenu.add_command(label='Show breakdown per venue', command=self.showBreakdown)
        self.toolmenu.add_command(label='Save results', command=self.saveResults)
        self.toolmenu.add_command(label='Clear HAL cache', command=hal.clearCache)

    def configHelpMenu(self,menubar):
        super().configHelpMenu(menubar)
        self.helpmenu.add_command(label='How To', command=self.howto)  
    
    def howto(self):
        top = Toplevel(self.rootwindow)
        top.title("How to use PubStat...")

        icon = Label(top,image=self.logo)
        icon.pack()
        text = Text(top)
        text.pack()
        text.insert(END,"Examples of Structures\n")
        for k in examples.keys():
            text.insert(END,k+": "+examples[k]+"\n")

        text.insert(END,"\nExamples of Conferences (or use '*' meaning all)\n")
        for c in AStarSecurityConfs:
            text.insert(END,c+"\n")

        text.insert(END,"\nExamples of Journals (or use '*' meaning all)\n")
        for c in ASecurityJournals:
            text.insert(END,c+"\n")

        text.insert(END,'\n\nOnce these fields have been filled up, click on "Get publications from HAL"\n')
        text.insert(END,'Caveat: HAL can only return a maximum of 9999 publications\n')
        text.config(state=DISABLED)
        button = Button(top, text="Dismiss", command=top.destroy)
        button.pack()


def main():
    if len(sys.argv) > 1:
        jsonfile = sys.argv[1]
    else:
        jsonfile = None

    hal.setuplog()
    app = PubStat(jsonfile)
    app.mainloop()


if __name__ == "__main__":
    # execute only if run as a script
    main()

