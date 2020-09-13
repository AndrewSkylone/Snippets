import tkinter as tk
from tkinter import filedialog
import os, sys

import keyboard


class Snipper(object):
    def __init__(self):
        self.file_path = None
        self.snippets_frame = None

        self.create_widgets()

    def create_widgets(self):
        self.snippets_frame = Snippets_LabelFrame(master=self, application=self)
        self.snippets_frame.grid(row=0, column=0)

        self.layout_manager = LayoutManager_Frame(master=self, snippets_frame=self.snippets_frame)
        self.layout_manager.grid(row=1, column=0)

    def create_menubar(self, master=None, **options) -> tk.Menu:
        menubar = tk.Menu()
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open...", command=self.open_file)
        filemenu.add_command(label="Open recent", command=self.open_recent_file)
        filemenu.add_command(label="Save", command=self.save_file)
        filemenu.add_command(label="Save as...", command=self.save_file_as)
        menubar.add_cascade(label="File", menu=filemenu)

        return menubar

    def open_file(self):
        self.file_path = filedialog.askopenfilename(initialdir=sys.path[0], title="Select file", filetypes=(("txt files", "*.txt"), ))
        if not self.file_path:
            return        

        snippets = self.get_snippets_from_file(file_path=self.file_path)
        self.snippets_frame.display_snippets(snippets=snippets)
        self.register_snippets(snippets=snippets)

        filename = os.path.basename(self.file_path)
        self.title(title=filename)

    def open_recent_file(self):
        pass

    def save_file(self):
        if not self.file_path:
            self.save_file_as()

        abbreviations = [entry.get() for entry in self.get_abbreviation_entries()]
        templates = [entry.get() for entry in self.get_template_entries()]

        with open(self.file_path, "w") as f:
            for i in range(len(abbreviations)):
                f.write(abbreviations[i] + " : " + templates[i] + "\n")

    def save_file_as(self):
        self.file_path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[("txt files", '*.txt')], initialdir=sys.path[0])
        self.save_file()

    def get_snippets_from_file(self, file_path : str) -> dict:
        snippets = {}
        with open(file_path, "r") as f:
            lines = [line.split(" : ") for line in f.readlines() if not line.isspace()]
            for snippet in lines:
                snippets[snippet[0]] = snippet[1].strip("\n")  
        return snippets 

    def register_snippet(self, abbreviation, template):
        if abbreviation and template:
            keyboard.add_abbreviation(abbreviation, template)

    def register_snippets(self, snippets):
        for abbreviation, template in snippets.items():          
            self.register_snippet(abbreviation, template)

    def unregister_snippet(self, abbreviation, template):
        if abbreviation and template:
            keyboard.remove_word_listener(abbreviation)

    def unregister_all_snippets(self):
        keyboard.unhook_all()

    def get_abbreviation_entries(self) -> list:
        return self.snippets_frame.abbreviation_entries

    def get_template_entries(self) -> list:
        return self.snippets_frame.template_entries
    
    def title(self, title):
        raise NotImplementedError

class Snippets_LabelFrame(tk.LabelFrame):
    def __init__(self, master, application, cfg={}, **kw):
        tk.LabelFrame.__init__(self, master, cfg, **kw)
        self.app = application
        self.__listeners = []
        self.abbreviation_entries = []
        self.template_entries = []

        self.add_snippet_widgets()
        
    def add_snippet_widgets(self):
        self.create_abbreviation_entry()
        self.create_template_entry()
    
    def remove_snippet_widgets(self):
        if not self.abbreviation_entries or not self.template_entries:
            return

        abbreviation_entry = self.abbreviation_entries.pop()
        template_entry = self.template_entries.pop()
        self.app.unregister_snippet(abbreviation_entry.get(), template_entry.get())

        abbreviation_entry.destroy()
        template_entry.destroy()
    
    def create_abbreviation_entry(self):
        row = len(self.abbreviation_entries)

        abbreviation_entry = Snippet_Entry(self, textvariable = tk.StringVar(), state="readonly", width=7, bd=1, justify="center")
        abbreviation_entry.bind('<FocusIn>', self.on_abbreviation_focusIn)
        abbreviation_entry.bind('<FocusOut>', self.on_abbreviation_focusOut)
        abbreviation_entry.grid(row=row, column=0, pady=1)
        self.abbreviation_entries.append(abbreviation_entry)

    def create_template_entry(self):
        row = len(self.template_entries)

        template_entry = Snippet_Entry(self, textvariable = tk.StringVar(), state="readonly", width=40, bd=1, justify="center")
        template_entry.bind('<FocusIn>', self.on_template_focusIn)
        template_entry.bind('<FocusOut>', self.on_template_focusOut)
        template_entry.grid(row=row, column=1)
        self.template_entries.append(template_entry)
    
    def on_abbreviation_focusIn(self, event):
        abbreviation_entry = event.widget
        abbreviation_entry.configure(state="normal")
        index = self.abbreviation_entries.index(abbreviation_entry)

        self.app.unregister_snippet(abbreviation_entry.get(), self.template_entries[index].get())
        self.notify_listeners(event=event)

    def on_abbreviation_focusOut(self, event):
        abbreviation_entry = event.widget
        abbreviation_entry.configure(state="readonly")
        index = self.abbreviation_entries.index(abbreviation_entry)

        abbreviation = abbreviation_entry.get()
        template = self.template_entries[index].get()

        self.app.register_snippet(abbreviation, template)
        self.notify_listeners(event=event)

    def on_template_focusIn(self, event):
        template_entry = event.widget
        template_entry.configure(state="normal")
        index = self.template_entries.index(template_entry)

        self.app.unregister_snippet(self.abbreviation_entries[index].get(), template_entry.get())
        self.notify_listeners(event)

    def on_template_focusOut(self, event):
        template_entry = event.widget
        template_entry.configure(state="readonly")
        index = self.template_entries.index(template_entry)

        abbreviation = self.abbreviation_entries[index].get()
        template = template_entry.get()

        self.app.register_snippet(abbreviation, template)
        self.notify_listeners(event)
    
    def subscribe(self, listener):
        self.__listeners.append(listener)

    def notify_listeners(self, event):
        """ Notify listeners about snippets entry focus events. FocusIn and FocusOut """
        
        for listener in self.__listeners:
            listener.on_entry_focus(event=event)

    def get_snippet_index_by_entry(self, entry) -> int:
        if entry in self.abbreviation_entries:
            return self.abbreviation_entries.index(entry)

        if entry in self.template_entries:
            return self.template_entries.index(entry)

    def display_snippets(self, snippets):
        """ Clear old entries and create new with snippets"""

        self.clear_frame()

        for i, abbreviation in enumerate(snippets):
            self.add_snippet_widgets()
            self.abbreviation_entries[i].textvariable.set(abbreviation)
            template = snippets[abbreviation]
            self.template_entries[i].textvariable.set(template)  
    
    def clear_frame(self):
        for i in range(len(self.abbreviation_entries)):
            self.remove_snippet_widgets()

class LayoutManager_Frame(tk.Frame):
    def __init__(self, master, snippets_frame, cfg={}, **kw):
        tk.Frame.__init__(self, master, cfg, **kw)

        self.snippets_frame = snippets_frame
        self.snippet_index = None

        self.create_widgets()
        self.snippets_frame.subscribe(self)
    
    def create_widgets(self):       
        self.add_button = tk.Button(self, command=self.add_snippet_widgets)
        self.add_button.image = tk.PhotoImage(file=os.path.join("images", "Add.png"))
        self.add_button.configure(image=self.add_button.image)
        self.add_button.grid(row=0, column=0)

        self.remove_button = tk.Button(self, command=self.remove_snippet_widgets)
        self.remove_button.image = tk.PhotoImage(file=os.path.join("images", "remove.png"))
        self.remove_button.configure(image=self.remove_button.image)
        self.remove_button.grid(row=0, column=1)

        self.up_button = tk.Button(self, state=tk.DISABLED, command=self.move_up_snippet_widgets)
        self.up_button.image = tk.PhotoImage(file=os.path.join("images", "Up.png"))
        self.up_button.configure(image=self.up_button.image)
        self.up_button.grid(row=0, column=2)

        self.down_button = tk.Button(self, state=tk.DISABLED, command=self.move_down_snippet_widgets)
        self.down_button.image = tk.PhotoImage(file=os.path.join("images", "Down.png"))
        self.down_button.configure(image=self.down_button.image)
        self.down_button.grid(row=0, column=3)

    def add_snippet_widgets(self):
        self.snippets_frame.add_snippet_widgets()
    
    def remove_snippet_widgets(self):
        self.snippets_frame.remove_snippet_widgets()

    def move_up_snippet_widgets(self):
        pass

    def move_down_snippet_widgets(self):
        pass
    
    def on_entry_focus(self, event):
        if str(event.type) == "FocusIn":
            self.up_button.config(state=tk.NORMAL)
            self.down_button.config(state=tk.NORMAL)
            self.snippet_index = self.snippets_frame.get_snippet_index_by_entry(entry=event.entry)

        elif str(event.type) == "FocusOut":
            self.up_button.config(state=tk.DISABLED)
            self.down_button.config(state=tk.DISABLED)
            self.snippet_index = None
    
class Snippet_Entry(tk.Entry):
    def __init__(self, master, cfg={}, **kw):
        self.textvariable = kw.get("textvariable", None)
        tk.Entry.__init__(self, master, **kw)

        self.bind('<Return>', self.focus_out)
        self.bind('<Button-3>', self.right_button_pressed)

    def focus_out(self, event):
        self.master.focus_set() 
    
    def right_button_pressed(self, event):
        event.widget.delete(0, tk.END)
        event.widget.focus()

class Snipper_TopLevel(Snipper, tk.Toplevel):
    def __init__(self, master, cnf={}, **kw):
        tk.Toplevel.__init__(self, master, cnf, **kw)
        Snipper.__init__(self)

        self.resizable(False, False)
        self.config(menu=self.create_menubar())
            
    def title(self, title):
        tk.Toplevel.title(title)

class Snipper_Frame(Snipper, tk.Frame):
    def __init__(self, master, cnf={}, **kw):
        tk.Frame.__init__(self, master, cnf, **kw)
        Snipper.__init__(self)

        self.master.resizable(False, False)
        master.config(menu=self.create_menubar())
   
    def title(self, title):
        self.master.title(title)


if __name__ == "__main__":
    root = tk.Tk()
    frame = Snipper_Frame(root)
    frame.grid()
    root.mainloop()