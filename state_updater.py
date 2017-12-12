


class StateProvider:
	"""
	A state provider is a mediator between 
	a store and Qt Widgets whose state depends on the store.
	(similar to a React Provider I think)
	Widgets subscribe to a state updater instead of the store,
	specifying which parts of the state they care about.
	state = {
		'foo': 1,
		'counters': {
			0: 15,
			1: 3
		}
	}
	
	prov = StateProvider()
	counter = BoxCounter(id=1)
	# counter cares about `state['counters'][1]`

	prov.subscribe(counter, path=['counters', 1])
	#						 ^ indexes into the state tree

	Now every time the state updates, counter.state will be set
	to `state['counters'][1]`.
	#TODO: optimize this so that only the parts that changed send updates
	"""
	def __init__(prov, store):
		this.store = store
		# TODO: add path subscribing to Store?
		# because this seems like it will kinda duplicate stuff with that

	def subscribe()
