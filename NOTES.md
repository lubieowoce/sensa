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

`pipenv` can't lock the dependencies, and complains about `numpy` versions?
Everything is installed fine, but pip's checker can't parse the version in the
wheel file correctly. For some reason, when numpy is installed from Gohlke's wheel, the version is parsed as `1.14.1+mkl` instead of `1.14.1`, which pipenv 
can't understand.
TODO: This might be possible to fix by dropping the `+mkl` from the wheel's filename. 


`pipenv` failing randomly, saying stuff like `WinError: cannot find file`?
Make sure you don't have a `home` environment variable, it messed stuff up for me.


`pipenv` failing randomly, importing files from your project even though they have nothing to do with `pipenv` internals? 
Look at `pipenv`'s debug trace - you'll probably see that it tried to import a module named the same as one of your files.

Happened for:
- `signal` → fixed by rename to `eeg_signal`
- `util`   → fixed by rename to `utils`

---

## IMGui notes

### When are clicks actually processed?

That is, when does a button react to a click?

> **Note**: *This is not 100% verified, but matches my experience and seems to make sense.*


    --|--(C)--|---C---|---B---|-->
      n       n+1     n+2
      ^ frame n: actual click happens during frame n
              ^ frame n+1: imgui 'sees' the click - imgui.is_mouse_clicked() -> True
                      ^ frame n+2: button reacts to click, button("click me") -> True


Code to see it:
```python
mouse  = imgui.is_mouse_clicked()
button = imgui.button("click")
imgui.text(
	"button: {!r:<5}  mouse:{!r:<5} both:{!r:<5}"\
		.format(mouse, button, mouse and button)
)
```

Notice that `mouse` and `button` are never `True` at the same time.
Mouse becomes true for a frame, and `button` the frame after.


---

## IMGui quirks

### `imgui.text`

It seems like imgui.text truncates the displayed string to some length.
This maximal length also depends on the number of newlines.
We hit this limit when displaying the entire `state` dict as a single string (around 3000 chars in length) - only around 2900 characters were shown.

Possible solution: consider using `imgui.text_unformatted`

Repro:
```python
from utils import parts_of_len

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