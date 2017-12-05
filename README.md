
# 🔵 Sensa

Work with EEG signals comfortably.



## Installation on Windows


Sensa uses `pipenv` for installation, so you'll need python and pip. pipenv will install Sensa's own python and packages into an isolated pipenv environment, so it won't interfere with your system-wide python installation.

~~pip install pipenv~~

*As of 27.11.2017 we have to install from github, not PyPI, because the PyPI version can't install `.whl` files yet, and we need that for numpy (maybe). Installing numpy on Windows (especially x64) is a pain, I hope it can be sorted out somehow.*

First, install pipenv:
```
> pip install git+https://github.com/kennethreitz/pipenv
```
Then, clone/download sensa.
download `numpy-1.13.3+mkl-cp35-cp35m-win32.whl`
from [Christoph Gohlke's website](https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)
Put `numpy-1.13.3+mkl-cp35-cp35m-win32.whl` in sensa/numpy_installer.

Install the dependencies:
```
> cd sensa
> pipenv install

```
Done! 👍
(hopefully) 


## Instalation on Unix-based systems

You can get it to work, but right now the Pipfile is set up to installi a numpy binary on Windows. If you edit that out, it should work okay.


## Run
```
> pipenv run python gui.py
```

## Shell
```
> pipenv run python
```
