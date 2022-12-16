# Copyright (C) 2022 William Goodspeed (龚志乐)
# This file is part of GNtools.
#
# GNtools is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# GNtools is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with GNtools. If not, see <https://www.gnu.org/licenses/>.

import re
import math
import json
import gzip
import fnmatch
import shutil
import os.path
import logging

from threading import Thread
from multiprocessing import Process, Queue, Value

blksize = 10*1024*1024
nproc = 4
NW = '\n'

comp_map = {
	'A': 'T', 'T': 'A',
	'U': 'A', 'u': 'a',
	'C': 'G', 'G': 'C',
	'R': 'Y', 'Y': 'R',
	'a': 't', 't': 'a',
	'c': 'g', 'g': 'c',
	'r': 'y', 'y': 'r',
}

def extract_gzfasta(inp, outp):
	"""Extract the gz format fasta file."""
	with gzip.open(inp, 'rb') as f_in:
		with open(outp, 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)

class FastaSequence():
	"""FASTA Sequence Object"""
	def __init__(self, name, desc, data):
		self.name = name
		self.desc = desc
		self.data = data

	def build_text(self, lb=80):
		"""Generate the plain text for this sequence."""
		return f'''>{self.name} {self.desc}
{NW.join([self.data[i:i+lb] for i in range(0, len(self.data), lb)])}'''

	def complement(self):
		"""Reverse the sequence and complement it."""
		self.data = ''.join(map(lambda x: comp_map[x] if x in comp_map else x, self.data))

	def slice(self, start, stop):
		"""Slice the sequence into smaller one."""
		if start < stop:
			self.data = self.data[start-1:stop]
		else:
			self.data = self.data[stop-1:start][::-1]

class FastaReader():
	"""Read an entire fasta sequence file."""
	def update_progress(self, name, finished, total):
		if callable(self.progress_cb):
			self.progress_cb(name, 100*(finished/total))

	def __init__(self, fasta_path, progress_cb=None):
		self.fasta_path = fasta_path
		self.index_path = f'{os.path.dirname(fasta_path)}/{os.path.basename(fasta_path)}.idx'

		self.index = []
		self.running = False
		self.progress_cb = progress_cb

		if not os.path.isfile(fasta_path):
			raise FileNotFoundError('Cannot find target fasta file, enter a valid one')

		if self.fasta_path.endswith('.gz'):
			self.fasta_path = f'{os.path.dirname(fasta_path)}/{os.path.basename(fasta_path)}.txt'
			if not os.path.exists(self.fasta_path):
				logging.info('extract fasta gz to plain text')
				extract_gzfasta(fasta_path, self.fasta_path)

		self.fasta_f = open(self.fasta_path, 'r', encoding='utf-8')

		if not os.path.exists(self.index_path):
			self.build_index()
		else:
			with open(self.index_path, 'r', encoding='utf-8') as idx_f:
				self.index = json.load(idx_f)

		self.update_progress('READY', 1, 1)

	def build_index_thread(self):
		begin_idx = []
		self.running = True

		self.fasta_f.seek(0, os.SEEK_END)
		tlen = self.fasta_f.tell()
		self.fasta_f.seek(0)

		# Find the start of sequences.
		def find(q, offset, n, cnt):
			fr = open(self.fasta_path, 'r')
			fr.seek(offset)
			prev = -1;
			for i in range(n):
				now = fr.tell()
				if now == prev:
					break # reached the end
				buf = fr.read(blksize)
				occr = [i for i, c in enumerate(buf) if c == '>']
				if occr != []:
					q.put(list(map(lambda x: x + now, occr)))
				prev = now
				cnt.value += 1
			fr.close()

		tinfo = []
		tbloc = math.ceil(tlen/blksize)
		blocp = math.floor(tbloc/nproc)

		[ tinfo.append(blocp) for i in range(nproc) ]
		tinfo[-1] += tbloc - blocp * nproc
		self.tbloc = tbloc

		finbk = Value('i', 0)
		queue = Queue()

		process_pool = []
		for i in range(nproc):
			process_pool.append(Process(target=find, args=(queue, tinfo[i]*blksize*i, tinfo[i], finbk)))
		[ process_pool[i].start() for i in range(nproc) ]

		while True:
			self.update_progress('Index the FASTA file...', finbk.value, tbloc)
			try:
				begin_idx += queue.get(timeout=1)
			except:
				pass
			# Exit the loop if all tasks finish.
			noexit = False
			for p in process_pool:
				if p.is_alive():
					noexit = True
			if not noexit:
				break

		# Find all the descriptive lines.
		for i in range(len(begin_idx)):
			self.fasta_f.seek(begin_idx[i])
			desl = self.fasta_f.readline().strip()
			self.index.append({
			    'name': desl.lstrip('>').split()[0],
			    'desc': desl[desl.index(' ') + 1:],
			    'fidx': begin_idx[i]
			})
			self.update_progress('Resolve the index and cache it...', i, len(begin_idx))
		# Cache the index data.
		with open(self.index_path, 'w') as idx_f:
			idx_f.write(json.dumps(self.index))

		self.running = False

	def build_index(self):
		"""Build the index of fasta file."""
		logging.info('target fasta does not have a vaild index, rebuild')
		t = Thread(target=self.build_index_thread)
		t.start()

	def find_seq(self, name):
		"""Find a FastaSequence from the file."""
		for seq in self.index:
			if seq['name'] == name:
				self.fasta_f.seek(seq['fidx'])
				# skip the `>' line
				self.fasta_f.readline()
				# build the sequence data
				data = ''
				while True:
					databuf = self.fasta_f.readline()
					if not databuf or databuf[0] == '>':
						break
					data += databuf.strip()
				return FastaSequence(seq['name'], seq['desc'], data)
		raise NameError('Cannot find the wanted sequence. Maybe out-of-date index?')

	def find_seqs(self, glob, desc_match=False, ignore_case=False):
		"""Find some FastaSequences from the file by glob."""
		seqs = []
		rex = fnmatch.translate(glob)
		for seq in self.index:
			match = re.findall(rex, seq['name'], flags=re.IGNORECASE if ignore_case else 0)
			if desc_match:
				match += re.findall(rex, seq['desc'], flags=re.IGNORECASE if ignore_case else 0)
			if match == []:
				continue
			self.fasta_f.seek(seq['fidx'])
			# skip the `>' line
			self.fasta_f.readline()
			# build the sequence data
			data = ''
			while True:
				databuf = self.fasta_f.readline()
				if not databuf or databuf[0] == '>':
					break
				data += databuf.strip()
			seqs.append(FastaSequence(seq['name'], seq['desc'], data))
		return seqs