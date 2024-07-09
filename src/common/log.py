"""
File: utils.py
Author: Christien Alden
Purpose: Contains utility functions and classes.
"""
import sys

class Log:
	def __init__(self, quiet : bool = False, indent_level = 0, fill_width : int = 60, fill_char : str = '.'):
		self.quiet = quiet
		self.indent_level = indent_level
		self.fill_width = fill_width
		self.fill_char = fill_char

	def __call__(self, *args, **kwargs) -> None:
		if not self.quiet:
			indent = self.indent_level * '\t'
			modified_args = tuple(indent + str(arg) for arg in args)
			print(*modified_args, **kwargs)

	def print_no_indent(self, *args, **kwargs) -> None:
		if not self.quiet:
			print(*args, **kwargs)

	def action(self, message : str, min_fill : int = 0) -> None:
		self(f'{self.pad(message, min_fill)}', end = '')
		sys.stdout.flush()

	def success(self, message : str = 'done') -> None:
		self.print_no_indent(message)
		sys.stdout.flush()

	def fail(self, message : str = 'failed') -> None:
		self.print_no_indent(message)
		sys.stdout.flush()

	def error(self, message : str) -> None:
		self.fail()
		self(f'\t{message}')
		sys.stdout.flush()

	def pad(self, message : str, min_fill : int = 0) -> str:
		if len(message) >= self.fill_width - min_fill:
			return f'{message}{min_fill * self.fill_char}'

		return message.ljust(self.fill_width, self.fill_char)
