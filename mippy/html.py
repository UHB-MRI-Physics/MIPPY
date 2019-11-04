from tkinter import *
from tkinter.ttk import *
from tkinterhtml import HtmlFrame
import markdown2
import os
import webbrowser
import shutil


class MarkdownWindow(Toplevel):
    """
    Window to render simple HTML for displaying simple text-only markdown
    as rendered HTML.
    """
    def __init__(self,master_window,inline='',filepath=''):
        if not inline=='' and not filepath=='':
            print("ERROR: You cannot pass both inline content and filepath.\n"
                    +"Please pass only one or the other.")
        if inline=='' and filepath=='':
            print("ERROR: No content provided.\n"
                    +"Please pass either inline (string) content or filepath.")
        Toplevel.__init__(self,master=master_window)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.htmlframe = HtmlFrame(self,horizontal_scrollbar = "auto")
        self.htmlframe.set_content('<html></html>')
        md_content = None
        if not inline=='':
            md_content = (markdown2.markdown(inline))
        else:
            md_content = markdown2.markdown_path(filepath)
        print(md_content)
        self.htmlframe.set_content(md_content)
        self.htmlframe.pack()

        return

    def on_close(self):
        print("Closed help window, event captured")
        self.master.lift()
        self.destroy()
        return

def markdown_to_browser(module_window,inline='',filepath=''):
    """
    Takes markdown input (as a filepth or as a string), renders
    to html and displays in a web browser. Images must be in a subdirectory
    called img and must be referenced as 'img/filename' in the markdown text.

    Must be called from a module in order to get appropriate directory structure
    for the temporary files.
    """
    md_content = None
    img_paths = []
    if not inline=='':
        md_content = (markdown2.markdown(inline))
    else:
        md_content = markdown2.markdown_path(filepath)
        # Check for images
        filedir = os.path.split(filepath)[0]
        if os.path.exists(os.path.join(filedir,'img')):
            for img in os.listdir(os.path.join(filedir,'img')):
                img_paths.append(os.path.join(filedir,'img',img))
    # print(md_content)
    htmlpath = os.path.join(module_window.instance_info['temp_directory'],module_window.instance_info['module_instance'])
    if not os.path.exists(htmlpath):
        os.makedirs(htmlpath)
    with open(os.path.join(htmlpath,'index.html'),'w') as html_file:
        html_file.write(md_content)
    if len(img_paths)>0:
        if not os.path.exists(os.path.join(htmlpath,'img')):
            os.makedirs(os.path.join(htmlpath,'img'))
        for path in img_paths:
            indir = os.path.split(path)[0]
            infile = os.path.split(path)[1]
            shutil.copyfile(path,os.path.join(htmlpath,'img',infile))
    webbrowser.open_new(os.path.join(htmlpath,'index.html'))
    return
