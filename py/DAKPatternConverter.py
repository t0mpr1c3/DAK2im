#!/usr/bin/python3

import sys
import numpy as np
from collections import Counter
import png


def signExt_b2d(x):
	return (((x & 0xFF) ^ 0x80) - 0x80) & 0xFFFFFFFF


class DAKColor:

	def __init__(self, code = 0x10, n = None, symbol = "", name = "",
		r = np.uint8(), g = np.uint8(), b = np.uint8()):
		self.code = code
		self.n = n
		self.symbol = symbol
		self.name = name
		self.rgb = bytearray([r, g, b])

	def string(self):
		return f"{hex(self.code)}, {str(self.n)}, '{self.symbol}', '{self.name}', {hex(int.from_bytes(self.rgb, 'big'))}"

# end of DAKColor class definition


class DAKPatternConverter:

	def __init__(self, debug = True):
		self.filename = None
		self.height = None
		self.width = None
		self.pattern = bytearray()
		self.extension = bytearray()
		self.colors = {}
		self.max_row_colors = 0
		self.col1 = None
		self.col2 = None
		self.status = None
		self.debug = debug

	def read_pat(self, filename):

		def getByteAt(i):
			return input_data[i] & 0xFF

		def getWordAt(i):
			return getByteAt(i) + (getByteAt(i + 1) << 8)

		def getDWordAt(i):
			return getWordAt(i) + (getWordAt(i + 2) << 16)

		self.__init__()
		self.status = 0
		self.filename = filename
		if self.debug:
			print(f"filename {self.filename}")
		file = open(self.filename, "rb")
		if file is None:
			self.exit("file not found", -3)
		input_data = file.read()
		file.close()
		input_size = len(input_data)
		if self.debug:
			print(f"input size {hex(input_size)} bytes")
			print(f"header {input_data[0:3]}")
		header = input_data[0:3]
		if header != b'D4C' and header != b'D46':
			self.exit("file header not recognized", -4)
		self.width = getWordAt(0x13A)
		self.height = getWordAt(0x13C)
		if self.debug:
			print(f"width {self.width}")
			print(f"height {self.height}")
		if self.width > 500 or self.height > 800:
			print("dimensions are too big")
			sys.exit(-2)
		#
		all_colors = set()
		src_pos = 0x165
		self.pattern = np.zeros((self.height, self.width,), np.uint8)
		for row in range(self.height):
			row_colors = set()
			stitch = 0
			while stitch < self.width:
				run = 1
				color = getByteAt(src_pos)
				src_pos += 1
				if color & 0x80:
					run = color & 0x7F
					color = getByteAt(src_pos)
					src_pos += 1
				if run > 0:
					all_colors.add(color)
					row_colors.add(color)
					for repeat in range(run):
						self.pattern[row, stitch] = color
						stitch += 1
			self.max_row_colors = max(self.max_row_colors, len(row_colors))
		#
		b151 = getByteAt(0x151)
		self.col1 = 0
		if b151:
			self.col1 = np.int8(b151) + 0x100
			if self.debug:
				print(f"col1 {hex(self.col1)}")
		self.col2 = getByteAt(0x152)
		b15A = getByteAt(0x15A)
		if b15A == 0x0E or b15A == 0x0F:
			self.status = 0
		else:
			self.status = b15A
		if self.status == 0 or \
		self.status < self.max_row_colors or \
		self.max_row_colors > 2:
			self.status = self.max_row_colors
		#
		src_pos += 1
		while src_pos < input_size:
			src_pos += 1
			if getByteAt(src_pos - 1) == 0xFE:
				break
			src_pos += getByteAt(src_pos) + 1
			src_pos += getByteAt(src_pos) + 3
		#
		if self.debug:
			print(f"src_pos {hex(src_pos)}")
		dst_pos = 0x10
		if src_pos < input_size:
			# color information after pattern block
			if self.col1 == 0:
				self.col1 = 0x20
				s = src_pos + 0x19
				for i in range(0x48):
					if getByteAt(s) & 0x50 == 0x50:
						self.col1 = i
						if self.debug:
							print(f"col1 {hex(self.col1)}")
						break
					else:
						s += 0x19
			for i in range(0x47):
				src_pos += 0x19
				b = input_data[src_pos:src_pos + 0x1A]
				if b[0] & 0x10 and b[1] > 0:
					new_color = DAKColor(b[0], b[3], bytes([b[1]]).decode(),
						b[10:10 + b[9]].decode(), b[6], b[7], b[8])
					self.colors[b[1]] = new_color
					if self.debug:
						print(f"new_color {new_color.string()}")
			if src_pos < input_size - 6 and \
			bytes(input_data[src_pos:src_pos + 6]) != b'Arial' and \
			input_data[src_pos:src_pos + 6] != bytearray(6):
				extension = 6 * self.height
				self.extension = input_data[src_pos:src_pos + extension]
		if src_pos == input_size or len(self.colors) == 0:
			# color information before pattern block
			if self.col1 == 0:
				self.col1 = Counter(color_array).most_common(1)[0][0]
				if self.debug:
					print(f"col1 {self.col1}")
			color = 0
			for i in range(0x80):
				a = getByteAt(i + 3)
				if a != 0xFF:
					color += 1
					a = 3 * (a & 0xF)
					#b = 3 * (self.getByteAt(i + 0x84) & 0xF)
					new_color = DAKColor(
						0x10 + 0x40 * ((self.col1 & 0xFF) == i),
						color,
						bytes([i]).decode(),
						"",
						getByteAt(a + 0x107),
						getByteAt(a + 0x106),
						getByteAt(a + 0x105))
					self.colors[i] = new_color
					if self.debug:
						print(f"new_color {new_color.string()}")
		return self.status

	def write_sti(self, output_filename = None):

		def setByteAt(i, n):
			sti_data[i] = n & 0xFF

		def setWordAt(i, n):
			setByteAt(i, n)
			setByteAt(i + 1, n >> 8)

		def setDWordAt(i, n):
			setWordAt(i, n)
			setWordAt(i + 2, n >> 16)

		extension = len(self.extension)
		sti_data = bytearray()
		sti_size = None
		block_start = 0x410
		dst_pos = 0x10
		#
		sti_size = block_start + self.width * self.height + 1 + extension
		if self.debug:
			print(f"output size {hex(sti_size)} bytes")
		sti_data = bytearray(sti_size)
		sti_data[0:3] = bytearray(b'Sti')
		setWordAt(4, self.height)
		setWordAt(6, self.width)
		setWordAt(8, self.col1)
		setByteAt(0x0A, 0)
		setByteAt(0x0B, self.status)
		#
		# pattern
		row_start = 0
		for row in range(self.height):
			for stitch in range(self.width):
				loc = block_start + row_start + stitch
				setByteAt(loc, self.pattern[row, stitch])
			row_start += self.width
		#
		# extension
		if extension:
			d = block_start + self.height * self.width
			self.sti_data[d:d + extension] = self.extension
		#
		# colors
		n = 0
		d = dst_pos
		for color in self.colors.values():
			n += 1
			setByteAt(d + 3, color.code)
			setByteAt(d + 2, color.rgb[0]) # r
			setByteAt(d + 1, color.rgb[1]) # g
			setByteAt(d,     color.rgb[2]) # b
			d += 4
		#
		# base color
		count = last = 0
		d = dst_pos + 3
		for i in range(0x100):
			if sti_data[d] & 0x50 == 0x50:
				count += 1
				last = i
			d += 4
		if count == 1:
			if self.debug:
				print(f"last {last}")
			setWordAt(8, last + 0x200)
		#
		setByteAt(dst_pos + 0x3FC, 0xFF)
		setByteAt(dst_pos + 0x3FD, 0xFF)
		setByteAt(dst_pos + 0x3FE, 0xFF)
		#
		# output
		if output_filename == None:
			output_filename = self.filename[0:self.filename.find(".") + 1] + "sti"
			if self.debug:
				print(f"output_filename {output_filename}")
		try:
			file = open(output_filename, "wb")
		except Exception as ex:
			self.exit(ex, -3)
		try:
			file.write(sti_data)
		except Exception as ex:
			file.close()
			self.exit(ex, -3)
		file.close()
		return self.status
	
	def write_png(self, output_filename = None):
		if output_filename == None:
			output_filename = self.filename[0:self.filename.find(".") + 1] + "png"
			if self.debug:
				print(f"output_filename {output_filename}")
		try:
			file = open(output_filename, "wb")
		except Exception as ex:
			self.exit(ex, -3)
		writer = png.Writer(self.width, self.height, greyscale=False, bitdepth=8)
		rgb = [[num for element in [self.colors[self.pattern[self.height - row - 1, stitch]].rgb \
		for stitch in range(self.width)] for num in element] for row in range(self.height)]
		try:
			writer.write(file, rgb)
		except Exception as ex:
			file.close()
			self.exit(ex, -3)
		file.close()
		return 0

	def exit(self, msg, return_code):
		print(msg)
		self.status = return_code
		sys.exit(self.status)

# end of DAKPatternConverter class definition


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("filename argument required")
		sys.exit(-3)
	elif len(sys.argv) > 2:
		print("too many arguments")
		sys.exit(-3)
	else:
		p = DAKPatternConverter(debug=True)
		p.read_pat(sys.argv[1])
		p.write_sti()
		p.write_png()
