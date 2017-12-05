from PyQt5.QtWidgets import (
	QWidget, 
)
from PyQt5.QtCore import (
	QObject,
	pyqtSignal,
)


from util import *


# class Reactive(QWidget):
class Reactive():
	"""
	A Reactive object with machinery that auto-updates
	child widgets that depend on the object state when 
	the object state changes.
	Register an update function with
	obj.on_change_of('property', updateFunction)

	After a method decorated with `update`/`update_0
	is executed, all update functions registered with
	`obj.on_change_of('foo', _)` are called with the value of
	getattr(obj, 'foo')
	"""
	# state = ['counter']

	r_state_changed = pyqtSignal(name='r_state_changed')

	def on_change_of(obj, var_name: str, update_func):
		obj.r_state_changed.connect(
			lambda: update_func( getattr(obj, var_name) )
		)

	def r_update(obj):
		obj.r_state_changed.emit()



# decorator
def update_n(method):
	"""
	WARNING
	if the method is nullary, use @update_0
	(see its docs for explanation)

	Adds a self.update() after a method that modifies
	widget state to fire `state_changed` thus
	updating all state-dependent child widgets
	(by running all the update functions connected
	to `state_changed` with `on_update`)
	"""
	def with_update(*args):
		obj = args[0] 
		res = method(*args)
		obj.r_update() # args[0] is the object
		return res
	return with_update

# decorator
update = update_n

# decorator
def update_0(method):
	"""
	method: a -> IO[b], where a is the object
	This is a variant of the the @update decorator
	intended for nullary methods
	(of type a -> IO[b], because the object instance `a` is passed in.)

	It is necessary because `with_update` is variadic
	which causes Qt to sometimes pass more arguments than we want.
	
	btn.clicked.connect(lambda: obj.wrapped_method()) # works, because qt knows the method is nullary
	btn.clicked.connect(obj.wrapped_method) # doesn't work, Qt passes in an additional bool argument
											# describing whether the button is toggled

	http://doc.qt.io/qt-4.8/qabstractbutton.html#clicked

	Adds a self.update() after a method that modifies
	widget state to fire `state_changed` thus
	updating all state-dependent child widgets
	(by running all the update functions connected
	to `state_changed` with `on_update`)
	"""
	def with_update(obj):
		# raise Exception(str(args))
		res = method(obj)
		obj.r_update() # args[0] is the object
		return res
	return with_update




from inspect import getargspec
# getargspec(f: Function) -> ArgSpec[args: List[str],
# 								     varargs: Optional[str],
# 								     keywords: Optional[str],
# 								     defaults: Optional[NTuple[str]]
# 								    ]

def update_any(method):
	spec = getargspec(method)
	if spec.varargs or spec.keywords:
		raise NotImplementedError("Error: @update doesn't currently support functions with *args or **kwargs.\n" +
								  "in " + str(method) + " that takes " + str(args))

	if len(spec.args) == 0:
		return update_0(method)
	else:
		return update_n(method)
	return with_update

