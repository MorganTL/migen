from migen.fhdl.structure import *
from migen.fhdl.specials import Special
from migen.fhdl.tools import value_bits_sign, list_signals

class MultiRegImpl:
	def __init__(self, i, o, odomain, n):
		self.i = i
		self.o = o
		self.odomain = odomain

		w, signed = value_bits_sign(self.i)
		self.regs = [Signal((w, signed)) for i in range(n)]

	def get_fragment(self):
		src = self.i
		o_sync = []
		for reg in self.regs:
			o_sync.append(reg.eq(src))
			src = reg
		comb = [
			self.o.eq(src)
		]
		return Fragment(comb, {self.odomain: o_sync})

class MultiReg(Special):
	def __init__(self, i, o, odomain="sys", n=2):
		Special.__init__(self)
		self.i = i
		self.o = o
		self.odomain = odomain
		self.n = n

	def iter_expressions(self):
		yield self, "i", SPECIAL_INPUT
		yield self, "o", SPECIAL_OUTPUT

	def rename_clock_domain(self, old, new):
		Special.rename_clock_domain(self, old, new)
		if self.odomain == old:
			self.odomain = new

	def list_clock_domains(self):
		r = Special.list_clock_domains(self)
		r.add(self.odomain)
		return r

	@staticmethod
	def lower(dr):
		return MultiRegImpl(dr.i, dr.o, dr.odomain, dr.n)

class PulseSynchronizer:
	def __init__(self, idomain, odomain):
		self.idomain = idomain
		self.odomain = odomain
		self.i = Signal()
		self.o = Signal()

	def get_fragment(self):
		toggle_i = Signal()
		toggle_o = Signal()
		toggle_o_r = Signal()
		sync_i = [
			If(self.i, toggle_i.eq(~toggle_i))
		]
		sync_o = [
			toggle_o_r.eq(toggle_o)
		]
		comb = [
			self.o.eq(toggle_o ^ toggle_o_r)
		]
		return Fragment(comb, 
			{self.idomain: sync_i, self.odomain: sync_o},
			specials={MultiReg(toggle_i, toggle_o, self.odomain)})
