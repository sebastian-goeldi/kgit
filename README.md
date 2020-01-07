# KLayout git Package Manager
KLayout git Management

Allow the management of KLayout Packages through git.

Through a .yml file the repository is described. If the package finds a .yml file in any packages of KLayout (in the salt folder), it adds them to manage them by git, even if they weren't a git repository before.


* Example gitrepo.yml file:
  ```
  url:
    https://github.com/sebastian-goeldi/kgit
  name:
    kgit
  ```
    
Additionally a subdirectory can be defined. If a subdirectory is defined only a sparse-checkout will be performed (requires git >= 2.14)

* Example gitrepo.yml with subdirectory:
  
  ```
  url:
    git@gitlab.psiquantum.lan:hardware/tapeouts/klayout/klayout_technologies.git
  subdir:
    ex
  name:
    example/com
  ```
  This will create a KLayout package at $KLAYOUT_HOME/salt/example/com/ex/ .

