import timeit
import types
from collections import namedtuple
from functools import partial
from eff import effectful, run_eff, ID, ACTIONS, eff_operation



def test_async_get_id(n):
	(_, res, id_) = run_id_async(get_n_ids_async(n), id_=0)
	# print(res, id_)

# async def get_n_ids_async(n: int):
# 	_get_id = get_id # perf: local lookup
# 	for _ in range(n):
# 		await _get_id()
async def get_n_ids_async(n: int):
	_get_id = get_id # perf: local lookup
	for _ in range(n):
		await GetId(('foo', 1, 2))

def test_sync_get_id(n):
	(res, eff_res) = run_eff(get_n_ids_sync, id=0, actions=[])(n)
	# print(res, eff_res[ID])

# @effectful(ID)
# def get_n_ids_sync(n: int):
# 	# assert n >= 0
# 	get_id = eff_operation('get_id')
# 	for _ in range(n):
# 		get_id()

@effectful(ACTIONS)
def get_n_ids_sync(n: int):
	# assert n >= 0
	emit = eff_operation('emit')
	for _ in range(n):
		emit(GetId(('foo', 1, 2)))


# class GetId:
# 	__slots__ = ('variant',)
# 	def __init__(self, variant):
# 		self.variant = variant
# 	# def __setattr__(cmd, name, value): raise Exception("Can't set, State is immutable")
# 	def __await__(self):
# 		"""
# 		This is needed so that the user can do
# 			id_ = await GetId()
# 		This way, the GetId request just gets passed to
# 		the runner function (e.g. `run_eff`).

# 		Note: this method contains a `yield`, so it returns
# 		a generator. Generators are iterators, so everything
# 		follows the async-stuff PEP.
# 		"""
# 		res = yield self
# 		return res

# class Id:
# 	__slots__ = ()
# 	# def __setattr__(cmd, name, value): raise Exception("Can't set, State is immutable")
# 	def __await__(self):
# 		"""
# 		This is needed so that the user can do
# 			id_ = await GetId()
# 		This way, the GetId request just gets passed to
# 		the runner function (e.g. `run_eff`).

# 		Note: this method contains a `yield`, so it returns
# 		a generator. Generators are iterators, so everything
# 		follows the async-stuff PEP.
# 		"""
# 		res = yield self
# 		return res

# class GetId(Id):
# 	__slots__ = ()
# 	def __repr__(get): return 'GetId()'

# get_id = GetId


def yield_(x):
	res = yield x
	return res

GetId = namedtuple('GetId', ['variant'])
GetId.__await__ = yield_

# Id = namedtuple('Id', ['variant', 'val'])
# _GetId = namedtuple('_GetId', [])

# def get_id(): return GetId(0) 
get_id = partial(GetId, 0)



def run_id_async(comp, id_):

	actions = []

	response = None
	try:
		# req = comp.send(None) # run comp until first await (request)
		req = comp.send(None) # run comp until first await (request)
	except StopIteration as done:
		# `comp` finished without making any requests
		return (done.value, id_)
	except BaseException:
		# error in `comp`
		raise

	while True:
		# assert isinstance(req, Id), "`Id` handler got non-Id request: " + repr(req)

		# if req.variant == 0:
		if True:
		# if type(req) == GetId:
			actions.append(req.variant)
			response = id_
			id_ += 1

		else: assert False, "`Id` handler got unknown command: " + repr(req)

		# either resume computation with response, and get the next request
		# or get the computation's result and return it along with current Id 
		try:
			req = comp.send(response)
		except StopIteration as done:
			# `comp` finished
			return ('ok', done.value, id_)
		except BaseException as e:
			return ('error', e, id_)


if __name__ == '__main__':

	n_timing_repetitions = 1001
	n_get_id_requests = 1000

	print('timing async...')
	time_ms = timeit.timeit(
		'test_async_get_id({})'.format(n_timing_repetitions),
		setup='from __main__ import test_async_get_id',
		number=n_timing_repetitions
	) * 1000 / n_timing_repetitions
	print('async get_id x', n_get_id_requests ,'took', round(time_ms, 2), 'ms (', round(time_ms/n_get_id_requests, 5), 'ms per get_id)')
	time_async_ms = time_ms

	print('timing sync...')
	time_ms = timeit.timeit(
		'test_sync_get_id({})'.format(n_timing_repetitions),
		setup='from __main__ import test_sync_get_id',
		number=n_timing_repetitions
	) * 1000 / n_timing_repetitions

	print( 'sync get_id x', n_get_id_requests ,'took', round(time_ms, 2), 'ms (', round(time_ms/n_get_id_requests, 5), 'ms per get_id)')
	time_sync_ms = time_ms

	print('an async get_id takes', round(time_async_ms/time_sync_ms, 1), 'times longer')