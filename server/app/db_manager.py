"""
A custom database manager.
I do not use SQLAlchemy because I have not figured out how can I create and drop indexes as I need.
After all, it is efficient, thread-safe, and easy to use.
"""

import sqlite3
import threading
from .settings import Settings

local_storage = threading.local()

def get_connection() -> 'sqlite3.Connection':
	if not hasattr(local_storage, 'connection'):
		local_storage.connection = sqlite3.connect(Settings.SQLITE_DB_FILE)
	return local_storage.connection

def get_cursor() -> 'sqlite3.Cursor':
	if not hasattr(local_storage, 'cursor'):
		local_storage.cursor = get_connection().cursor()
	return local_storage.cursor

def create_table_entries() -> 'None':
	cursor = get_cursor()
	cursor.execute('''create table if not exists entries (
		key text, -- the entry in lowercase and without accents
	    dictionary_name text, -- filename of the dictionary
	    word text, -- the entry as it appears in the dictionary
	    offset integer, -- offset of the entry in the dictionary file
	    size integer -- size of the definition in bytes
	)''')
	get_connection().commit()

def dictionary_exists(dictionary_name: 'str') -> 'bool':
	cursor = get_cursor()
	cursor.execute('select count(*) from entries where dictionary_name = ?', (dictionary_name,))
	return cursor.fetchone()[0] > 0

def add_entry(key: 'str', dictionary_name: 'str', word: 'str', offset: 'int', size: 'int') -> 'None':
	"Commit manually!"
	cursor = get_cursor()
	cursor.execute('insert into entries values (?, ?, ?, ?, ?)', (key, dictionary_name, word, offset, size))

def commit() -> 'None':
	get_connection().commit()

def get_entries(key: 'str', dictionary_name: 'str') -> 'list[tuple[str, int, int]]':
	"""
	Returns a list of (word, offset, size).
	"""
	cursor = get_cursor()
	cursor.execute('select word, offset, size from entries where key = ? and dictionary_name = ?', (key, dictionary_name))
	return cursor.fetchall()

def delete_dictionary(dictionary_name: 'str') -> 'None':
	cursor = get_cursor()
	cursor.execute('delete from entries where dictionary_name = ?', (dictionary_name,))
	get_connection().commit()

def create_index() -> 'None':
	cursor = get_cursor()
	cursor.execute('create index idx_dictname on entries (dictionary_name)')
	cursor.execute('create index idx_key_dictname on entries (key, dictionary_name)')
	get_connection().commit()

def drop_index() -> 'None':
	cursor = get_cursor()
	cursor.execute('drop index if exists idx_dictname')
	cursor.execute('drop index if exists idx_key_dictname')
	get_connection().commit()

def select_entries_beginning_with(key: 'str', names_dictionaries: 'list[str]') -> 'list[str]':
	"""
	Return the first ten entries (word) in the dictionaries that begin with key.
	"""
	cursor = get_cursor()
	cursor.execute('select distinct word from entries where key like ? and dictionary_name in (%s) order by key limit 10' % ','.join('?' * len(names_dictionaries)), (key + '%', *names_dictionaries))
	return [row[0] for row in cursor.fetchall()]

def select_entries_containing(key: 'str', names_dictionaries: 'list[str]', words_already_found: 'list[str]') -> 'list[str]':
	"""
	Return the first 10 - len(words_already_found) entries (word) in the dictionaries that contain key.
	"""
	num_words = 10 - len(words_already_found)
	cursor = get_cursor()
	cursor.execute('select distinct word from entries where key like ? and dictionary_name in (%s) and word not in (%s) order by key limit ?' % (','.join('?' * len(names_dictionaries)), ','.join('?' * len(words_already_found))), ('%' + key + '%', *names_dictionaries, *words_already_found, num_words))
	return [row[0] for row in cursor.fetchall()]

def select_entries_like(key: 'str', names_dictionaries: 'list[str]') -> 'list[str]':
	"""
	Return the first ten entries matched.
	"""
	cursor = get_cursor()
	cursor.execute('select distinct word from entries where key like ? and dictionary_name in (%s) order by key limit 10' % ','.join('?' * len(names_dictionaries)), (key, *names_dictionaries))
	return [row[0] for row in cursor.fetchall()]

def entry_exists_in_dictionary(key: 'str', dictionary_name: 'str') -> 'bool':
	cursor = get_cursor()
	cursor.execute('select count(*) from entries where key = ? and dictionary_name = ?', (key, dictionary_name))
	return cursor.fetchone()[0] > 0

def entry_exists_in_dictionaries(key: 'str', names_dictionaries : 'list[str]') -> 'bool':
	cursor = get_cursor()
	cursor.execute('select count(*) from entries where key = ? and dictionary_name in (%s)' % ','.join('?' * len(names_dictionaries)), (key, *names_dictionaries))
	return cursor.fetchone()[0] > 0