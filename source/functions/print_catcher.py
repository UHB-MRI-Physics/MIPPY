class PrintCatcher(object):
	def __init__(self,output_widget):
		self.output = output_widget
	def print(self,string):
		self.output.config(state=NORMAL)
		self.output.insert(END,string)
		self.output.config(state=DISABLED)
	def clear(self):
		self.output.config(state=NORMAL)
		self.output.delete(1.0,END)
		self.output.config(state=DISABLED)

# usage
# 
# p = PrintCatcher(win.textbox)
# p.print("here is some code")
# p.clear()