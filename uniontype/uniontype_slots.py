from typing import (
	Any,
	Tuple, List, Iterator,
	Callable,
	TypeVar,
	NoReturn, # functions that always raise or exit the interpreter 
)

Fun = Callable
A = TypeVar('A')

import sys
from warnings import warn

from keyword import iskeyword


__all__ = [
	'union',
	'untyped_union',
]


def union(
		name: str,
		variant_specs: List[  Tuple[str, List[Tuple[str, type]] ]  ],
		typecheck=False,
		immutable=True,
		verbose=False,
		_module_name=None,
	) -> Tuple[type, ...]:

	if typecheck:
		raise NotImplementedError('Typechecking is not supported yet')
	if not immutable:
		raise NotImplementedError('Mutability is not supported yet')
	
	print('union::', name, *variant_specs, sep='\n')
	variant_specs = [(variant_name, [attr_name for (attr_name, attr_type) in attr_names_and_types])
					 for (variant_name, attr_names_and_types) in variant_specs]

	# module name

	# `untyped_union` relies on sys._getframe to inspect the caller's frame and
	# get the right module name. That won't work if `union` calls it,
	# since the caller's frame will be located in this module.
	# So we have to get the module name here, and pass it down.				 
	# See the "module name" section in `union`'s definition for more.
	if _module_name is None:
		try:
			_module_name = sys._getframe(1).f_globals.get('__name__', '__main__')
		except (AttributeError, ValueError):
			warn(RuntimeWarning("Cannot access the caller's module name - pickle will likely have trouble unpickling {} objects".format(name)))
			_module_name = __name__ # fallback - this module

	return untyped_union(name, variant_specs, immutable=immutable, verbose=verbose, _module_name=_module_name)




def untyped_union(
		name: str,
		variant_specs: List[ Tuple[str, List[str]] ],
		immutable=True,
		verbose=False,
		_module_name=None,
	) -> Tuple[type, ...]:

	if not immutable:
		raise NotImplementedError('Mutability is not supported yet')

	variant_names      = [variant_name for (variant_name, attr_names_and_types) in variant_specs]
	variant_attr_names = [attr_names for (variant_name, attr_names) in variant_specs]
	variant_ids = range(len(variant_names))

	# # useful for the typed version:
	# variant_attr_specs = [attr_names_and_types for (variant_name, attr_names_and_types) in variant_specs]
	# variant_attr_names = [[attr_name for (attr_name, attr_type) in attr_names_and_types] for attr_names_and_types in variant_attr_specs]
	# # variant_attr_types = [[attr_type for (attr_name, attr_type) in attr_names_and_types] for attr_names_and_types in variant_attr_specs]

	max_n_fields = max((len(attrs) for attrs in variant_attr_names), default=0)
	slots = ('_variant_id',) + tuple('_{}'.format(i) for i in range(max_n_fields))
	if verbose:
		print('class {}'.format(name))
		print('__slots__', slots, sep='\n')



	class Class:
		__slots__ = slots
		_variants    = variant_names
		_variant_ids = tuple(variant_ids)
		_variant_fields = {
			name: tuple(fields)
			for (name, fields) in zip(variant_names, variant_attr_names)
		}
		_variant_id_fields = tuple(tuple(field_names) for field_names in variant_attr_names)


		def raise_direct_init_forbidden(self) -> NoReturn:
			""" Objects of this class can only be created with its constructor-classmethods. """
			cls = type(self)
			raise TypeError(
				'Cannot instantiate {type!r} directly - use one of the variant constructors: {vars}'.format(
					type=cls.__name__, vars=cls._variants_repr()
				)
			)
		__init__ = raise_direct_init_forbidden



		def _values(self) -> tuple:
			# TODO: codegen it
			cls = type(self)
			field_vals = (field_descriptor.__get__(self) for field_descriptor in cls._positional_descriptors[ : len(cls._variant_id_fields[self._variant_id])])
			return tuple(field_vals)
		values = _values

			

		@property
		def _variant(self) -> str:
			return type(self)._variants[self._variant_id]
		variant = _variant



		def _as_tuple(self) -> tuple:
			return (self._variant,) + self._values()
		as_tuple = _as_tuple 
		_astuple = _as_tuple # namedtuple convention
		astuple  = _as_tuple


		def _as_dict(self) -> dict:
			# TODO: codegen it
			cls = type(self)
			res = {'variant': self._variant}
			for (field, val) in zip(cls._variant_id_fields[self._variant_id], self._values()):
				res[field] = val
			return res
		as_dict = _as_dict
		_asdict = _as_dict # namedtuple convention
		asdict  = _as_dict # namedtuple convention



		def _replace(self, **fields_and_new_vals) -> name:
			"""
			Analogous to `namedtuple`'s `_replace`.
			Returns a new value with fields modified according
			to the keyword arguments.
			"""
			cls = type(self)
			fields = cls._variant_id_fields[self._variant_id]
			field_descriptors = cls._positional_descriptors

			new = cls.__new__(cls)
			variant_id_descriptor = cls._variant_id
			variant_id_descriptor.__set__(new, self._variant_id)

			# important - by using zip, `field_descriptors` gets trimmed to the length of `fields`,
			# so we never access an uninitialized attribute
			for (field, field_descriptor) in zip(fields, field_descriptors):
				old_field_val = field_descriptor.__get__(self)
				new_field_val = fields_and_new_vals.pop(field, old_field_val)
				field_descriptor.__set__(new, new_field_val)

			if not fields_and_new_vals:
				return new
			else:
				# Reuse __getattr__'s error cause guessing.
				# TODO: Factor it out to make it less hacky.
				first_bad_field = next(iter(fields_and_new_vals))
				if first_bad_field.startswith('_'):
					# Catch this here. if __getattr__ sees this name, 
					# it will (correctly) guess that it can't be a field,
					# and will show the generic "object doesn't have attribute x" error.
					# However, if someone tries to `a._replace(_variant_id=15)`, the message will
					# be confusing, because the objects clearly *do* have a '_variant_id' attribute. 
					raise TypeError("_replace can only modify fields, and '{}' is not a field".format(first_bad_field))
				else:
					# getattr should give a nice error message
					self.__getattr__(first_bad_field)


		replace = _replace
		set     = _replace
		update  = _replace


		def __hash__(self):
			return hash(self._as_tuple())


		def _copy(self) -> name:
			""" Returns a shallow copy of self. """
			# TODO: efficiency - codegen it
			cls = type(self)

			new = cls.__new__(cls)
			variant_id_descriptor = cls._variant_id
			variant_id_descriptor.__set__(new, self._variant_id)

			for field_descriptor in cls._positional_descriptors[ : len(cls._variant_id_fields[self._variant_id])]:
				field_val = field_descriptor.__get__(self)
				field_descriptor.__set__(new, field_val)
			return new

		copy = _copy
		

		# Pickle methods
		# 	We used __getstate__ and __setstate__ instead of __getnewargs__
		#	because even after calling __new__ the correct arguments,
		#	pickle tried to manually set each attribute from __slots__,
		#	which didn't work because __setattr__ blocks all modification attempts.
		#	__(get/set)state__ make pickle back off and let us handle all initialization. 

		def __getstate__(self) -> tuple:
			""" For pickling """
			return (self._variant_id,) + self._values()


		def __setstate__(self, state: tuple) -> None:
			""" For unpickling """
			# print('{}.__setstate__({})'.format(object.__repr__(self), state))
			cls = type(self)
			_variant_id, *field_vals = state

			variant_id_descriptor = cls._variant_id
			variant_id_descriptor.__set__(self, _variant_id)

			field_descriptors = cls._positional_descriptors 
			for (field_descriptor, field_val) in zip(field_descriptors, field_vals):
				field_descriptor.__set__(self, field_val)




		# Methods that always raise

		def _raise_error_missing_descriptor(self, attr: str) -> NoReturn:
			"""
			A fake __getattr__ implemented only to give better error messages.
			Will always raise an exception, because if it was called, one of the
			following is true:
			- the class has no data descriptor for `attr`
			- the class has a data descriptor for `attr`, but the descriptor raised AttributeError()
				(e.g. the user tried to access an uninitialized slot)
			"""

			cls = type(self)

			if cls._is_unsafe_accessor_name(attr):
				attr = cls._extract_field_from_unsafe_accessor_name(attr)

			ex = None
			if any(attr in fields for fields in cls._variant_fields.values()):
				# A data descriptor for 'attr' exists, but it raised AttributeError() and the interpreter called __getattr__ as a fallback
				ex = AttributeError(
					"Incorrect '{type}' variant: Field '{attr}' not declared in variant '{var}'. Variants: {vars}".format(
						attr=attr, var=self._variant, type=cls.__qualname__, vars=cls._variants_repr(),
					),
				)
			elif cls._is_permitted_union_field_name(attr):
				# No data descriptor for 'attr' exists - if we didn't create it, then there's no attribute with
				# this name in any variant
				ex = AttributeError(
					"Unknown attribute: Field '{attr}' not declared in any variant of '{type}': {vars}".format(
						attr=attr, type=cls.__qualname__, vars=cls._variants_repr(),
					) 
				)
			else: # Couldn't possibly be a field - probably a typo or nonexistent method
				ex = AttributeError("'{type}' object has no attribute '{attr}'".format(type=cls.__qualname__, attr=attr,) )

			raise ex
		__getattr__ = _raise_error_missing_descriptor



		def _raise_setattr_forbidden(self, attr: str, val) -> NoReturn:
			"""
			A fake __setattr__ implemented only to give better error messages
			for attribute modification attempts.
			"""
			raise TypeError(
				"Cannot modify '{type}' values. Use `myval2 = myval.replace(attr=x)` instead. (Tried to set {self}.{field} = {val!r})".format(
					type=type(self).__qualname__, self=self, field=attr, val=val,
				)
			)
		__setattr__ = _raise_setattr_forbidden



		def _raise_delattr_forbidden(self, attr: str) -> NoReturn:
			"""
			A fake __delattr__ implemented only to give better error messages
			for attribute modification attempts.
			"""
			raise TypeError(
				"Cannot modify '{type}' values.".format(
					type=type(self).__qualname__,
				)
			)
		__delattr__ = _raise_delattr_forbidden

		
		@classmethod
		def _variant_reprs(cls) -> Iterator[str]:
			return (
				"{var}({fields})".format(var=variant, fields=str.join(', ', cls._variant_fields[variant]))
				for variant in cls._variants
			)


		# Error message helpers

		@classmethod
		def _variants_repr(cls) -> str:
			"Used to display all the variants in error messages."
			return str.join(', ', cls._variant_reprs())

		@classmethod
		def _is_permitted_union_field_name(cls, field: str) -> bool:
			return not field.startswith('_') and not iskeyword(field)


		@classmethod
		def _is_unsafe_accessor_name(cls, field: str) -> bool:
			""" '_Foo_x' -> True """
			return any(field.startswith('_{}_'.format(variant)) for variant in cls._variants)

		@classmethod
		def _extract_field_from_unsafe_accessor_name(cls, field: str) -> str:
			return field.split('_', maxsplit=2)[2]

		def _get_invalid_variant_error(self) -> Exception:
			cls = type(self)
			return RuntimeError(
				"Internal error: {id} is not a valid '{type}' variant id  (ids: {ids})".format(
					type=cls.__qualname__, id=self._variant_id, ids=cls._variant_ids,
				)
			)

	# end class


	# class name
	Class.__name__     = name
	Class.__qualname__ = name

	if _module_name is None:
		# caller of `union` didn't pass a module name - get the caller's module name
		try:
			_module_name = sys._getframe(1).f_globals.get('__name__', '__main__')
		except (AttributeError, ValueError):
			warn(
				RuntimeWarning(
					"`untyped_union` can't access the caller's module name - pickle will likely have trouble unpickling {!r} objects".format(name)
				)
			)
			_module_name = __name__ # fallback - this module
	Class.__module__ = _module_name

	variant_def_indent = ' ' * (len(name) + 1)
	Class.__doc__ = (
		'A sum type (also called a variant or tagged union).\n' +
		'\n' +
		'{name} = ' + str.join(
			'\n{indent}| ', Class._variant_reprs()
		) + '\n' +
		'\n'

	).format(
		name=name,
		indent=variant_def_indent
	)


	all_variant_fields = uniq( sum(Class._variant_id_fields, ()) )
	variant_ids_that_have_attr = {
		attr: [
			id_ for id_ in Class._variant_ids
			if attr in Class._variant_id_fields[id_]
		]
		for attr in all_variant_fields
	}

	real_attr_for_variant_id_and_field = {
		(id_, field): '_{}'.format(ix)
		for id_ in Class._variant_ids
			for (ix, field) in enumerate(Class._variant_id_fields[id_])
	}


	# code templates (to be `.format()`'ed before evaluation) are prefixed with '__'
	# finished code strings (ready to be `eval`'d / `exec`'d) are prefixed with  '_'

	# constructors

	__def_constructor = """
def constructor(cls, {field_args}) -> '{name}':
	val = cls.__new__(cls)
	cls._variant_id.__set__(val, {id})

	{set_fields}
	return val
"""[1:] # drop the first newline

	# __set_field = "val.{real_attr} = {field_arg}" 		  # fast, but doesn't work with defensive setattr 
	__set_field = "cls.{real_attr}.__set__(val, {field_arg})" # slower because of the extra method lookup, but works with defensive setattr
	# ^ Uses property descriptors, because normal assignments are blocked to make the values more or less immutable


	# TODO:
	# Possible perf improvement:
	# Cache the descriptors' __set__ methods to skip one lookup.
	# This makes setting via descriptor call as fast as setting via '='. 
	# It introduces a bit of complexity though - it's another thing to
	# remember. Maybe add this after investigating Pickle integration.

	# Class.__set_variant_id = Class._variant_id.__set__
	# Class.__set_0 = Class._0.__set__
	# Class.__set_1 = Class._1.__set__
	# __set_field = "cls.__set_{real_attr}(val, {field_arg})"


	_def_constructors = {}
	for (id_, variant) in zip(Class._variant_ids, Class._variants):
		fields = Class._variant_id_fields[id_]
		_field_args = str.join(', ', fields)
		_set_fields = str.join(
			'\n\t',
			(
				__set_field.format(
					field_arg=field,
					real_attr=real_attr_for_variant_id_and_field[(id_, field)]
				)
				for field in fields
			)

		)
		_def_constructor = __def_constructor.format(
			field_args=_field_args,
			name=name,
			id=id_,
			set_fields=_set_fields,
		)
		_def_constructors[variant] = _def_constructor

	if verbose:
		print(*[variant+'\n'+_def_constructors[variant] for variant in Class._variants], sep='\n')

	for (variant, _def_constructor) in _def_constructors.items():
		assert not hasattr(Class, variant), "'{}' already defined. Class dir:\n{}".format(variant, dir(Class))
		constructor = eval_def(_def_constructor)
		constructor.__name__ = variant
		constructor.__qualname__ = '{}.{}'.format(name, constructor.__name__)
		setattr(Class, variant, classmethod(constructor))



	# .is_Foo(), is_Bar(), etc. methods for pattern mathing 

	__def_is_some_variant = """
def is_some_variant(self) -> bool:
	return self._variant_id == {id}
"""[1:]

	for (id_, variant) in zip(Class._variant_ids, Class._variants):
		method_name = 'is_{variant}'.format(variant=variant)
		_def_is_some_variant = __def_is_some_variant.format(id=id_)
		if verbose:
			print(method_name, _def_is_some_variant, sep='\n')
		is_some_variant = eval_def(_def_is_some_variant)
		is_some_variant.__name__ = method_name
		is_some_variant.__qualname__ = '{}.{}'.format(name, is_some_variant.__name__)
		setattr(Class, method_name, is_some_variant)



	# field getters

	__def_getter = """
def getter(self):
	variant_id = self._variant_id
	{ifs_that_return_real_attr}
	else: raise AttributeError()
"""[1:]
	#   ^ the AttributeError gets swallowed by the interpreter, and __getattr__ is called as a fallback

	__if_variant_equal_id_then_return_real_attr = "if variant_id == {id}: return self.{real_attr}"

	_def_getters = {}
	for field in all_variant_fields:
		valid_variant_ids = variant_ids_that_have_attr[field]
		assert len(valid_variant_ids) >= 1
		_ifs_that_return_real_attr = str.join(
			'\n\tel', # adding 'el' will turn all 'if's after the first one into elifs
			(
				__if_variant_equal_id_then_return_real_attr.format(
					id=id_,
					real_attr=real_attr_for_variant_id_and_field[(id_, field)],
				)
				for id_ in valid_variant_ids
			)
		) or 'if False: pass' # default for classes with no variants (unusual but possible)

		_def_getter = __def_getter.format(
			ifs_that_return_real_attr=_ifs_that_return_real_attr,
		)
		_def_getters[field] = _def_getter


	if verbose:
		print(*[field+'\n'+_def_getters[field] for field in all_variant_fields], sep='\n')


	for (field, _def_getter) in _def_getters.items():
		assert not hasattr(Class, field), "'{}' already defined. Class dir:\n{}".format(field, dir(Class))
		getter = eval_def(_def_getter)
		getter.__name__ = field
		getter.__qualname__ = '{}.{}'.format(name, getter.__name__)

		setattr(Class, field, property(getter))



	# unsafe accessors

	for (id_, variant) in zip(Class._variant_ids, Class._variants):
		for field in Class._variant_fields[variant]:
			unsafe_accessor_name = '_{var}_{field}'.format(var=variant, field=field)
			unsafe_accessor_descriptor = getattr(Class, real_attr_for_variant_id_and_field[(id_, field)])
			setattr(Class, unsafe_accessor_name, unsafe_accessor_descriptor)



	# enable a form of postional access
	Class._positional_descriptors = tuple(getattr(Class, '_{}'.format(field_ix)) for field_ix in range(max_n_fields))


	# __repr__

	__def_repr = """
def __repr__(self) -> str:
	variant_id = self._variant_id
	
	{ifs_that_return_repr}
	else: raise self._get_invalid_variant_error()
"""[1:]

	__if_variant_equal_id_then_return_repr = "if variant_id == {id}: return '{variant}({arg_kw_fmts})'.format(self=self)"
	__arg_kw_fmt = "{field}={{self.{real_attr}!r}}"

	_ifs_that_return_repr = str.join(
		'\n\tel',
		(
			__if_variant_equal_id_then_return_repr.format(
				id=id_,
				variant=variant,
				arg_kw_fmts=str.join(
					', ',
					(__arg_kw_fmt.format(field=field, real_attr=real_attr_for_variant_id_and_field[(id_, field)]) for field in Class._variant_id_fields[id_])
				)
			)
			for (id_, variant) in zip(Class._variant_ids, Class._variants)
		)
	) or 'if False: pass' # default for classes with no variants (unusual but possible)

	_def_repr = __def_repr.format(ifs_that_return_repr=_ifs_that_return_repr)
	if verbose:
		print('__repr__\n'+_def_repr)


	
	__repr__ = eval_def(_def_repr)
	__repr__.__name__ = '__repr__'
	__repr__.__qualname__ = '{}.{}'.format(name, __repr__.__name__)
	Class.__repr__ = __repr__


	# __eq__

	__def_eq = """
def __eq__(a, b) -> bool:
	if type(a) is not type(b):
		return NotImplemented

	a_variant_id = a._variant_id
	b_variant_id = b._variant_id
	if a_variant_id != b_variant_id:
		return False
	
	{ifs_that_return_equal}
	else: raise a._get_invalid_variant_error()
"""[1:]

	__if_variant_equal_id_then_return_equal = "if a_variant_id == {id}: return ({compare_real_attrs})"
	__compare_real_attr = "(a.{real_attr} == b.{real_attr})"
	_ifs_that_return_equal = str.join(
		'\n\tel',
		(
			__if_variant_equal_id_then_return_equal.format(
				id=id_,
				compare_real_attrs=str.join(
					' and ',
					(__compare_real_attr.format(real_attr=real_attr_for_variant_id_and_field[(id_, field)]) for field in Class._variant_id_fields[id_])
				) or 'True' # default for variants with no fields
			)
			for id_ in Class._variant_ids
		)
	) or 'if False: pass' # default for classes with no variants (unusual but possible)

	_def_eq = __def_eq.format(ifs_that_return_equal=_ifs_that_return_equal)
	if verbose:
		print('__eq__\n'+_def_eq)

	__eq__ = eval_def(_def_eq)
	__eq__.__name__ = '__eq__'
	__eq__.__qualname__ = '{}.{}'.format(name, __eq__.__name__)
	Class.__eq__ = __eq__

	return (Class,) + tuple(getattr(Class, variant_name) for variant_name in variant_names)





def uniq(xs: List[A]) -> List[A]:
	""" Like set(xs), but order-preserving.""" 
	seen = set()
	res = []
	for x in xs:
		if x not in seen:
			res.append(x)
			seen.add(x)
	return res



def eval_def(src: str) -> Fun[..., Any]:
	""" `exec` a function definition and return the function. """  
	temp_local_namespace  = {}
	exec(src, {}, temp_local_namespace)
	assert len(temp_local_namespace) == 1, "The source:\n\n{src}\n\ndefined more than one function. locals:\n {locals}".format(src=src, locals=temp_local_namespace)
	func = next(iter(temp_local_namespace.values()))
	assert func not in globals().values(), "Function leaked into globals"
	return func



UNSAFE_ACCESSORS_README = """
Thing._Foo_x   = Thing._0
Thing._Foo_y   = Thing._1
...

In contrast with the regular accessors like .x, .y, these will *NOT* check 
if they were called on the correct variant. They can be used for speed
if you know that the variant of a value.
Note, however, that they may silently return incorrect results
when used on an incorrect variant.

	>>> # class Thing = Foo(x, y, z) | Bar(a, z)
	>>>
	>>> # Correct - accessing Bar fields on a Bar value:
	>>>
	>>> # checked access - will error for variants that don't have the field
	>>> # (still very fast)
	>>> Bar(a=3, z=10).a 
	3
	>>> Bar(a=3, z=10).z
	10
	>>> # unchecked access - assumes the value is a Bar
	>>> # A bit faster, but can hide bugs 
	>>> Bar(a=3, z=10)._Bar_a
	3
	>>> # Note that even though the two variants share a field name,
	>>> # everything works correctly 
	>>> Bar(a=3, z=10)._Bar_z
	10
	>>> Foo(x=7, y=8, z=9)._Foo_z
	9
	>>>
	>>>
	>>> # Incorrect - accessing Foo fields on a Bar value
	>>>
	>>> # safe accessors will catch incorrect accesses:
	>>> Bar(a=3, z=10).x
	AttributeError(...)
	>>> Bar(a=3, z=10).y
	AttributeError(...)
	>>> # But unsafe ones won't:
	>>> Bar(a=3, z=10)._Foo_x	# assumes the value is a Foo, silently returns an incorrect result
	3
	>>> Bar(a=3, z=10)._Foo_y	# assumes the value is a Foo, silently returns an incorrect result
	10
	>>> Bar(a=3, z=10)._Foo_z 	# errors because of implementation details 
	AttributeError(...)
	>>>
	>>> # Incorrect - accessing Bar fields on a Foo value
	>>>
	>>> Foo(x=10, y=15).a 		# safe accessors will catch incorrect accesses
	AttributeError(...)
	>>> Foo(x=10, y=15)._Bar_a	# assumes the value is a Bar, silently returns an incorrect result
	10
"""




def main():
	Void, = untyped_union('Void', [], verbose=True)
	print(dir(Void))
	print('\n\n')
	# Void has no constructors, so it can't be instantiated.
	# Mostly useless, but the fact that it works gives me a certain peace of mind about the codegen :)
	# (inspired by Haskell, just like this whole module)

	(Thing,
		Foo,
		Bar,
		Zip,
		Hop) = untyped_union(
	'Thing',
	[
		('Foo', ['x', 'y',]),
		('Bar', ['y',     ]),
		('Zip', ['hey',   ]),
		('Hop', []         ),
	],
	 verbose=True,
	)

	print('__name__    : ', Thing.__name__)
	print('__qualname__: ', Thing.__qualname__)
	print('__module__  : ', Thing.__module__)
	# print('__doc__:', Thing.__doc__, sep='\n')
	# help(Thing)
	print('_positional_descriptors:', getattr(Thing, '_positional_descriptors', None))
	print(dir(Thing))
	
	foo = Thing.Foo(3, 5)
	bar = Thing.Bar("nice")
	zip = Thing.Zip(15.234)
	hop = Thing.Hop()

	print("Attribute access:")
	all_variant_fields = uniq( sum((Thing._variant_fields[variant] for variant in Thing._variants), ()) )

	for val in ('foo', 'bar', 'zip', 'hop'):
		val_ = eval(val)
		print("\t{}".format(val_))
		for field in all_variant_fields:
			should_work = (field in Thing._variant_fields[val_.variant])
			expr = "{val}.{field}".format(**locals())
			try:
				res = eval(expr)
				did_work = True
			except AttributeError as e:
				res = e
				did_work = False

			print(
				"\t\t{should}{did} {expr:<10}: {res!r}".format(
					expr=expr, res=res,
					should={True: '+', False: '-'}[should_work],
					did={True: '+', False: '-'}[did_work]
				)
			)
			# print()
		expr = '{val}.{bad}'.format(val=val, bad=str.join('', all_variant_fields))
		try: res = eval(expr)
		except AttributeError as e: res = e
		print(
			"\t{expr:<10}: {res!r}".format(
				expr=expr, res=res,
			)
		)
		print()
		print()




	print()
	print(foo, bar, zip, hop, sep='\n')
	# Thing._variant_id.__set__(foo, 5)
	print("x==x:", foo==foo, bar==bar, zip==zip, hop==hop)
	print("V(*args) == V(*args):", Thing.Foo(3,5) == Thing.Foo(3,5))
	print("V(*args1) == V(*args2):", Thing.Foo(3,5) == Thing.Foo(0,10))
	print("X(*args) == Y(*args)", Thing.Bar(3) == Thing.Zip(3))
	print()
	foo2 = foo._copy()
	print("x, x.copy(), x is x.copy():", foo, foo2, foo is foo2, sep=', ')
	bar2 = bar._copy()
	print("x, x.copy(), x is x.copy():", bar, bar2, bar is bar2, sep=', ')
	zip2 = zip._copy()
	print("x, x.copy(), x is x.copy():", zip, zip2, zip is zip2, sep=', ')
	hop2 = hop._copy()
	print("x, x.copy(), x is x.copy():", hop, hop2, hop is hop2, sep=', ')
	bar2 = bar.replace(y="better")
	print("replace:", bar, bar2)
	print("x.is_X()", foo.is_Foo(), bar.is_Bar(), zip.is_Zip())
	print("x.is_Y()", foo.is_Bar(), bar.is_Zip(), zip.is_Foo())

	try: res = bar.replace(blah_blah_blah=5)
	except Exception as e: res = e
	print("bad replace 1:", bar, res)

	try: res = bar.replace(_0=5)
	except Exception as e: res = e
	print("bad replace 2:", bar, res)

	try: res = bar.replace(_variant_id=5)
	except Exception as e: res = e
	print("bad replace 2:", bar, res)

	# del foo._Foo_y
	# print(foo)

	# foo._Foo_y = 10
	# print(foo)

	# Profiling

	import timeit
	from uniontype import untyped_union as untyped_union_tuple

	Thing2, *_ \
	= untyped_union_tuple(
	'Thing2', [
		('Foo', ('x', 'y',)),
		('Bar', ('y',)),
		('Zip', ('hey',)),
	])


	create_3_variants = """
foo = Thing.Foo(3, 5)
bar = Thing.Bar("nice")
zip = Thing.Zip(15.234)
"""
	create_3_variants_kwargs = """
foo = Thing.Foo(x=3, y=5)
bar = Thing.Bar(y="nice")
zip = Thing.Zip(hey=15.234)
"""

	access_attributes = """
x = foo.x
# y = foo.y
# y = bar.y
# z = zip.hey
"""
	unsafe_access_attributes = """
x = foo._Foo_x
# y = foo._Foo_y
# y = bar._Bar_y
# z = zip._Zip_hey
"""

	replace_all_attributes = """
foo2 = foo.replace(x=4)
# foo2 = foo.replace(x=4, y=6)
# bar2 = bar.replace(y="nicer")
# zip2 = zip.replace(hey=3.141592)
"""

	copy = """
foo2 = foo._copy()
# bar2 = bar._copy()
# zip2 = zip._copy()
"""
	# make the classes accessible to timeit
	# (they're created within `main()`, so they're not visible otherwise)
	globals()['Thing']  = Thing
	globals()['Thing2'] = Thing2

	slot_union_setup  = "from __main__ import Thing"
	tuple_union_setup = "from __main__ import Thing2 as Thing"


	n_timing_repetitions = 100001

	tests = (
		('slot_union_create_3',          create_3_variants,        slot_union_setup),
		('tuple_union_create_3',         create_3_variants,        tuple_union_setup),

		# ('slot_union_create_3_kwargs',   create_3_variants_kwargs, slot_union_setup),
		# ('tuple_union_create_3_kwargs',  create_3_variants_kwargs, tuple_union_setup),

		('slot_union_access_all',        access_attributes,        slot_union_setup +create_3_variants),
		('tuple_union_access_all',       access_attributes,        tuple_union_setup+create_3_variants),
		('slot_union_unsafe_access_all', unsafe_access_attributes, slot_union_setup +create_3_variants),

		('slot_union_copy',              copy,                     slot_union_setup +create_3_variants),
		('tuple_union_copy',             copy,                     slot_union_setup +create_3_variants),

		('slot_union_replace_all_attributes',          replace_all_attributes,        slot_union_setup +create_3_variants),
		('tuple_union_replace_all_attributes',         replace_all_attributes,        tuple_union_setup+create_3_variants),
	)
	print("Profiling")
	for (name, code, setup) in tests:
		time_usec = timeit.timeit(
			code,
			setup=setup,
			number=n_timing_repetitions
		) * 1000000 / n_timing_repetitions
		print('\t{name}:\t{time_usec:.2f} usec'.format(**locals()))

if __name__ == '__main__':
	main()


