from pyrsistent import l
from types_util import *
from util import get

class Store:
	def __init__(store, initial_state, update_fn):
		store.state = initial_state
		store.subscriptions = {}
		store.update_fn = update_fn
		store.cur_sub_id = 0

	def subscribe(store, sub_fun, path:Iterable[Any]=l()):
		"""
		Path - a list of indexes, to extract some nested bit of state.
		When the store's state changes, it will call
			`sub_fun( util.get(store.get_state(), path) )`
		"""


		sub_id = store.get_new_id()
		store.subscriptions[sub_id] = (sub_fun, path)

		def remove():
			del subscriptions[sub_id]
		return remove

	def get_new_id(store):
		sub_id = store.cur_sub_id
		store.cur_sub_id += 1
		return sub_id

	def update(store, action):
		store.state = store.update_fn(store.state, action)

	def dispatch(store, action):
		store.update(action)
		for sub_id, (sub_fun, path) in store.subscriptions.items():
			sub_fun( get(store.get_state(), path) )

	def get_state(store):
		return store.state