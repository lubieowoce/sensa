Install from github:
```
> pipenv install git+http://github.com/lubieowoce/pyimgui#egg=imgui
```


Install a package from a local directory into pipenv:
```
> pipenv run pip install --editable ..\pyimgui[full]
```

## Pipenv troubleshooting

`pipenv` failing randomly, saying stuff like `WinError: cannot find file`?
Make sure you don't have a `home` environment variable, it messed stuff up for me.

`pipenv` failing randomly, importing files from your project even though they have nothing to do with `pipenv` internals? 
Look at `pipenv`'s debug trace - you'll probably see that it tried to import a module named the same as one of your files. (happened for: `signal`, `sensa_util`)