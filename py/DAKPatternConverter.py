#!/usr/bin/python3

import sys
import numpy as np
from collections import Counter
import png


def signExt_b2d(x):
	return (((x & 0xFF) ^ 0x80) - 0x80) & 0xFFFFFFFF

def getByteAt(data, i):
	return data[i] & 0xFF

def getWordAt(data, i):
	return getByteAt(data, i) + (getByteAt(data, i + 1) << 8)

def getDWordAt(data, i):
	return getWordAt(data, i) + (getWordAt(data, i + 2) << 16)

## Pascal-style string
def getStringAt(data, i):
	size = getByteAt(data, i)
	return data[i + 1:i + size + 1].decode()


class DAKColor:

	def __init__(self, code = 0x10, n = None, symbol = "", name = "",
		r = np.uint8(), g = np.uint8(), b = np.uint8(), binary = None):
		if binary != None:
			self.code = getByteAt(binary, 0)
			self.n = getByteAt(binary, 3)
			self.symbol = getByteAt(binary, 1)
			self.name = getStringAt(binary, 9)
			self.rgb = bytearray([getByteAt(binary, 6), getByteAt(binary, 7), getByteAt(binary, 8)])
		else:
			self.code = code
			self.n = n
			self.symbol = symbol
			self.name = name
			self.rgb = bytearray([r, g, b])

	def string(self):
		return f"{hex(self.code)}, {str(self.n)}, '{chr(self.symbol)}', '{self.name}', {hex(int.from_bytes(self.rgb, 'big'))}"

## end of DAKColor class definition


class DAKStitch:

	def __init__(self, i, j, k, a, b, c, d):
		self.i = i
		self.j = j
		self.k = k
		self.a = a
		self.b = b
		self.c = c
		self.d = d

	def string(self):
		return f"{hex(self.i)}, {hex(self.j)}, {hex(self.k)}, {hex(self.a)}, {hex(self.b)}, {hex(self.c)}, {hex(self.d)}"

## end of DAKStitch class definition


class STPBlock:

	def __init__(self, buffer, start, xorkey = None):
		self.height = getWordAt(buffer, start)
		self.size = getWordAt(buffer, start + 2)
		if xorkey != None:
			self.data = bytearray(self.size)
			for i in range(self.size):
				self.data[i] = buffer[start + 4 + i] ^ xorkey[i]
		else:
			self.data = buffer[start + 4:start + 4 + self.size]

## end of STPBlock class definition

class DAKPatternConverter:

	def __init__(self, debug = True):
		self.filename = None
		self.height = None
		self.width = None
		self.color_pattern = bytearray()
		self.stitch_pattern = bytearray()
		# self.extension = bytearray()
		self.colors = {}
		self.stitches = {}
		self.max_row_colors = 0
		self.col1 = 0
		# self.col2 = 0x3C ## '<'
		self.status = 9
		self.debug = True

	def read_data(self, filename):
		self.__init__()
		self.filename = filename
		if self.debug:
			print(f"filename {self.filename}")
		file = open(self.filename, "rb")
		if file is None:
			self.exit("file not found", -3)
		data = file.read()
		file.close()
		size = len(data)
		if self.debug:
			print(f"input size {hex(size)} bytes")
		return data

	def check_header(self, header, ok_headers):
		if self.debug:
			print(f"header {header}")
		if header not in ok_headers:
			self.exit("file header not recognized", -4)

	def check_dims(self, data, w_pos, h_pos, w_max, h_max):
		self.width = getWordAt(data, w_pos)
		self.height = getWordAt(data, h_pos)
		if self.debug:
			print(f"width {self.width}")
			print(f"height {self.height}")
		if self.width > w_max or self.height > h_max:
			print("dimensions are too big")
			sys.exit(-2)

	def find_col1(buffer, start):
		pos = start
		for i in range(0x47):
			if buffer[pos] & 0x50 == 0x50:
				return i
			else:
				pos += 0x19
		return 0x20 ## default value for col1

	## block of color data after pattern block = 1775 bytes = 0x47 * 0x19
	def read_colors(self, buffer, start):
		pos = start
		for i in range(0x47):
			b = buffer[pos:pos + 0x1A]
			# if b[0] & 0x10 and b[1] > 0: ## works for .pat file
			if b[0] & 0x10: ## works for .stp file
				new_color = DAKColor(binary = b)
				# self.colors[b[1]] = new_color ## works for .pat file
				self.colors[i] = new_color ## works for .stp file
				if self.debug:
					print(f"new_color '{chr(i)}' {new_color.string()}")
			pos += 0x19

	def read_stitches(self, data, start):
		pos = start
		for i in range(0x30):
			k = data[pos + 1]
			if k != 0:
				j = data[pos]
				x = (data[4 * j + 3] & 0xF) | ((k & 5) << 4)
				new_stitch = DAKStitch(i + 1, j, k, data[4 * j], data[4 * j + 1], data[4 * j + 2], data[4 * j + 3])#x)
				self.stitches[i + 1] = new_stitch
				if self.debug:
					print(f"new_stitch {new_stitch.string()}")
			pos += 2

	def read_pat(self, filename):
		## constants
		dst_pos = 0x10
		pattern_start = 0x165
		#
		## read data
		input_data = self.read_data(filename)
		input_size = len(input_data)
		#
		## check data
		self.check_header(input_data[0:3], (b'D4C', b'D6C'))
		self.check_dims(input_data, 0x13A, 0x13C, 500, 800)
		self.status = 0
		#
		## decode run length encoding of color pattern
		## count colors
		self.color_pattern = np.zeros((self.height, self.width,), np.uint8)
		pos = pattern_start
		all_colors = set()
		for row in range(self.height):
			row_colors = set()
			stitch = 0
			while stitch < self.width:
				run = 1
				color = getByteAt(input_data, pos)
				pos += 1
				if color & 0x80:
					run = color & 0x7F
					color = getByteAt(input_data, pos)
					pos += 1
				all_colors.add(color)
				row_colors.add(color)
				if run > 0:
					for i in range(run):
						self.color_pattern[row, stitch] = color
						stitch += 1
			self.max_row_colors = max(self.max_row_colors, len(row_colors))
		#
		## no stitch data
		self.stitch_pattern = np.zeros((self.height, self.width), np.uint8)
		#
		## get base color
		b151 = getByteAt(input_data, 0x151)
		if b151:
			self.col1 = np.int8(b151) + 0x100
		else:
			self.col1 = 0
		# self.col2 = getByteAt(input_data, 0x152)
		#
		## calculate return code
		b15A = getByteAt(input_data, 0x15A)
		if b15A == 0x0E or b15A == 0x0F:
			self.status = 0
		else:
			self.status = b15A
		if self.status == 0 or \
		self.status < self.max_row_colors or \
		self.max_row_colors > 2:
			self.status = self.max_row_colors
		#
		## go to end of pattern block
		pos += 1
		while pos < input_size:
			pos += 1
			if getByteAt(input_data, pos - 1) == 0xFE:
				break
			pos += getByteAt(input_data, pos) + 1
			pos += getByteAt(input_data, pos) + 3
		if self.debug:
			print(f"pos {hex(pos)}")
		#
		## get color information
		## block of color data after pattern block = 1775 bytes = 0x47 * 0x19
		if pos < input_size:
			if self.col1 == 0:
				self.col1 = find_col1(input_data, pos)
			self.read_colors(input_data, pos)
			#
			## not sure what these data represent. Stitch types?
			# pos += 1775
			# if pos < input_size - 6 and \
			# bytes(input_data[pos:pos + 6]) != b'Arial' and \
			# input_data[pos:pos + 6] != bytearray(6):
			# 	extension = 6 * self.height
			# 	self.extension = input_data[pos:pos + extension]
		#
		## color information before pattern block
		if pos == input_size or len(self.colors) == 0:
			if self.col1 == 0:
				self.col1 = Counter(color_array).most_common(1)[0][0]
			color = 0
			for i in range(0x80):
				a = getByteAt(input_data, i + 3)
				if a != 0xFF:
					color += 1
					pos = 3 * (a & 0xF)
					# b = 3 * (self.getByteAt(i + 0x84) & 0xF)
					new_color = DAKColor(
						0x10 + 0x40 * ((self.col1 & 0xFF) == i),
						color,
						chr(i),
						"",
						getByteAt(input_data, 0x107 + pos),
						getByteAt(input_data, 0x106 + pos),
						getByteAt(input_data, 0x105 + pos))
					self.colors[i] = new_color
					if self.debug:
						print(f"new_color {new_color.string()}")
		if self.debug:
			print(f"col1 {hex(self.col1)}")
		#
		## no information on stitch types
		## done
		return self.status

	def read_stp(self, filename):

		def calc_key(data):

			def appendKeystring(next_string, max_size):
				return (keystring + next_string)[0:max_size]

			key1 = (getDWordAt(data, 0x35) >> 1)
			key1 += (getWordAt(data, 0x3F) << 2)
			key1 += getDWordAt(data, 0x39) 
			key1 += getWordAt(data, 0x3D)
			key1 += getByteAt(data, 0x20);
			if self.debug:
				print(f"first key number {key1}")
			salt1 = getWordAt(data, 0x39);
			salt2 = int((getDWordAt(data, 0x35) & 0xFFFF) > 0)
			keystring = getStringAt(data, 0x60)
			keystring = appendKeystring(getStringAt(data, 0x41),    0x6E)
			keystring = appendKeystring(str(getWordAt(data, 0x3D)), 0x7D) 
			keystring = appendKeystring(str(getByteAt(data, 0x20)), 0x8C) 
			keystring = appendKeystring(getStringAt(data, 0x41),    0xAA) 
			keystring = appendKeystring(str(getByteAt(data, 0x20)), 0xB9) 
			keystring = appendKeystring(str(getWordAt(data, 0x3D)), 0xC8)
			if self.debug:
				print(f"first key string '{keystring}'")
			key2 = key1 
			for i in range(len(keystring)):
				b = ord(keystring[i]) // 2
				switch = (i + 1) % 3
				if switch == 0:
					temp = (salt2 + b) // 7
					key2 += (i + 1) * b + temp
				elif switch == 1:
					temp = b // 5 * getWordAt(data, 0x3F);
					key2 += (i + 1) * salt2;
					key2 += b * 6;
					key2 += temp;
				else: ## switch == 2
					key2 += (i + 1) * salt1;
					key2 += b * 4;
			if self.debug:
				print(f"second key number {key2}")
			keystring = str(key2 * 3)
			keystring = appendKeystring(str(key2),     0x1E)
			keystring = appendKeystring(str(key2 * 4), 0x2D)
			keystring = appendKeystring(str(key2 * 2), 0x3C)
			keystring = appendKeystring(str(key2 * 5), 0x4B)
			keystring = appendKeystring(str(key2 * 6), 0x5A)
			keystring = appendKeystring(str(key2 * 8), 0x69)
			keystring = appendKeystring(str(key2 * 7), 0x78)
			if self.debug:
				print(f"second key string '{keystring}'")
			xorkey = bytearray(max_xor_len)
			for i in range(max_xor_len):
				index = (i + 1) % len(keystring)
				temp1 = ord(keystring[index]) & 0xFF
				temp2 = key2 % (i + 1) & 0xFF
				xorkey[i] = temp1 ^ temp2
			return xorkey

		def decrypt_next_block(pos):
			blocks = []
			while True:
				block = STPBlock(input_data, pos, xorkey)
				blocks.append(block)
				pos += block.size + 4
				if block.height == self.height:
					return blocks, pos

		# decode run length encoding of color and stitch patterns
		def decode_runs(data, blocks, offset):
			output = np.zeros((self.height, self.width), np.uint8)
			block_num = 0
			block_data = blocks[0].data
			pos = 0
			for row in range(self.height):
				if row == blocks[block_num].height:
					block_num += 1
					block_data = blocks[block_num].data
					pos = 0
				column = 0
				while column < self.width:
					run = 1
					symbol = getByteAt(block_data, pos)
					pos += 1
					if symbol & 0x80:
						run = symbol & 0x7F
						symbol = getByteAt(block_data, pos)
						pos += 1
					if offset:
						symbol = getByteAt(data, offset + symbol * 2 - 2)
					if run > 0:
						for i in range(run):
							output[row, column] = symbol
							column += 1
			return output

		## constants
		max_xor_len = 21000
		color_block_start = 0xF8
		color_data_size = 1775 ## 71 colors * 25 bytes
		#
		## read data
		input_data = self.read_data(filename)
		#
		## check data
		self.check_header(input_data[0:3], b'D7c')
		self.check_dims(input_data, 3, 5, 500, 3000)
		self.status = 0
		#
		## calculate key for decryption
		xorkey = calc_key(input_data)
		#
		## decrypt data blocks
		color_blocks, stitch_block_start = decrypt_next_block(color_block_start)
		stitch_blocks, color_data_start = decrypt_next_block(stitch_block_start)
		stitch_data_start = color_data_start + color_data_size
		if self.debug:
			print(f"start of color data {hex(color_data_start)}")
			print(f"start of stitch data {hex(stitch_data_start)}")
		#
		## get pattern, color, and stitch data
		self.color_pattern = decode_runs(input_data, color_blocks, 0)
		self.stitch_pattern = decode_runs(input_data, stitch_blocks, color_data_size)
		self.read_colors(input_data, color_data_start)
		self.read_stitches(input_data, stitch_data_start)
		if self.debug:
			print(input_data[stitch_data_start:stitch_data_start+0x100])
			print(self.colors)
		#
		## done
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

		## constants
		block_start = 0x410
		dst_pos = 0x10
		#
		## initialize output
		sti_size = block_start + (self.width + 6) * self.height + 1
		sti_data = bytearray(sti_size)
		if self.debug:
			print(f"output size {hex(sti_size)} bytes")
		#
		## header
		sti_data[0:3] = bytearray(b'Sti')
		setWordAt(4, self.height)
		setWordAt(6, self.width)
		setWordAt(8, self.col1)
		setByteAt(0x0A, 0)
		setByteAt(0x0B, self.status)
		#
		## color pattern
		row_start = 0
		for row in range(self.height):
			for stitch in range(self.width):
				setByteAt(block_start + row_start + stitch, self.color_pattern[row, stitch])
			row_start += self.width
		#
		## extended data
		# extension = len(self.extension)
		# if extension:
		# 	d = block_start + self.height * self.width
		# 	self.sti_data[d:d + extension] = self.extension
		#
		## colors
		n = 0
		pos = dst_pos
		for color in self.colors.values():
			n += 1
			setByteAt(pos + 3, color.code)
			setByteAt(pos + 2, color.rgb[0]) # r
			setByteAt(pos + 1, color.rgb[1]) # g
			setByteAt(pos,     color.rgb[2]) # b
			pos += 4
		#
		## base color
		count = last = 0
		pos = dst_pos + 3
		for i in range(0x100):
			if sti_data[i] & 0x50 == 0x50:
				count += 1
				last = i
			pos += 4
		if count > 0:
			if self.debug:
				print(f"last {last}")
			setWordAt(8, last + 0x200)
		#
		setByteAt(dst_pos + 0x3FC, 0xFF)
		setByteAt(dst_pos + 0x3FD, 0xFF)
		setByteAt(dst_pos + 0x3FE, 0xFF)
		#
		## save output
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
		#
		## done
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
		rgb = [[num for element in [self.colors[self.color_pattern[self.height - row - 1, stitch]].rgb \
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
