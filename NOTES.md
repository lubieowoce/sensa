## Pipenv 

Install from github:
```
> pipenv install git+http://github.com/lubieowoce/pyimgui#egg=imgui
```


Install a package from a local directory into pipenv:
```
> pipenv install --editable ..\pyimgui[full]
```

## Pipenv troubleshooting

`pipenv` failing randomly, saying stuff like `WinError: cannot find file`?
Make sure you don't have a `home` environment variable, it messed stuff up for me.


`pipenv` failing randomly, importing files from your project even though they have nothing to do with `pipenv` internals? 
Look at `pipenv`'s debug trace - you'll probably see that it tried to import a module named the same as one of your files.

Happened for:
- `signal` → fixed by rename to `eeg_signal`
- `util`   → fixed by rename to `sensa_util`



## IMGui quirks

### imgui.text

It seems like imgui.text truncates the displayed string to some length.
This maximal length also depends on the number of newlines.
We hit this limit when displaying the entire `state` dict as a single string (around 3000 chars in length) - only around 2900 characters were shown.

Repro:
```
from sensa_util import parts_of_len

with window(name="test"):
	text_len = ui.get('text_len', 3000)
	changed, val = im.slider_int('text len', text_len,
								   min_value=2800, max_value=3200)
	if changed:
		ui['text_len'] = val

	row_len = ui.get('row_len', 60)
	changed, val = im.slider_int('row len', row_len,
								   min_value=10, max_value=200)
	if changed:
		ui['row_len'] = val

	im.text(  '\n'.join(
						''.join(map(lambda _: 'a', row))
						for row in parts_of_len( range(text_len), row_len) 
						   )  )
```
Note how new letters stop appearing after `text_len` crosses some treshhold, and that this treshhold depends on `row_len` too.