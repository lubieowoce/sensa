import glfw
import imgui as im
import math

from collections import (
	OrderedDict, defaultdict,
	deque,
	namedtuple,
)


from types_util import *
from imgui_widget import (window, group, child)

from util import (
	uniform_dict_type, uniform_sequence_type,
	dict_to_function,
	get_mouse_position,
	parts_of_len,
)


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



debug_dict = OrderedDict(
	range_duration_histories_ms={},
	times_current_frame_ms=[],

	values=OrderedDict(),
	dicts=OrderedDict(),
	sequences=OrderedDict(),
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



def debug_log_dict(name: str, dictionary: Dict[str, Any]) -> Debug[None]:
	if not DEBUG:
		return
	debug_dict['dicts'][name] = dictionary


def debug_log_seq(name: str, seq: Sequence[A]) -> Debug[None]:
	if not DEBUG:
		return
	debug_dict['sequences'][name] = dictionary




def debug_window() -> IMGui[None]:
	with window(name="debug"):
		debug_window_draw_start_t_s = glfw.get_time()


		# print some general app state
		# im.text("actions: "+str(frame_actions))
		im.text("mouse:   "+str(get_mouse_position()))
		im.text("drag-d:  "+str(im.get_mouse_drag_delta()))
		im.text("drag:    "+str(im.is_mouse_dragging(button=0)))
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
			show_varied_dict(dictionary, name=name)


		# print all other values in debug (set with `debug_log`)
		im.new_line()
		show_varied_dict(debug_dict['values'])


		# print how long it took to draw the debug window (hehe)
		debug_window_draw_end_t_s = glfw.get_time()
		debug_window_draw_dur_ms = (debug_window_draw_end_t_s - debug_window_draw_start_t_s) * 1000
		im.new_line()
		im.text("drawing debug took {:4.1f} ms".format(debug_window_draw_dur_ms))





def debug_frame_ended() -> Debug[None]:

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





def varied_dict_to_str(dictionary: Dict[str, Any],
					   key_format_string_for_len:    Fun[[int], str ] = default_key_format_string_for_len,
					   value_format_string_for_type: Fun[[type], str] = default_value_format_string_for_type) -> str:
	if len(dictionary) == 0:
		return ''
	else:
		max_key_len = max(  (len(name) for name in dictionary.keys())  , default=0)
		key_format_string = key_format_string_for_len(max_key_len)
		# im.new_line()
		return str.join('\n',  ( key_format_string.format(k) + value_format_string_for_type(type(v)).format(v)
							     for k, v in dictionary.items()  )                                              ) 




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
		im.text( name_and_multiline_str(name, dict_str) )




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
	return name + '\n' + indent_multiline_str(multiline_str, 4)


def indent_str(string: str, indent: int) -> str:
	indent_n = indent
	assert indent_n > 0, "Indent value must be nonnegative (is {})".format(indent_n)
	return ' ' * indent_n + string


def indent_multiline_str(multiline_str: str, indent: int) -> str:
	indent_n = indent
	assert indent_n > 0, "Indent value must be nonnegative (is {})".format(indent_n)
	lines = multiline_str.split('\n')
	return str.join('\n',  (indent_str(line, indent_n) for line in lines)  )




def logged_times_to_durations(fresh_logged_times: OrderedDict_[Tuple[str, str], float]) -> Dict[str, Tuple[float, float]]:
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
