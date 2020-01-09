import pya
import pathlib
import xml.etree.ElementTree as ET
import git
import glob
import os
from urllib.request import urlopen
import yaml
import logging

klayout_path = []
gityaml = os.getenv('KLAYOUT_GIT_REPO')

def getRepos(path  = None):
    global klayout_path
    if path is None:
        klayout_path = [pathlib.Path(i)/'salt' for i in pya.Application.instance().klayout_path()]
    else:
        klayout_path = [pathlib.Path(path)]
    for d in klayout_path:
        if not d.is_dir():
            klayout_path.remove(d)
    
    ymlrepos = []
    
    for d in klayout_path:
        ymlrepos.extend([pathlib.Path(f) for f in glob.glob(str(d/'**/gitrepo.yml'),recursive=True)])
    return ymlrepos

def getRemoteRepos():
    urlstr = settings.repository.url()
    if urlstr:
        url = urlopen(urlstr)
        remoterepos = yaml.safe_load(url.read())
        repos = []
        for r in remoterepos['repository']:
            f = urlopen(r)
            repo = yaml.safe_load(f.read())
            repos.append(repo)
        return repos
    #else:
    #    raise AttributeError("No Repository defined")

def updateRepos(repos : 'list(pathlib.Path of yamlFile)'):
    for repopath in repos:
        repodic = yaml.safe_load(repopath.read_text())
        #if not 'subdir' in repodic:
        #    repodic['subdir']=None
        if is_git_repo(repopath.parent):
            repo = git.Repo(repopath.parent)
            if repo.git.status('s'):
                print(f'{repopath.parent} has uncommited modifcations')
                repo.git.fetch()
            else:
                repo.remotes.origin.pull('master')
        elif 'subdir' in repodic:
            repopathnosubdir = pathlib.Path('/'.join([item for item in repopath.parent.resolve().parts if item not in repodic['subdir']]).replace('//','/'))
            if is_git_repo(repopathnosubdir):
                repo = git.Repo(repopathnosubdir)
                repo.remotes.origin.pull('master')
                repo.git.checkout()
            
            else:
                cloneRepo(url=repodic['url'],gitsubdir=repodic['subdir'],packsubdir=repopath.parent)
        else:
            cloneRepo(url=repodic['url'],packsubdir=repopath.parent)
            #ValueError(f'Unable to find a git repository for path {repopath}')
            
        
def checkoutTag(repopath, tag : str):
    repo = git.Repo(repopath)
    repo.checkout(tag)

def cloneRepo(url : str, gitsubdir : str=None, packsubdir : str=None):
    if gitsubdir is not None:
        package_path = (klayout_path[0] / packsubdir)
        package_path.mkdir(parents=True,exist_ok=True)
        
        if not is_git_repo(package_path):
            repo = git.Repo.init(package_path)
            repo.git.config('core.sparsecheckout','true')
            checkoutfile = package_path/'.git/info/sparse-checkout'
            checkoutfile.touch()
            checkoutfile.write_text(gitsubdir)
            repo.git.remote('add','-f','origin',url)
            repo.git.pull('origin','master')
            repo.git.reset('origin/master')
            repo.git.checkout('master')
        else:
            checkoutfile = package_path/'.git/info/sparse-checkout'
            with checkoutfile.open('a') as f:
                f.write('\n')
                f.write(gitsubdir)
            repo = git.Repo(package_path)
            repo.remotes.origin.pull('master')
            repo.git.checkout()
    else:
        package_path = (klayout_path[0] / packsubdir)
        package_path.mkdir(parents=True,exist_ok=True)
        repo = git.Repo.init(package_path)
        repo.git.remote('add','-f','origin',url)
        repo.git.fetch()
        repo.git.reset('origin/master','mixed')
        repo.git.checkout('origin/master','grain.xml')
        

def is_git_repo(path):
    try:
        _ = git.Repo(path).git_dir
        return True
    except git.exc.InvalidGitRepositoryError:
        return False

# Settings

class YAMLObject:
    def __init__(self, dic : dict, master=None):
        self._yamldic = dic
        self._master = master
        d = self.read_yml(dic)
        vars(self).update(d)
        
    def read_yml(self,dic : dict):
      d = dict()
      for k in dic:
        v = dic[k]
        if "value" in v:
          value = v['value']
          if 'type' in v:
            typ = str(v['type'])
          else:
            typ = "string"
          if 'description' in v:
            description = v['description']
          else:
            description = None
          if 'ro' in v:
            ro = v['ro']
          else:
            ro = False
          if self._master:
            d[k] = SettingsProperty(value,typ,description,attributes={'yamldic' : self._master._yamldic})
          else:
            d[k] = SettingsProperty(value,typ,description,attributes={'yamldic' : self._yamldic})
        else:
          if self._master:
            d[k] = YAMLObject(dic[k], master=self._master)
          else:
            d[k] = YAMLObject(dic[k], master=self)
      return d
        
class YAMLListIndex:
  def __init__(self, listname : str, index : int, yamldic : dict):
    self.listname = listname
    self.index = int(index)
    listpath = self.listname.split('.') + ['value'] # the values are stored in the value property of the list
    l = yamldic
    for s in listpath: # get to the actual list containing the values
      l = l[s]
    self._list = l
    self.value = l[self.index]

class SettingsProperty:
  def __init__(self, value, typ="string", description=None, attributes=None):
    self.value,self.type = SettingsProperty.get_valuetype(value,typ,attributes)
    self.description = description
    if 'ro' in attributes:
        self.ro = True
    else:
        self.ro = False
  
  def __call__(self):
      if self.type is YAMLListIndex:
        return self.value.value
      return self.value
      
  def get_valuetype(value,strtype,attributes):
      if strtype == 'string':
        return value,str
      elif strtype == 'listindex':
        if not 'yamldic' in attributes:
          raise AttributeError('Need a yamldic from the master yamlobject')
        d,i = value[:-1].split('[')
        return YAMLListIndex(d,int(i),attributes['yamldic']),YAMLListIndex
      elif strtype == 'list':
        return value,list
      elif strtype == 'bool':
        return bool(value),bool
      elif strtype == 'int':
        return int(value),int
      elif strtype == 'float':
        return float(value),float
      else:
        raise AttributeError(f'Unknown type {strtype}')
        
  def to_yamldic(self):
    d = {'value': self.value, 'description': self.description}
    if self.ro:
        d['ro'] = True
    if self.type is str:
    #if isinstance(self.type,str):
        d['type']= 'string'
    if self.type is YAMLListIndex:
    #elif isinstance(self.type,YAMLListIndex):
        d['value'] = f'{self.value.listname}[{self.value.index}]'
        d['type'] = 'listindex'
    if self.type is bool:
    #elif isinstance(self.type,bool):
        d['type'] = 'bool'
    if self.type is int:
    #elif isinstance(self.type,int):
        d['type'] = 'int'
    if self.type is float:
    #elif isinstance(self.type,float):
        d['type'] = 'float'
    if self.type is list:
    #elif isinstance(self.type,list):
        d['type'] = 'list'
    return d

def load_settings(path):
    #global settings
    with open(path, 'r') as infile:
        return YAMLObject(yaml.safe_load(infile))

settings_path = pathlib.Path(__file__).resolve().parent.parent.parent / "settings.yml"
default_path = pathlib.Path(__file__).resolve().parent.parent.parent / "default-settings.yml"

def reload_settings(path):
    if path.is_file():
        load_settings(path)
    else:
        load_settings(default_path)

default = load_settings(default_path)
if settings_path.is_file():
  settings = load_settings(settings_path)
else:
  settings = load_settings(default_path)

logfile_path = settings_path.parent / "kgit.log"
logger = logging.getLogger('kgit')
logger.setLevel(logging.DEBUG)
_fh = logging.handlers.RotatingFileHandler(logfile_path, maxBytes=32768, backupCount=4)
_ch = logging.StreamHandler()
_fh.setLevel(logging.getLevelName(settings.logging.logfilelevel()))
_ch.setLevel(logging.getLevelName(settings.logging.logstreamlevel()))
_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
_fh.setFormatter(_formatter)
_ch.setFormatter(_formatter)

logger.addHandler(_fh)
logger.addHandler(_ch)

updateRepos(getRepos())
