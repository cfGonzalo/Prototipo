from .vista import vistaInicial
from .root import Root

class Vista:
	def __init__(self):
		self.root = Root()
		self.frames = {}

		self.add_frame(vistaInicial, "inicio")

	def add_frame(self, Frame, name):
		self.frames[name] = Frame(self.root)
		self.frames[name].grid(row = 0, column=0,sticky="nsew")

	def switch(self, name):
		frame = self.frames[name]
		frame.tkraise()

	def start_mainloop(self):
		self.root.mainloop()

	def actualizaFrame(self, img):
		self.frames["inicio"].actualizaFrame(img)

	def actualizaUlt(self, img, txt):
		self.frames["inicio"].actualizaUlt(img, txt)