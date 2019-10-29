from tkinter import *
from tkinter.ttk import *
from tkinterhtml import HtmlFrame
import markdown2


class MarkdownWindow(Toplevel):
    """
    Window to render simple HTML for displaying module help/instructions. Takes a string
    of markdown as an input.
    """
    def __init__(self,master_window,markdown_content):
        Toplevel.__init__(self,master=master_window)
        self.helpframe = HtmlFrame(self,horizontal_scrollbar = "auto")
        self.helpframe.set_content('<html></html>')
        self.helpframe.set_content(markdown2.markdown(markdown_content))
        self.helpframe.pack()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        return

    def on_close(self):
        print("Closed help window, event captured")
        self.master.lift()
        self.destroy()
        return

def show_markdown(master_window,markdown_str):
    MarkdownWindow(master_window,markdown_str)
    return
