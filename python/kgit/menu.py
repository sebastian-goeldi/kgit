import pya
import kgit
import importlib
import yaml

class Dialog(pya.QDialog):

    def __init__(self, parent=None):
    
    
        self.repolist = None
        #self.loadRepos()
    
        self.vbox,self.tabw = self.tabWindow()
        self.setLayout(self.vbox)
        self.settingtab = self.settings(parent=self)
        self.repotab = self.repoManager(parent=self)
        self.tabw.addTab(self.repotab,"Packages")
        self.tabw.addTab(self.settingtab, "Properties")
        
        self.setWindowTitle("KLayout GitManager Settings")
        
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.adjustSize()
        
        
    def settings(self,parent=None):
        if parent is None:
            parent = self
        settingw = pya.QWidget(self)
        vbox = pya.QVBoxLayout(settingw)
        settingw.setLayout(vbox)
        self.settingspath = kgit.settings_path
        self.settings = {}

        scrollarea = pya.QScrollArea(self)
        optionswidget = pya.QWidget(self)
        scrollarea.setWidget(optionswidget)
        scrollarea.setWidgetResizable(True)

        optionvbox = pya.QVBoxLayout(optionswidget)
        categorydict = vars(kgit.settings)

        hbSplitter = pya.QHBoxLayout()
        vboxbuttons = pya.QVBoxLayout()
        vbox.addLayout(hbSplitter)
        hbSplitter.addWidget(scrollarea)
        hbSplitter.addLayout(vboxbuttons)

        resetButton = pya.QPushButton('Restore Defaults', self)
        resetButton.clicked(self.restoreDefaults)
        vboxbuttons.addWidget(resetButton)

        vboxbuttons.addStretch()
        
        # General Settings
        
        cat = 'Repository'
        groupbox = pya.QGroupBox(cat,self)
        optionvbox.addWidget(groupbox)
        vb = pya.QVBoxLayout(groupbox)
        self.settings['repository'] = {}
        repdic = self.settings['repository']
        repdic['repository'] = kgit.settings.repository()
        l = pya.QHBoxLayout()
        le = pya.QLineEdit(repdic['repository'],self)
        la = pya.QLabel(kgit.settings.repository.description,self)
        l.addWidget(le)
        l.addWidget(la)
        vb.addLayout(l)
        
        # Log settings
        
        cat = "Logs"
        groupbox = pya.QGroupBox(cat, self)
        optionvbox.addWidget(groupbox)
        vb = pya.QVBoxLayout(groupbox)
        self.settings['logs'] = {}
        logdic = self.settings['logs']
        logdic['filelvl'] = (kgit.settings.logging.logfilelevel.value.index,kgit.settings.logging.logfilelevel)
        logdic['streamlvl'] = (kgit.settings.logging.logstreamlevel.value.index,kgit.settings.logging.logstreamlevel)
        ## File Logging
        v = pya.QComboBox(self)
        l = pya.QHBoxLayout()
        for i in kgit.settings.logging.levels():
            v.addItem(i)
        v.currentIndex = logdic['filelvl'][0]
        vb.addLayout(l)
        l.addWidget(v)
        d = pya.QLabel(kgit.settings.logging.logfilelevel.description, self)
        l.addWidget(d)
        l.addStretch()
        ## Stream Logging
        v = pya.QComboBox(self)
        l = pya.QHBoxLayout()
        for i in kgit.settings.logging.levels():
            v.addItem(i)
        v.currentIndex = logdic['streamlvl'][0]
        vb.addLayout(l)
        l.addWidget(v)
        d = pya.QLabel(kgit.settings.logging.logfilelevel.description, self)
        l.addWidget(d)
        l.addStretch()
        vbox.addStretch()

        save = pya.QPushButton("Save", self)
        save.clicked = self.save
        abort = pya.QPushButton("Cancel", self)
        abort.clicked = self.abort
        hbox = pya.QHBoxLayout()
        vbox.addLayout(hbox)
        hbox.addWidget(abort)
        hbox.addStretch()
        hbox.addWidget(save)
        
        optionvbox.addStretch()
        
        return settingw

    def repoManager(self, parent=None):
        if parent is None:
            parent = self
        
        widget = pya.QWidget(self)
        
        vbox = pya.QVBoxLayout(widget)
        widget.setLayout(vbox)
        
        self.repolist = pya.QListWidget(widget)        
        repos = kgit.getRepos()
        
        items = []
        
        for r in repos:
            s = yaml.safe_load(r.read_text())
            whatsthis=s['name']
            if '/' in s['name']:
                description = (f"Name:\t\t{s['name'].rsplit('/',1)[1]}\n"
                               f"Project:\t\t{s['name'].rsplit('/',1)[0]}\n"
                               )
            else:
                description = f"Name:\t\t{s['name']}\n"
            description += "Location:\t\tlocal\n"
            #if 'author' in s:
            #    description += f"Author:\t\t{s['author']}\n"
            #    pass
            description += f"Project URL:\t\t{s['url']}"
            if 'subdir' in s:
                description += f"\nProject Sub-URL:\t{s['subdir']}"
            item = pya.QListWidgetItem(description)
            item.whatsThis=s['name']
            items.append(item)
            self.repolist.addItem(item)
        remoterepos = kgit.getRemoteRepos()
        for r in remoterepos:
            if r['name'] in [i.whatsThis for i in items]:
                continue
            if '/' in r['name']:
                description = (f"Name:\t\t{r['name'].rsplit('/',1)[1]}\n"
                               f"Project:\t\t{r['name'].rsplit('/',1)[0]}\n"
                               )
            else:
                description = f"Name:\t\t{r['name']}\n"
            description += "Location:\t\tremote\n"
            #if 'author' in r:
            #    description += f"Author:\t\t{r['author']}\n"
            #    pass
            description += f"Project URL:\t\t{r['url']}"
            if 'subdir' in r:
                description += f"\nProject Sub-URL:\t{r['subdir']}"
                
            item = pya.QListWidgetItem(description)
            item.whatsThis=r['name']
            self.repolist.addItem(item)
        
        vbox.addWidget(self.repolist)
        
        buttonbox = pya.QHBoxLayout(widget)
        downloadbutton = pya.QPushButton("Download && Install",widget)
        downloadbutton.clicked = self.downloadRepos
        buttonbox.addWidget(downloadbutton)
        buttonbox.addStretch()
        removebutton = pya.QPushButton("Remove",widget)
        buttonbox.addWidget(removebutton)
        vbox.addLayout(buttonbox)
        
        return widget

    def downloadRepos(self, checked):
        for it in self.repolist.selectedItems():
            d = yaml.safe_load(it.text.replace('\t',' '))
            if d['Location'] == 'local':
                continue
            else:
                if 'Project' in d:
                    if 'Project Sub-URL' in d:
                        kgit.cloneRepo(url=d['Project URL'], gitsubdir=d['Project Sub-URL'], packsubdir=d['Project'])
                    else:
                        kgit.cloneRepo(url=d['Project URL'], packsubdir=d['Project'])
                else:
                    if 'Project Sub-URL' in d:
                        kgit.cloneRepo(url=d['Project URL'], gitsubdir=d['Project Sub-URL'])
                    else:
                        kgit.cloneRepo(url=d['Project URL'])
        
    def abort(self, checked):
        self.reject()

    def tabWindow(self):
        tabw = pya.QTabWidget()
        vbox = pya.QVBoxLayout(self)
        self.setLayout(vbox)
        vbox.addWidget(tabw)
        return vbox,tabw

    def save(self, checked):
        for c in self.settings.keys():
            v = self.settings[c]
            for s in v.keys():
                setattr(getattr(kgit.settings, c), s, self.settings[c][s][1](self.settings[c][s][0]))
        sdict = {}
        for k in kgit.settings.__dict__.keys():
            sdict[k] = {}
            for kk in kgit.settings.__dict__[k].__dict__.keys():
                sdict[k][kk] = kgit.settings.__dict__[k].__dict__[kk]
        with open(self.settingspath, 'w') as f:
            json.dump(sdict, f, indent=4, sort_keys=False)
        importlib.reload(kgit)
        set_settings()
        self.accept()


    def restoreDefaults(self, checked):
        dir_path = Path(__file__).parent.parent.parent
        sf = dir_path / "settings.json"
        df = dir_path / "default-settings.json"

        msg = pya.QMessageBox(pya.QMessageBox.Warning,
                              "Reload Default Settings",
                              "Restore default Settings?\nThis will close this dialog and reload the default settings.",
                              pya.QMessageBox.StandardButton.Cancel | pya.QMessageBox.StandardButton.Ok,
                              self)
        # msg.setStandardButtons(pya.QMessageBox.StandardButton.Ok | pya.QMessageBox.StandardButton.Cancel)
        res = msg.exec_()
        if res == pya.QMessageBox.Ok.to_i():
            kgit.settings_path.write_bytes(kgit.default_path.read_bytes())
            kgit.load_settings(kgit.settings_path)
            self.accept()
        else:
            self.reject()


    def abort(self, checked):
        self.reject()


def open_dialog():
    dialog = Dialog(pya.Application.instance().main_window())
    dialog.exec_()


if __name__ == "__main__":
    open_dialog()
