
# 🔵 Sensa

Work with EEG signals comfortably.



## Installation
### Windows

*(64-bit only for now)*

Sensa uses `pipenv` for installation, so you'll need python and pip installed. pipenv will install Sensa's own python and packages into an isolated pipenv environment, so it won't interfere with your system-wide python installation.

First, install pipenv:
```
> pip install pipenv
```
Then, clone/download sensa.

Download `numpy-1.13.3+mkl-cp35-cp35m-win64.whl`  
from [Christoph Gohlke's website](https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)  
Put `numpy-1.13.3+mkl-cp35-cp35m-win64.whl` in sensa/whl/x64/numpy.  

Install the dependencies:
```
> cd sensa
> pipenv install
```
Done! 👍
(hopefully) 


TODO: Specify the right version to install in Pipfile?
https://docs.pipenv.org/advanced/#specifying-basically-anything

### Unix-based systems

Similar to Windows, but right now the Pipfile is set up to install a numpy binary. If you edit that out, it should work okay.


## Run
```
> pipenv run python app.py
```

## Shell
```
> pipenv run python
```
