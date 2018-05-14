"""
This module defines some utility functions
for persisting state to disk and loading it back.
"""

from typing import (Iterable, Iterator, Any)
from types_util import (IO_)

import pickle


def dump_all(objs: Iterable[Any], file) -> IO_[None]:
	""" Write each object to the pickle file.
	Does not close the file """

	assert file.mode == 'wb', "File must be opened in write-binary ('ab') mode: " + repr(file)
	pickler = pickle.Pickler(file)
	for obj in objs:
		pickler.dump(obj)



def dump_append(obj: Any, file) -> IO_[None]:
	""" Append object to the pickle file.
	Does not close the file """
	assert file.mode == 'ab', "File must be opened in append-binary ('ab') mode: " + repr(file)
	pickle.dump(obj, file)



def load_all(file) -> Iterable[IO_[Any]]:
	""" Returns an iterator that yields successive unpickled objects from `file`.
	The file can be a normal pickle file, or a file where multiple
	pickled objects were appended.
	Does not close the file """
	assert file.mode == 'rb', "File must be opened in read-binary ('rb') mode: " + repr(file)
	unpickler = pickle.Unpickler(file)
	while True:
		try:
			yield unpickler.load()
		except EOFError:
			break

