
Tags used: *`#CHECK-OUT`* *`#PERF-IMPROVEMENT`*



# Conceptual



## Signals
`PyQt5.QtCore.pyqtSignal`
[docs](http://pyqt.sourceforge.net/Docs/PyQt5/signals_slots.html)
### Defining
Signals have to be class variables.

```
class Example:
	sig = pyqtSignal(name='sig')

	def __init__(self, x):
		...
```

Adding a new signal for a class works like def'ing a class method -
each class instance will get its own 'bound signal'.
(All of this happens via PyQt magic)

http://pyqt.sourceforge.net/Docs/PyQt5/signals_slots.html#unbound-and-bound-signals
https://stackoverflow.com/a/12638536



### Signals with optional signal values

*(Or overloaded signals I guess)*

Examples:

- `QPushButton.clicked : Signal[() | checked: bool]`
- `QAction.triggered   : Signal[() | checked: bool]`

`QPushButton.clicked : Signal[() | bool]`

`clicked` has an optional bool value - 
it will only be sent to .connect'ed functions that accept a parameter.
Both of these work:
```
btn = QPushButton('test')
btn.clicked.connect(lambda: foo()) 	  # this one is just triggered
btn.clicked.connect(lambda ch: foo()) # this one gets a bool parameter
```
I don't know how Qt determines the function signature and if it should pass something or not. It might use Python's`inspect.signature`.

http://doc.qt.io/qt-4.8/qabstractbutton.html#clicked

Optional signal values are why `reactive` has two versions of `@update` (see its [docs](reactive.py) for more)



### Bundling many signals together   *`#CHECK-OUT`*

**`QSignalMapper`**
[docs](http://doc.qt.io/qt-5/qsignalmapper.html)

It's for bundling many signals together, but giving each an identifier so you can know which signal fired.  
Might come in handy: [Figuring out why QSignalMapper doesnt work](http://pysnippet.blogspot.com/2010/09/pyqt-and-signal-overloads.html)



### Maybe-speeding-up signals/slots? *`#CHECK-OUT`* *`#PERF-IMPROVEMENT`*

Adding a decorator with a type annotation supposedly speeds up signals/slots.
[Read about it here](http://pyqt.sourceforge.net/Docs/PyQt5/signals_slots.html#the-pyqtslot-decorator)


--------


# Class reference

## QSize
`PyQt5.QtCore.QSize`
[docs](https://doc.qt.io/qt-5/qsize.html)
```
QSize
	width()  -> int
	height() -> int
```
Returned by:
- `QWidget.sizeHint()`



## QRect
`PyQt5.QtCore.QRect`
[docs](https://doc.qt.io/qt-5/qrect.html)
```
QRect
	center(),
	topLeft() ,
	topRight(),
	bottomLeft(),
	bottomRight() -> QPoint

	top(),
	bottom(),
	left(),
	right() -> int
```
Returned by:
- `QWidget.frameGeometry()`
- `QDesktopWidget.availableGeometry()`



## QPoint
`PyQt5.QtCore.QPoint`
[docs](http://doc.qt.io/qt-5/qpoint.html)
```
QPoint
	x(),
	y() -> int
```



## QAction
`PyQt5.QtWidgets.QAction`
[docs](http://doc.qt.io/qt-5.9/qaction.html)
```
QAction
slots:
	trigger()
signals:
	triggered : Signal[() | ckecked: bool]
	`triggered` has an optional bool value. (see  Conceptual/"Signals with optional signal values")
```
#### QActionGroups *`#CHECK-OUT`*
[`QActionGroups`](http://doc.qt.io/qt-5/qactiongroup.html)
Useful if you want something to listen for many actions at once.



## QPushButton
`PyQt5.QtWidgets.QPushButton`

### signals:
`clicked : Signal[() | ckecked: bool]`[docs](http://doc.qt.io/qt-4.8/qabstractbutton.html#clicked)
`clicked` has an optional bool value. (see  Conceptual/"Signals with optional signal values")



-------



# Useful methods

`QWidget.setFixed<Width|Height>(int) -> None`

