from typing import (Set, Any, Iterable, TypeVar, Optional, Sequence)

import inspect
import importlib
import builtins

from pathlib import (Path)
# import pathlib as p



from functools import reduce
import operator as op


A = TypeVar('A')
Module = type(inspect) # <class 'module'>  # any module would work here


def recursive_reload(module: Module, dir: Path, excluded: Sequence[str] = (), verbose=False, inject_versions=False) -> None:
	"""
	Reload `module`, its dependencies, their dependencies, etc.
	Dependencies are reloaded first to ensure every module gets the right version.

	`dir` is used to limit the scope of reloading - `recursive_reload` will only 
	touch modules from this directory. There's a useful helper: `current_module_dirpath()`
	Which uses `inspect` to get your modules directory. If you don't like that, there's
	also `module_dirpath(mod)`.
	NOTE: You can pass `dir=None`. In that case `recursive_reload` will try to reload
	any dependency it finds. In my experience it blew up on some stdlib modules.
	Unfortunately AFAIK there's no easy way to check if a module is in the stdlib,
	so we opted to just pass a directory.

	`excluded` is a sequence of names that will not be reloaded. You should pass
	the name of your main module here - the one that launched `run_reloadable_imgui_app`
	if you have a heavy module that never changes, but be careful -
	if you modify the module during runtime, the app won't see the changes. 
	"""
	excluded = excluded + (__name__,)
	done = set()

	def rec_rel(mod, current_depth=0) -> None:
		if verbose:
			indent = current_depth*'\t'
			print(indent + mod.__name__ + ("(won't reload)" if mod.__name__ in excluded else ""), flush=True)

		deps = direct_deps(mod, dir=dir)
		# first, recursively reload the dependencies
		for dep in deps:
			if dep not in done:
				rec_rel(dep, current_depth=current_depth+1)

			elif verbose: print(indent+'\t' + dep.__name__ + " (already reloaded)", flush=True)

		# then reload the module
		if mod.__name__ not in excluded:
			# tag the classes and routines in the module object with its version
			# (helps find reload-related bugs)
			if inject_versions:
				mod_reload_incarnation = getattr(mod, '__reload_incarnation__', 0)
				members = dict(inspect.getmembers(mod))
				for (name, obj) in members.items():
					if (not inspect.isbuiltin(obj)) and (inspect.isclass(obj) or inspect.isroutine(obj)) and obj.__module__ == mod.__name__:
						setattr(obj, '__reload_incarnation__', mod_reload_incarnation)

			importlib.reload(mod)

			if inject_versions: setattr(mod, '__reload_incarnation__', mod_reload_incarnation+1)

		done.add(mod)

	rec_rel(module)

	# print('Reloaded:', *('\t'+mod.__name__ for mod in done), sep='\n', flush=True)


# # Graph stuff - might be unnecessary

# from networkx import DiGraph
# import networkx as nx


# def dep_graph(module: Module, dir=None) -> DiGraph:
# 	graph = nx.DiGraph()
# 	done = set()

# 	def recursively_add(mod) -> None:
# 		graph.add_node(mod)
# 		deps = direct_deps(mod, dir=dir)
# 		for dep in deps:
# 			graph.add_edge(mod, dep)
# 			if dep not in done:
# 				recursively_add(dep)
# 		done.add(mod)

# 	recursively_add(module)
# 	return graph

# def all_deps_g(module: Module, dir=None):
# 	graph = nx.transitive_closure( dep_graph(module, dir=dir) )
# 	# nx.topological_sort(graph)  # - reloading order
# 	return list(graph.neighbors(module))






def direct_deps(module: Module, dir: Path = None) -> Set[Module]:
	"""
	Returns the set of the direct dependencies of the module,
	i.e. modules it imports. If a directory is specified, only modules
	in that directory (and its children) will be returned.
	"""
	assert inspect.ismodule(module)

	deps_i = None
	try:
		members = dict(inspect.getmembers(module))
		deps_i = filter(lambda m: m is not None and m is not module,
						map(inspect.getmodule, members.values()))
	except ImportError:
		deps_i = ()

	if dir is not None:
		dirpath = dir
		assert dirpath.is_absolute()
		assert dirpath.exists()
		assert dirpath.is_dir()

		return set(mod for mod in deps_i if is_module_in_dir(mod, dirpath))
	else:
		return set(deps_i)



def all_deps(module: Module, dir=None) -> Set[Module]:
	"""
	Returns the set of dependencies of the module, and their dependencies,
	And so on all the way down, i.e. the transitive closure of dependecy.
	"""

	deps = direct_deps(module, dir=dir)
	return deps | union_all( all_deps(dep, dir=dir) for dep in deps )



def is_module_in_dir(module: Module, directory: Path) -> bool:
	assert directory.is_dir()
	dirpath = directory

	o_modpath = module_abspath(module)
	if o_modpath is None:
		return False
	else:
		modpath = o_modpath
		return dirpath in modpath.parents


def module_dirpath(module: Module) -> Optional[Path]: return module_abspath(module).parent


def module_abspath(module: Module) -> Optional[Path]:
	assert inspect.ismodule(module), repr(module)

	try:   return Path(inspect.getfile(module))
	except TypeError: return None # builtin module



def current_module_dirpath() -> Path:
	""" Returns the dirpath of the file it was called from. """
	parent_frame = inspect.stack()[1].frame
	return Path(inspect.getfile(parent_frame)).parent



def current_module_abspath() -> Path:
	"""
	Returns the abspath of the file it was called from.
	__path__ doesn't always work, as it sometimes returns ".../foo.pyc"
	instead of ".../foo.py" (So I heard)
	"""
	parent_frame = inspect.stack()[1].frame
	return Path(inspect.getfile(parent_frame))



def union_all(sets: Iterable[Set[A]]) -> Set[A]:
	return reduce(op.__or__, sets, set())


def cat(expr, *exs):
	if exs == ():
		exs = (Exception,)

	try: return expr()
	except exs: return None


def catf(f, *exs):
	if exs == ():
		exs = (Exception,)

	def safe_f(*args, **kwargs):
		try: return f(*args, **kwargs)
		except exs: return None

	return safe_f


import sys

def all_modules(dir=None):
	modules_iter = filter(inspect.ismodule, sys.modules.values())
	# It's really weird that things that aren't modules can go in sys.modules, but they can... (see `typing.re`, a class)

	if dir is not None:
		dirpath = dir
		assert dirpath.is_absolute()
		assert dirpath.exists()
		assert dirpath.is_dir()

		return set(mod for mod in modules_iter if is_module_in_dir(mod, dirpath))
	else:
		return set(modules_iter)