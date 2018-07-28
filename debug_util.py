import glfw
import imgui as im
import math

from collections import (
	OrderedDict, defaultdict,
	deque,
	namedtuple,
)

from typing import (
	Any, 
	Dict, Sequence, Optional, Tuple, Deque, List,
)
from utils.types import (
	A,
	OrderedDict_,
	Fun, 
	IO_, IMGui,
)

from imgui_widget import window #, group, child

from utils import (
	uniform_dict_type, uniform_sequence_type, is_sequence_uniform,
	dict_to_function,
	get_mouse_position,
	parts_of_len,
)

from functools import reduce
import traceback

from flags import DEBUG 

# types
Debug = IO_ # type of things that log stuff to debugging
RangeId = str

# PointPlace = START | END 
PointPlace = bool
START = True # type: PointPlace
END   = False   # type: PointPlace

# PointId = PointId(RangeId, PointPlace)
PointId = namedtuple('PointId', ['range_id', 'point_place'])

range_start = lambda range_id: PointId(range_id, START) 
range_end   = lambda range_id: PointId(range_id, END)
Range = lambda range_id: (range_start(range_id), range_end(range_id))



TIME_N_POINTS_STORED = 10


debug_dict = None

def debug_initialize():
	global debug_dict

	debug_dict = OrderedDict(
		range_duration_histories_ms={},
		times_current_frame_ms=[],

		values=OrderedDict(),
		dicts=OrderedDict(),
		sequences=OrderedDict(),
		crash=None
	)





def debug_log_time(point_id: PointId, time_s=None) -> Debug[None]:
	""" `time` is GLFW time (in seconds) """
	if not DEBUG:
		return

	if time_s == None:
		time_ms = glfw.get_time() * 1000 # convert to ms
	else:
		time_ms = time_s * 1000 # convert to ms

	# disabled for speed
	# if m_debug_dict != None and 'times_current_frame' in m_debug_dict:
	# 	debug_dict = m_debug_dict
	# 	times_current_frame = debug_dict['times_current_frame']
	# 	times_current_frame.append((point_name, time))

	debug_dict['times_current_frame_ms'].append((point_id, time_ms))




def debug_log(name: str, val: A) -> Debug[None]:
	if not DEBUG:
		return
	debug_dict['values'][name] = val



def debug_log_dict(name: str, dictionary: Dict[A, Any]) -> Debug[None]:
	if not DEBUG:
		return
	debug_dict['dicts'][name] = dictionary


def debug_log_seq(name: str, seq: Sequence[A]) -> Debug[None]:
	if not DEBUG:
		return
	debug_dict['sequences'][name] = seq

def debug_log_crash(origin: str, cause, exception: Exception) -> Debug[None]:
	if not DEBUG:
		return
	debug_dict['crash'] = {'origin': origin, 'cause': cause, 'exception': exception}


def debug_window() -> IMGui[None]:
	with window(name="debug"):
		debug_window_draw_start_t_s = glfw.get_time()

		if debug_dict['crash'] is not None:
			origin    = debug_dict['crash']['origin']
			cause     = debug_dict['crash']['cause']
			exception = debug_dict['crash']['exception']
			with window(name="Crash report"):
				im.text('Exception raised during `{}`. State rolled back'.format(origin))
				im.text('Caused by:')
				im.text('\t'+repr(cause))

				im.text('\n'+ str(exception.__cause__) if exception.__cause__ is not None else '')
				for line in traceback.format_tb(exception.__traceback__):
					im.text(line)
				im.text("{}: {}".format(type(exception).__qualname__, str.join(', ', map(repr, exception.args) )) )

				if im.button('close'):
					debug_dict['crash'] = None



		# print some general app state
		# im.text("actions: "+str(frame_actions))
		im.text("mouse:   "+str(get_mouse_position()))
		im.text("click:   "+str(im.is_mouse_clicked(button=0)))
		im.text("down:    "+str(im.is_mouse_down(button=0)))
		im.text("cl+down: "+str(im.is_mouse_clicked(button=0) and im.is_mouse_down(button=0)))
		im.text("drag:    "+str(im.is_mouse_dragging(button=0)))
		im.text("drag-d:  "+str(im.get_mouse_drag_delta()))
		im.new_line()

		# print the avg durations of ranges set with `debug_log_time`
		show_avg_durations_of_recorded_ranges()

		# print the values in dicts logged with `debug_log_dict`
		for name, sequence in debug_dict['sequences'].items():
			im.new_line()
			show_sequence(sequence, name=name)

		# print the values in dicts logged with `debug_log_dict`
		for name, dictionary in debug_dict['dicts'].items():
			im.new_line()
			# d = order_dict_by_key(stringify_keys(flatten_dict(dictionary)))

			show_varied_dict(dictionary, name=name)


		# print all other values in debug (set with `debug_log`)
		im.new_line()
		show_varied_dict(debug_dict['values'])


		# print how long it took to draw the debug window (hehe)
		debug_window_draw_end_t_s = glfw.get_time()
		debug_window_draw_dur_ms = (debug_window_draw_end_t_s - debug_window_draw_start_t_s) * 1000
		im.new_line()
		im.text("drawing debug took {:4.1f} ms".format(debug_window_draw_dur_ms))





def debug_post_frame() -> Debug[None]:

	times_current_frame_ms = debug_dict["times_current_frame_ms"]
	range_duration_histories_ms = debug_dict['range_duration_histories_ms']

	fresh_logged_times = OrderedDict(times_current_frame_ms)
	_debug_clear_times()

	fresh_logged_durations = logged_times_to_durations(fresh_logged_times)

	changed_range_duration_names = update_stored_durations(range_duration_histories_ms, fresh_logged_durations)
	changed_range_duration_histories_ms = OrderedDict( (name, range_duration_histories_ms[name])
														for name in changed_range_duration_names)
	debug_dict['range_duration_histories_ms_updated_this_frame'] = changed_range_duration_histories_ms




def _debug_clear_times() -> Debug[None]:
	debug_dict['times_current_frame_ms'].clear()



def show_avg_durations_of_recorded_ranges() -> IMGui[None]:
	range_duration_histories_ms_updated_this_frame = debug_dict['range_duration_histories_ms_updated_this_frame']
	avg_range_durations_ms_updated_this_frame = average_durations(range_duration_histories_ms_updated_this_frame)
	show_durations(avg_range_durations_ms_updated_this_frame)



def show_durations(durations_ms: OrderedDict_[RangeId, float]) -> IMGui[None]:
		
	show_uniform_dict(durations_ms, value_format_string="{:5.1f} ms")
	



# formatting keys

def default_key_format_string_for_len(len: int) -> str:
	 return "{:>" + str(len) + "s}: "


# formatting_values

default_value_format_string = "{}"

default_value_format_string_for_type_dd = defaultdict(lambda: default_value_format_string)
default_value_format_string_for_type = dict_to_function(default_value_format_string_for_type_dd)

def debug_set_type_format_string(t: type, fmt_string: str) -> IO_[None]:
	default_value_format_string_for_type_dd[t] = fmt_string

debug_set_type_format_string(float, "{:5.1f}")



NESTED_VALUE_INDENT = 4


def show_varied_dict(dictionary: Dict[str, Any],
					 key_format_string_for_len:    Fun[[int], str ] = default_key_format_string_for_len,
					 value_format_string_for_type: Fun[[type], str] = default_value_format_string_for_type,
					 name=None) -> IMGui[None]:
	dict_str = varied_dict_to_str(dictionary,
								  key_format_string_for_len=   key_format_string_for_len,
								  value_format_string_for_type=value_format_string_for_type)
	if name == None:
		im.text( dict_str )
	else:
		im.text( name_and_multiline_str(name, dict_str) )





def varied_dict_to_str(dictionary: Dict[A, Any],
					   key_format_string_for_len:    Fun[[int], str ] = default_key_format_string_for_len,
					   value_format_string_for_type: Fun[[type], str] = default_value_format_string_for_type
					   ) -> str:
	dictionary = dictionary if is_dictlike(dictionary) else to_dictlike(dictionary) 
	assert is_dictlike(dictionary)

	if len(dictionary) == 0:
		return '_'
	else:
		# max_key_len = max(  (len(name) for name in dictionary.keys())  , default=0)
		# key_format_string = key_format_string_for_len(max_key_len)
		# im.new_line()
		sorted_dictionary = order_and_stringify_keys(dictionary)

		# reprs = (key_format_string.format(k) + value_format_string_for_type(type(v)).format(v)
		reprs = (k + ': ' + value_format_string_for_type(type(v)).format(v)
				 if is_not_mapping(v)
				 else k + ':\n' \
 					  + indent_multiline_str(
 					  		varied_dict_to_str(
 					  			to_dictlike(v),
 							 	key_format_string_for_len,
 							 	value_format_string_for_type
 							 ),
 					  		NESTED_VALUE_INDENT
 					  	)

				 for k, v in sorted_dictionary.items())
		return str.join('\n',  reprs)                                             




DefaultValueFormatStringForTypeOfValue = None # sentinel value used in `show_uniform_dict` and `uniform_dict_to_str`







def show_uniform_dict(dictionary: Dict[str, A],
					  key_format_string_for_len: Optional[ Fun[[int], str] ] = default_key_format_string_for_len,
					  value_format_string:       str                         = DefaultValueFormatStringForTypeOfValue) -> IMGui[None]:
	"""
	Note: See `uniform_dict_to_str`'s docstring for explanation
	of the default value for `value_format_string`
	"""
	im.text( uniform_dict_to_str(dictionary,
								 key_format_string_for_len=key_format_string_for_len,
								 value_format_string=value_format_string             ) )



def uniform_dict_to_str(dictionary: Dict[str, A],
					    key_format_string_for_len: Fun[[int], str] = default_key_format_string_for_len,
					    value_format_string:       str             = DefaultValueFormatStringForTypeOfValue) -> str:
	""" 
	Note: The default value of `value_format_string` is actually
	default_value_format_string_for_type[ uniform_dict_type(dictionary) ]`
	But python doesn't let us do that, so we use
	`DefaultValueFormatStringForTypeOfValue (=None)` as a sentinel value.
	(default params are evaluated at definition time, and our desired default value
	 can only be computed at run time)
	"""

	if len(dictionary) == 0:
		return ''
	else: # dictionary has values
		if value_format_string == DefaultValueFormatStringForTypeOfValue:
			dict_value_type = uniform_dict_type(dictionary)
			value_format_string = default_value_format_string_for_type[dict_value_type]

		max_key_len = max(  (len(name) for name in dictionary.keys())  , default=0)
		key_format_string = key_format_string_for_len(max_key_len)

		return str.join('\n',  (  key_format_string.format(k) + value_format_string.format(v)
							      for k, v in dictionary.items()  )                           ) 
	

def show_sequence(seq: Sequence[A], name: str = None) -> IMGui[None]:
	seq_str = sequence_to_str(seq)

	if name == None:
		im.text(seq_str)
	else:
		im.text( name_and_multiline_str(name, seq_str) )




def sequence_to_str(seq: Sequence[A],
	                value_format_string: str = DefaultValueFormatStringForTypeOfValue) -> str:
	if len(seq) == 0:
		return ''
	else:
		if value_format_string == DefaultValueFormatStringForTypeOfValue:
			sequence_value_type = uniform_sequence_type(seq)
			value_format_string = default_value_format_string_for_type[sequence_value_type]
		
		rows = parts_of_len(seq, len=3)
		row_to_str = lambda row: str.join('  ', (value_format_string.format(x) for x in row))
		row_strs = (row_to_str(row) for row in rows)
		return str.join('\n', row_strs)
	


def name_and_multiline_str(name: str, multiline_str: str) -> str:
	return name + ':' + '\n' + indent_multiline_str(multiline_str, NESTED_VALUE_INDENT)


def indent_str(string: str, indent: int) -> str:
	indent_n = indent
	assert indent_n > 0, "Indent value must be nonnegative (is {})".format(indent_n)
	return ' ' * indent_n + string


def indent_multiline_str(multiline_str: str, indent: int) -> str:
	indent_n = indent
	assert indent_n > 0, "Indent value must be nonnegative (is {})".format(indent_n)
	lines = multiline_str.split('\n')
	return str.join('\n',  (indent_str(line, indent_n) for line in lines)  )




def logged_times_to_durations(fresh_logged_times: OrderedDict_[Tuple[str, str], float]) -> OrderedDict_[str, Tuple[float, float]]:
	fresh_logged_range_names = set()
	fresh_logged_range_names_ordered = []
	for (range_name, _) in fresh_logged_times.keys():
		if range_name not in fresh_logged_range_names:
			fresh_logged_range_names_ordered.append(range_name)
		fresh_logged_range_names.add(range_name)

	fresh_logged_durations = OrderedDict( (range_name,  fresh_logged_times[(range_name, END)]
											            - fresh_logged_times[(range_name, START)])
							              for range_name in fresh_logged_range_names_ordered         )
	return fresh_logged_durations



def update_stored_durations(durations_ms: IO_[ Dict[str, Optional[Deque[float]]] ],
							fresh_logged_durations: OrderedDict_[str, Tuple[float, float]]) -> IO_[List[str]]:

	fresh_logged_range_names         = fresh_logged_durations.keys()
	fresh_logged_range_names_ordered = [name for (name, _) in fresh_logged_durations.items()]

	already_tracked_range_names = durations_ms.keys()
	untracked_range_names = fresh_logged_range_names - already_tracked_range_names
	updated_tracked_range_names = fresh_logged_range_names & already_tracked_range_names
	not_updated_tracked_range_names = already_tracked_range_names - updated_tracked_range_names
	updated_tracked_range_names_ordered = [name for name in fresh_logged_range_names_ordered if name in updated_tracked_range_names]
	# add all untracked ranges' durations to durations_ms
	for range_name in untracked_range_names:
		durations_ms[range_name] = deque([fresh_logged_durations[range_name]])

	for range_name in not_updated_tracked_range_names:
		durations_ms[range_name] = None

	# update the durations
	for range_name in updated_tracked_range_names:
		range_durations = durations_ms[range_name]
		if range_durations != None:  # got recent updates
			range_durations.append(fresh_logged_durations[range_name])
			if len(range_durations) > TIME_N_POINTS_STORED:
				range_durations.popleft()
				assert len(range_durations) == TIME_N_POINTS_STORED, "stored {}, should be {}".format(len(range_durations), TIME_N_POINTS_STORED)
		else:  # was not-updated recently:
			durations_ms[range_name] = deque([fresh_logged_durations[range_name]])

	return updated_tracked_range_names_ordered





def average_durations(range_duration_histories_ms: Dict[str, Sequence[float]]) -> Dict[str, float]:
	# compute the average durations of all the durations that got updated
	avgs = { range_name: math.fsum(range_duration_histories_ms[range_name]) \
						 / len(range_duration_histories_ms[range_name])
		     for range_name in range_duration_histories_ms
		     if range_duration_histories_ms[range_name] != None               }

	return avgs






def is_namedtuple(x): return isinstance(x, tuple) and hasattr(x, '_asdict')

def is_union(x): return is_namedtuple(x) and hasattr(x, 'id__') and hasattr(x, 'val__')

def is_dictlike(x): return hasattr(x, 'keys') and hasattr(x, 'values')
def is_not_dictlike(x): return not is_dictlike(x)

def is_mapping(x): return is_dictlike(x) or is_namedtuple(x) or is_union(x)
def is_not_mapping(x): return not is_mapping(x)

def to_dictlike(x): 
	assert is_mapping(x)
	if is_union(x):
		res = OrderedDict()
		res['@'] = x.get_variant_name()
		res.update(x.as_dict())
		return res

	if is_namedtuple(x):
		res = OrderedDict()
		res['#'] = type(x).__name__
		res.update(x._asdict())
		return res
		
	elif is_dictlike(x):
		return x
	else:
		return x




def order_and_stringify_keys(d):
	if len(d) == 0:
		return d

	if type(d) != OrderedDict: # no ordering yet
		d = order_dict_by_key(d)
		
	if type(list(d.keys())[0]) != str:
		d = stringify_ordered_dict_keys(d)
	
	return d


def stringify_ordered_dict_keys(d):
	return OrderedDict([(str(k), v) for (k, v) in d.items()])

def order_dict_by_key(d: Dict[str, A]):
	return OrderedDict(sorted([(k, v) for (k, v) in d.items()], key=lambda p: p[0]))


# def dict_union(a, b):
# 	res = {}
# 	res.update(a)
# 	res.update(b)
# 	return res

# def dict_union_all(ds): return reduce(dict_union, ds, initial={})
	
# def filter_dict(pred, d): return {k: v for (k, v) in d.items() if pred(v)}

# # fnd({'a': 5}) -> {'a': 5}
# # fnd({'a': 5, 'b': {'x': 5, 'y': 7} }) -> {'a': 5. 'b.x': 5, 'b.y': 7}

# # fnd -> {'a.x': 5, 'a.y': 7, 'b.x': 5, 'b.y': 7}({'a': {'x':5, 'y': 7},
# #      'b': {'x': 5, 'y': 7} })

# # fnd({'a': {'x':5, 'y': 7, 'd': {'x': 10} },
# #      'b': {'x': 5, 'y': 7} }) -> {'a.x': 5, 'a.y': 7, 'a.d.x': 10, 'b.x': 5, 'b.y': 7}

# # { 'a': {'x':5, 'y': 7, 'd': {'x': 10} },   'b': {'x': 5, 'y': 7} }

# def flatten_dict(d):
# 	flat_items     = filter_dict(is_not_dictlike, d)
# 	dictlike_items = filter_dict(is_dictlike, d)
# 	if len(dictlike_items) == 0:
# 		assert all(is_not_dictlike(v) for (k, v) in d.items())
# 		return d
# 	else: # some items need flattening
# 		assert all(is_dictlike(v) for (k, v) in dictlike_items.items())
# 		flattened_dictlike_items = {k: flatten_dict(dct) for (k, dct) in dictlike_items.items()}
# 		assert all(is_not_dictlike(v) for (name, dct) in flattened_dictlike_items.items()
# 									     for (k, v) in dct.items())
# 		flattened = {name+'.'+str(k) : v for (name, dct) in flattened_dictlike_items.items()
# 										for (k, v) in dct.items()}

# 		res = dict_union(flat_items, flattened)
# 		assert all(is_not_dictlike(v) for (k, v) in res.items())
# 		return res




	
