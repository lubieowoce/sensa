class Store:
	def __init__(store, initial_state, update_fn):
		store.state = initial_state
		store.subscribers = {}
		store.update_fn = update_fn
		store.cur_sub_id = 0

	def subscribe(store, sub_fun):
		id = store.get_new_id()
		store.subscribers[id] = sub_fun

		def remove():
			del subscribers[id]
		return remove

	def get_new_id(store):
		id = store.cur_sub_id
		store.cur_sub_id += 1
		return id

	def update(store, action):
		store.state = store.update_fn(store.state, action)

	def dispatch(store, action):
		store.update(action)
		for id, sub_fun in store.subscribers.items():
			sub_fun()

	def get_state(store):
		return store.state