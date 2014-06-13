# coding=utf8

import sublime
import threading
import subprocess
import os
import re
import json
import codecs
import hashlib


print_classifications = []
# possible classifications:
possible_classifications = [ 'all',
	'tss', 'tss+', 'tss++',
	'command', 'command+',
	'adapter', 'adapter+',
	'files' ]

# DEBUG
def Debug(classification, text):
	if 'all' in print_classifications or classification in print_classifications:
		print("T3S: %s: %s" % (classification.ljust(8), text))
	if classification not in possible_classifications:
		print("T3S: debug: got unknown debug message classification: %s. " \
			"Consider adding this to possible_classifications" % classification)


# CANCEL COMMAND EXCEPTION
class CancelCommand(Exception):
	pass
	
# CANCEL COMMAND EXCEPTION CATCHER DECORATOR
def catch_CancelCommand(func):
	def catcher(*kargs, **kwargs):
		try:
			func(*kargs, **kwargs)
		except CancelCommand:
			if (Debug > 1):print("A COMMAND WAS CANCELED")
			pass
	return catcher

# PACKAGE PATH
dirname = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))


# VERSIONS
version = int(sublime.version())
ST3 = int(sublime.version()) >= 3000

# MEMBER PREFIX
PREFIXES = {
	'method': u'○',
	'property': u'●',
	'class':u'♦',
	'interface':u'◊',
	'keyword':u'∆',
	'constructor':u'■',
	'variable': u'V',
	'public':u'[pub]',
	'private':u'[priv]'
}

def get_prefix(token):
	if token in PREFIXES:
		return PREFIXES[token]
	else:
		return ''


# GET TSS PATH
def get_tss():
	return os.path.join(dirname,'bin','tss.js')


# GET PROCESS KWARGS
def get_kwargs():
	if os.name == 'nt':
		errorlog = open(os.devnull, 'w')
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		return {'stderr':errorlog, 'startupinfo':startupinfo}
	else:
		return {}


# BYTE ENCODE
def encode(message):
	if ST3: return bytes(message,'UTF-8')
	else: return message.encode('UTF-8')


# IS A TYPESCRIPT FILE
def is_ts(view):
	if not view: return False
	return view.file_name() and view.file_name().endswith('.ts')


# IS A TYPESCRIPT DEFINITION FILE
def is_dts(view):
	return view.file_name() and view.file_name().endswith('.d.ts')


# IS AN OBJECT MEMBER 
# TRUE: line=Instance. or line=Instance.fooba or line=Instance.foobar.alic
# FALSE: line=Inst
js_id_re = re.compile(u'^[_$a-zA-Z\u00FF-\uFFFF][_$a-zA-Z0-9\u00FF-\uFFFF]*')
def is_member_completion(line):
	def partial_completion():
		sp = line.split(".")
		if len(sp) > 1:
			return js_id_re.match(sp[-1]) is not None
		return False
	return line.endswith(".") or partial_completion()


# DEBOUNCE CALL
debounced_timers = {}
def debounce(fn, delay, uid=None, *args):
	uid = uid if uid else fn

	if uid in debounced_timers:
		debounced_timers[uid].cancel()

	if ST3:
		timer = threading.Timer(delay, fn, args)
	else:
		args_safe = (fn,)+args
		timer = threading.Timer(delay, thread_safe, args_safe)
	timer.start()

	debounced_timers[uid] = timer

# ST2 THREAD SAFE
def thread_safe(fn,args=None):
	if args!= None: sublime.set_timeout(lambda:fn(args),0)
	else: sublime.set_timeout(lambda:fn(),0)

# READ FILE
def read_file(filename):
	""" returns None or file contents if available """
	filename = os.path.normcase(filename) # back to \\ in nt
	if os.path.isfile(filename):
		try:
			if os.name == 'nt':
				return open(filename, 'r', encoding='utf8').read()
			else:
				return codecs.open(filename, 'r', 'utf-8').read()
		except IOError:
			pass
	return None


def read_and_decode_json_file(filename):
	""" returns None or json-decoded file contents as object,list,... """
	f = read_file(f)
	return json.loads(f) if f is not None else None

# FILE EXISTS
def file_exists(filename):
	""" returns weather the file exists """
	return os.path.isfile(os.path.normcase(filename))

# GET VIEW CONTENT
def get_content(view):
	return view.substr(sublime.Region(0, view.size()))


# GET LINES
def get_lines(view):
	(lines, col) = view.rowcol(view.size())
	return lines


# GET FILE INFO
def get_file_infos(view):
	return (view.file_name(),get_lines(view),get_content(view))
	
# MAKE MD5 of disk contents of file
def hash_file(filename, blocksize=65536):
	f = open(filename)
	buf = f.read(blocksize)
	hasher = hashlib.md5()
	while len(buf) > 0:
		hasher.update(encode(buf))
		buf = f.read(blocksize)
	f.close()
	return hasher.hexdigest()

# FILENAME transformations
def filename2linux(filename):
	""" returns filename with linux slashes """
	return filename.replace('\\','/')

def filename2key(filename):
	""" returns the unified version of filename which can be used as dict key """
	return filename2linux(filename).lower()

def fn2k(filename):
	""" shortcut for filename2key """
	return filename2key(filename)

def fn2l(filename):
	""" shortcut for filename2linux """
	return filename2linux(filename)


