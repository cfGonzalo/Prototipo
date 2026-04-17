from tkinter import Frame, Label, Entry, Button
from PIL import Image, ImageTk


class vistaInicial(Frame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Stream del video
		self.video = Label(self, image = None)
		self.video.grid(row = 0, column = 0, sticky = "nesw", columnspan = 2, rowspan = 4, padx = 10, pady = 10)

		# ultimo hito visualizado
		self.ult = Label(self, image = None)
		self.ult.grid(row = 0, column = 2, rowspan = 2, sticky ="nesw")

		# Lectura del último hito
		self.lec = Label(self, text = "Ultima lectura: ")
		self.lec.grid(row = 2, column = 2, sticky ="w")

		# Boton de cerrar
		self.bot = Button(self, text ="SALIR")
		self.bot.grid(row=3, column = 2, padx = 10, pady = 10) 

		img = Image.open("_internal/muestra.jpg")
		img= img.resize((1152,648))
		img2=img.resize((384,216))
		img=ImageTk.PhotoImage(img)
		self.video.configure(image = img)
		self.video.image=img
		img2=ImageTk.PhotoImage(img2)
		self.ult.configure(image=img2)
		self.ult.image=img2


	def actualizaFrame(self, img):
		self.video.configure(image=img)
		self.video.image=img
		del img
		return

	def actualizaUlt(self, img, txt):
		self.ult.configure(image=img)
		self.ult.image=img
		del img

		self.lec.configure(text = "Ultima lectura: "+ txt)
		return