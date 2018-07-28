
from collections import namedtuple
from typing import Any, Tuple, List, Callable, Union
import typing
import sys
# from functools import partial

Fun = Callable




def untyped_union(
		type_name: str, variant_specs: List[ Tuple[str, List[str]] ],
		allow_zero_constructors=False,
		_module_name=None) -> List[Any]:
	"""
	Wraps `union`, giving every field type `Any`.
	See the documentation for `union` for more.
	"""

	variant_specs = [    (variant_name, [(attr_name, Any) for attr_name in attr_names])
					 for (variant_name, attr_names)
					 in variant_specs]

	# module name

	# `union` relies on sys._getframe to inspect the caller's frame and
	# get the right module name. That won't work if untyped_union calls it,
	# since the caller's frame will be located in this module.
	# So we have to get the module name here, and pass it down.				 
	# See the "module name" section in `union`'s definition for more.
	if _module_name is None:
		try:
			_module_name = sys._getframe(1).f_globals.get('__name__', '__main__')
		except (AttributeError, ValueError):
			_module_name = __name__ # fallback - this module


	return union(type_name, variant_specs,
				 typecheck=False,
				 allow_zero_constructors=allow_zero_constructors,
				 _module_name=_module_name)




def union(
		type_name: str, variant_specs: List[  Tuple[str, List[Tuple[str, type]] ]  ],
		typecheck=True,
		allow_zero_constructors=False,
		_module_name=None
		) -> List[Any]:
	"""
	Analogous to the namedtuple function.


	Creating a type:

	Example: Foo{ r } | Bar{ x, y } | BazBaz {}
	- Foo has one attribute r,
	- Bar has two attributes x, y
	- BazBaz has no attributes

	>>> Example, \
		Foo, \
		Bar, \
		BazBaz, \
		\
		= uniontype_typed(
			'Example', [
				 ('Foo',    [('r', int)            ]),
				 ('Bar',    [('x', int), ('s', str)]),
				 ('BazBaz', [                      ]),
			]
		  )
	>>> x  = Foo(5);    y  = Bar(2,   'abc');    z  = BazBaz()
	>>> x2 = Foo(r=5);  y2 = Bar(x=2, s='abc');  z2 = BazBaz()
	>>>
	>>> x == x2  and  y == y2  and  z == z2
	True
	>>> type(x) == Example  and  type(y) == Example  and  type(z) == Example
	True
	>>>

	Pattern matching

	>>> a = Bar(1, 5)
	>>> if   a.is_Foo():
	>>>     r = a.r
	>>> 	print('a is a Foo')
	>>> elif a.is_Bar():
	>>> 	x, y = a.as_tuple()
	>>>     print('a is a Bar')
	>>> elif a.is_BazBaz():
	>>> 	print('a is a BazBaz')
	

	Classes returned by `union` are picklable if the attributes are picklable.


	`_module_name`: Used internally. (untyped_union calls union)
		The user normally doesn't have to pass anything here -
		`union` will figure out the right module name through introspection.
		(see the "module name" section in this function's source to see how it does that)
		If it doesn't for some reason, feel free to pass it the correct module name. 
		The resulting class will have its __module__ set to the value of _module_name.
		Necessary for nice type names and for pickling to work.

	"""
	if not allow_zero_constructors and len(variant_specs) == 0:
		raise Exception("No variants specified for " + type_name)


	variant_names      = [variant_name for (variant_name, attr_names_and_types) in variant_specs]
	variant_attr_specs = [attr_names_and_types for (variant_name, attr_names_and_types) in variant_specs]
	variant_attr_names = [[attr_name for (attr_name, attr_type) in attr_names_and_types] for attr_names_and_types in variant_attr_specs]
	# variant_attr_types = [[attr_type for (attr_name, attr_type) in attr_names_and_types] for attr_names_and_types in variant_attr_specs]
	variant_ids = range(len(variant_names))
	

	# for 
	# for name in variant_names:
	# 	if type(name) != str:
	# 		raise TypeError('Variant names must be strings, got {val}: {val_t}' \
	# 						 .format(val=repr(name), val_t=type(name)))
	# for attr_names in variant_attr_names:
	# 	for attr_name in attr_names:
	# 		if type(attr_name) != str:
	# 			raise TypeError('Attribute names must be strings, got {val}: {val_t}' \
	# 							 .format(val=repr(attr_name), val_t=type(attr_name)))
			
	UserUnionType = namedtuple(type_name, ['id__', 'val__'])

	# add typing type annotation (doesn't seem to work :/)
	# typing_type = Union[  tuple( Tuple[ tuple(attr_types) ] for attr_types in variant_attr_types )  ]

	# UserUnionTypeBase = namedtuple(type_name, ['id__', 'val__'])

	# class UserUnionType(UserUnionTypeBase):  # add typing type annotation here later?
	# 	pass
	


	# module name

	# Copied with modifications from collections.namedtuple, which has the same issue.

	# For pickling to work, the __module__ variable needs to be set to the __name__
	# of the module  where the union is created.
	# Bypass this step in environments where  sys._getframe is not defined  (Jython for example)
	# or sys._getframe is not  defined for arguments greater than 0 (IronPython).

	# note: `untyped_union` passes the correct module name to `union`.
	if _module_name is None:
		# caller of `union` didn't pass a module name - get the caller's module name
		try:
			_module_name = sys._getframe(1).f_globals.get('__name__', '__main__')
		except (AttributeError, ValueError):
			_module_name = __name__ # fallback - this module

	UserUnionType.__module__ = _module_name




	# string representation
	def __str__(x: UserUnionType) -> str:
		if x.id__ not in variant_ids:
			raise Exception("Illegal variant: Token(id={id}, val={val})"\
							 .format(**x._asdict()))
			
		for (variant_id, variant_name) in zip(variant_ids, variant_names):
			if x.id__ == variant_id:
				this_variant_attr_names = variant_attr_names[variant_id]
				attr_reprs = (name + '=' + repr(value)  for (name, value) in zip(this_variant_attr_names, x.val__))
				all_attrs_repr = str.join(', ', attr_reprs)
				return variant_name + '(' + all_attrs_repr + ')'

	UserUnionType.__str__ = __str__
	UserUnionType.__repr__ = __str__




	# add is_VariantName methods to UserUnionType

	def make_is_variant_name(variant_id: int):
		def is_variant_name(obj: UserUnionType) -> bool:
			return obj.id__ == variant_id
		return is_variant_name

	for (variant_id, variant_name) in zip(variant_ids, variant_names):
		setattr(UserUnionType, ('is_' + variant_name), make_is_variant_name(variant_id))





	# backing tuples

	def make_backing_tuple(variant_name: str, attr_names_and_types: List[Tuple[str, type]]):
		# Each variant gets a VariantNameVal namedtuple to store the values
		# it also stores the specified types in VariantNameVal._field_types
		name = '_'+variant_name+'Val'
		BackingTuple = typing.NamedTuple(name, attr_names_and_types)
		BackingTuple.__module__ = _module_name
		BackingTuple.__qualname__ = type_name + '.' + name
		return BackingTuple

	variant_backing_tuples = \
		[make_backing_tuple(variant_name, attr_names_and_types)
		 for (variant_name, attr_names_and_types) 
		 in variant_specs ]

	for BackingTuple in variant_backing_tuples:
		setattr(UserUnionType, BackingTuple.__name__, BackingTuple)



	# constructors

	def make_constructor(variant_id: int, variant_name: str, BackingTuple: type) -> type:

		def constructor(*args, **kwargs):

			# Reuse namedtuple's error checking and messages
			# Will throw a TypeError if
			#    - the number of parameters is wrong
			#    - an unexpected keyword arg was given)
			# Does not check the types! We do that later,
			#  if `union()` got the `typeckeck` parameter

			try:

				val__ = BackingTuple(*args, **kwargs)

			except TypeError as t_err:
				# err_text = t_err.args[0]
				# modified_err_text = _modified_constructor_err_text(type_name, variant_name, err_text)
				# # ^ helper defined at end of file
				raise t_err



			# typechecking

			if typecheck:
				specified_attr_types = BackingTuple._field_types

				for (attr_name, attr_val) in val__._asdict().items():
					specified_attr_type = specified_attr_types[attr_name]
					if specified_attr_type is not object and specified_attr_type is not Any and not isinstance(attr_val, specified_attr_type):
						raise TypeError(type_name+".{variant_name} constructor: attribute {attr_name} has specified type {specified_attr_type}, but is {arg}: {arg_type}" \
										 .format(variant_name=variant_name, attr_name=repr(attr_name),
												 specified_attr_type=specified_attr_type,
												 arg=repr(attr_val), arg_type=type(attr_val)))

			# constructor
			return UserUnionType(id__=variant_id, val__=val__)

		return constructor


	variant_constructors = \
		[make_constructor(variant_id, variant_name, BackingTuple)
		 for (variant_id, variant_name, BackingTuple) 
		 in zip(variant_ids, variant_names, variant_backing_tuples) ]


	# add the constructors to the created union type so the user can write TypeName.VariantName(foo, bar)

	for (variant_name, constructor) in zip(variant_names, variant_constructors):
		setattr(UserUnionType, variant_name, constructor)

	UserUnionType.variant_names = variant_names
	UserUnionType.variant_constructors   = variant_constructors
	UserUnionType.variant_backing_tuples = variant_backing_tuples



	# add attribute getters for each Variant's attr_names


	# Check what types an attr_name has in all variants
	
	# to know  the type of the property getter for `attr_name`
	# For example, if we have a class with two variants:
	#   Example = Foo(x: int) | Bar(x: str, s: str)
	# then the property getter Example.x has type (Example) -> Union[int, str]
	# because  `ex.x` can be either an int if `ex` is a `Foo` or a string if `ex` is a `Bar`. 

	# {
	#   'x': {0: int, 1: str},
	#   's': {1: str},
	# }

	all_attr_names = set( sum(variant_attr_names, []) )


	all_types_attr_name_can_have = {attr_name: set() for attr_name in all_attr_names}

	for BackingTuple in variant_backing_tuples:
		for (attr_name, attr_type) in BackingTuple._field_types.items():
			all_types_attr_name_can_have[attr_name].add(attr_type)




	def make_variant_attr_name_property(attr_name: str):
		# this_attr_types_in_variants = attr_name_to_types_in_variants[attr_name]
		# variants_that_have_this_attr_name = this_attr_types_in_variants[]
		# @property
		def attr_name_property(obj: UserUnionType) -> Union[ tuple(all_types_attr_name_can_have[attr_name]) ]:
			try:
				return getattr(obj.val__, attr_name)

			except AttributeError as a_err: # reuse namedtuple's error messages,  but change the text
				err_text = a_err.args[0]
				variant_name = obj.get_variant_name()
				modified_err_text = err_text.replace(variant_name+'Val', type_name+'.'+variant_name)
				raise AttributeError(modified_err_text)

		return attr_name_property


	for attr_name in all_attr_names:
		setattr(UserUnionType, attr_name,
				property(make_variant_attr_name_property(attr_name)))
		setattr(UserUnionType, 'get_' + attr_name,
				make_variant_attr_name_property(attr_name))



	# methods
	
	UserUnionType.is_same_variant = lambda obj1, obj2: obj1.id__ == obj2.id__
	UserUnionType.get_variant_name = lambda obj: variant_names[obj.id__]

	UserUnionType.as_tuple = lambda obj: tuple(obj.val__)
	UserUnionType.get_values = UserUnionType.as_tuple

	# reexport nameduple methods under different names
	UserUnionType.as_dict  = lambda obj: obj.val__._asdict()


	def replace(obj: UserUnionType, **replacements) -> UserUnionType:

		try:
			new_val__ = obj.val__._replace(**replacements) # this variant's BackingTuple

		except ValueError as val_err: # Reuse namedtuple's error messages, but change the text
			err_text = val_err.args[0]
			modified_err_text = type_name+'.'+obj.get_variant_name() + '.replace: ' + err_text
			raise ValueError(modified_err_text)
		
		# typechecking
		if typecheck:
			specified_attr_types = new_val__._field_types # this variant's BackingTuple's _field_types

			for (attr_name, attr_val) in replacements.items():
				specified_attr_type = specified_attr_types[attr_name]
				if type(attr_val) != specified_attr_type:
					raise TypeError(type_name+'.'+obj.get_variant_name()+".replace: Cannot set attribute {attr_name} with specified type {specified_attr_type} to {arg}: {arg_type}" \
									 .format(variant_name=obj.get_variant_name(), attr_name=repr(attr_name),
											 specified_attr_type=specified_attr_type,
											 arg=repr(attr_val), arg_type=type(attr_val)))

		# replacing
		return obj._replace(val__=new_val__)

	UserUnionType.replace = replace
	UserUnionType.set     = replace # alias
	UserUnionType.update  = replace # alias


	# # UserUnionType.__iter__ = lambda obj: obj.val__.__iter__() # can't do this - it breaks namedtuple's _asdict(), _replace(), _make(), and others
	# use as_tuple and iter over that instead.




	return [UserUnionType] + variant_constructors





def match(x, **variant_name_to_lamb):
	cls = type(x)
	for pat_name in variant_name_to_lamb.keys():
		if pat_name != '_':
			assert pat_name in cls.variant_names, "Pattern {var} is not a variant of class {cls}" \
												  .format(var=repr(pat_name), cls=cls)
	# first, try matching by variant name
	var_name = x.get_variant_name()
	o_var_expr = variant_name_to_lamb.get(var_name, None)
	if o_var_expr != None:
		return o_var_expr(*(x.as_tuple()))

	# if no match, try to find a wildcard pattern
	o_anything_expr = variant_name_to_lamb.get('_', None)
	if o_anything_expr != None:
		return o_anything_expr()

	else: # no wildcard pattern, so x doesn't match anything
		raise Exception("Unmatched pattern: " +repr(x))





# Example = nameduple('Example', ['x', 'y'])

Example, \
	Foo, \
	Bar, \
	BazBaz, \
	\
= union(
	'Example', [
		 ('Foo',    [('r', int)            ]),
		 ('Bar',    [('x', int), ('s', str)]),
		 ('BazBaz', [                      ]),
	]
  )

# z = match( BazBaz(),
# 		Foo=lambda r: 5,
# 		Bar=lambda x, y: x+1,
# 		BazBaz=lambda: 10
# 	)





Example, \
		Foo,\
		Bar,\
		BazBaz, \
\
= untyped_union(
	'Example', [
		 ('Foo',    ['r'     ]),
		 ('Bar',    ['x', 'y']),
		 ('BazBaz', [        ]),
	]
  )



# Helpers for modifying namedtuple error messages


def _modified_constructor_err_text(type_name: str, variant_name: str, err_text: str) -> str:
	# could probably be done way easier with regex
	# '__new__() takes 2 positional arguments but 3 were given'
	if err_text.count('__new__() takes ') == 1 \
		and err_text.count(' positional arguments but ') == 1 \
		and err_text.count(' were given') == 1:

		modified_err_text = _modified_positional_args_err_text(type_name, variant_name, err_text) # defined at the end of the file

	else:
		modified_err_text = err_text.replace('__new__()', type_name + '.' + variant_name + ' constructor')

	return modified_err_text


def _modified_positional_args_err_text(type_name, variant_name, err_text: str) -> str:
	# '__new__() takes 2 positional arguments but 3 were given'
	# could probably be done way easier with regex
	s_arg_numbers = err_text \
						.replace('__new__() takes ', '') \
						.replace(' positional arguments but ', ', ') \
						.replace(' were given', '') \
						.split(', ')

	arg_numbers = [int(s_num) for s_num in s_arg_numbers]
	correct_arg_numbers = [n-1 for n in arg_numbers]

	modified_err_text = type_name + '.' + variant_name \
						+ ' takes {} positional arguments but {} were given' \
							.format(*correct_arg_numbers)
	return modified_err_text