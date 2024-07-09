"""
File: utils.py
Author: Christien Alden
Purpose: Contains utility functions and classes.
"""
import sys

class Log:
	def __init__(self, quiet : bool = False, fill_width : int = 60, fill_char : str = '.'):
		self.quiet = quiet
		self.fill_width = fill_width
		self.fill_char = fill_char

	def __call__(self, *args, **kwargs):
		if not self.quiet:
			print(*args, **kwargs)

	def action(self, message : str, min_fill : int = 0):
		self(f'{self.pad(message, min_fill)}', end = '')
		sys.stdout.flush()

	def success(self):
		self('done')
		sys.stdout.flush()

	def fail(self):
		self('failed')
		sys.stdout.flush()

	def pad(self, message : str, min_fill : int = 0) -> str:
		if len(message) >= self.fill_width - min_fill:
			return f'{message}{min_fill * self.fill_char}'

		return message.ljust(self.fill_width, self.fill_char)
