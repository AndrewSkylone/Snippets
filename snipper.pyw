import tkinter as tk
import os

import keyboard


class Snipper(object):
    def __init__(self):
        self.file_path = "snippets.txt" 
        self.snippets_frame = None

        self.create_widgets()

    def create_widgets(self):
        self.snippets_manager = Snippets_LabelFrame(master=self, application=self)
        self.snippets_manager.grid(row=0, column=0)

        self.layout_manager = LayoutManager_Frame(master=self, application=self)
        self.layout_manager.grid(row=1, column=0)

    def get_snippets_from_file(self, path : str) -> dict:
        snippets = {}
        try:
            f = open(path, "r")
        except Exception as e:
            print(e.__traceback__)
            return

        lines = [line.split(" : ") for line in f.readlines() if not line.isspace()]
        for snippet in lines:
            snippets[snippet[0]] = snippet[1].strip("\n")   

        f.close()
        return snippets  

    def register_snippet(self, abbreviation, template):
        if abbreviation and template:
            keyboard.add_abbreviation(abbreviation, template)

    def unregister_snippet(self, abbreviation):
        if abbreviation:
            keyboard.remove_word_listener(abbreviation)

    def unregister_all_snippets(self):
        keyboard.unhook_all()

    def on_abbreviation_focusIn(self, entry):
        self.layout_manager.on_abbreviation_focusIn(entry)

    def on_template_focusIn(self, entry):
        self.layout_manager.on_template_focusIn(entry)    
    
    def on_snippet_entry_focusOut(self):
        self.layout_manager.on_snippet_entry_focusOut()

    def get_abbreviation_entries(self) -> list:
        return self.snippets_manager.abbreviation_entries

    def get_template_entries(self) -> list:
        return self.snippets_manager.template_entries

class Snippets_LabelFrame(tk.LabelFrame):
    def __init__(self, master, application, cfg={}, **kw):
        tk.LabelFrame.__init__(self, master, cfg, **kw)
        self.app = application
        self.abbreviation_entries = []
        self.template_entries = []
    
        self.display_snippets(snippets=self.app.get_snippets_from_file(path=self.app.file_path))
        self.register_all_snippets_from_entries()
    
    def create_snippet_widgets(self):
        self.create_abbreviation_entry()
        self.create_template_entry()
    
    def create_abbreviation_entry(self):
        row = len(self.abbreviation_entries)

        abbreviation_entry = Snippet_Entry(self, textvariable = tk.StringVar(), state="readonly", width=7, bd=1, justify="center")
        abbreviation_entry.bind('<FocusIn>', self.on_abbreviation_focusIn)
        abbreviation_entry.bind('<FocusOut>', self.on_abbreviation_focusOut)
        abbreviation_entry.grid(row=row, column=0)
        self.abbreviation_entries.append(abbreviation_entry)

    def create_template_entry(self):
        row = len(self.template_entries)

        template_entry = Snippet_Entry(self, textvariable = tk.StringVar(), state="readonly", width=40, bd=0, justify="center")
        template_entry.bind('<FocusIn>', self.on_template_focusIn)
        template_entry.bind('<FocusOut>', self.on_template_focusOut)
        template_entry.grid(row=row, column=1)
        self.template_entries.append(template_entry)
    
    def on_abbreviation_focusIn(self, event):
        abbreviation_entry = event.widget
        abbreviation_entry.configure(state="normal")
        self.app.unregister_snippet(abbreviation_entry.get())
        self.app.on_abbreviation_focusIn(entry=abbreviation_entry)

    def on_abbreviation_focusOut(self, event):
        abbreviation_entry = event.widget
        abbreviation_entry.configure(state="readonly")
        index = self.abbreviation_entries.index(abbreviation_entry)

        abbreviation = abbreviation_entry.get()
        template = self.template_entries[index].get()

        self.app.register_snippet(abbreviation, template)
        self.app.on_snippet_entry_focusOut()

    def on_template_focusIn(self, event):
        template_entry = event.widget
        template_entry.configure(state="normal")
        index = self.template_entries.index(template_entry)

        self.app.unregister_snippet(self.abbreviation_entries[index].get())
        self.app.on_template_focusIn(entry=template_entry)

    def on_template_focusOut(self, event):
        template_entry = event.widget
        template_entry.configure(state="readonly")
        index = self.template_entries.index(template_entry)

        abbreviation = self.abbreviation_entries[index].get()
        template = template_entry.get()

        self.app.register_snippet(abbreviation, template)
        self.app.on_snippet_entry_focusOut()

    def display_snippets(self, snippets):
        for i, abbreviation in enumerate(snippets):
            self.create_snippet_widgets()
            self.abbreviation_entries[i].textvariable.set(abbreviation)
            template = snippets[abbreviation]
            self.template_entries[i].textvariable.set(template)  

    def register_all_snippets_from_entries(self):
        for i in range(len(self.abbreviation_entries)):
            abbreviation = self.abbreviation_entries[i].get()
            template = self.template_entries[i].get()
            
            self.app.register_snippet(abbreviation, template)

class LayoutManager_Frame(tk.Frame):
    def __init__(self, master, snippets_frame, cfg={}, **kw):
        tk.Frame.__init__(self, master, cfg, **kw)

        self.snippets_frame = snippets_frame
        self.focused_abbreviation_entry = None
        self.focused_template_entry = None

        self.create_widgets()
    
    def create_widgets(self):       
        self.add_button = tk.Button(self, command=self.add_snippet_widgets)
        self.add_button.image = tk.PhotoImage(file=os.path.join("images", "Add.png"))
        self.add_button.configure(image=self.add_button.image)
        self.add_button.grid(row=0, column=0)

    def add_snippet_widgets(self):
        pass
    
    def on_abbreviation_focusIn(self, entry):
        self.focused_abbreviation_entry = entry

    def on_template_focusIn(self, entry):
        self.focused_template_entry = entry

    def on_snippet_entry_focusOut(self):
        self.focused_abbreviation_entry = None
        self.focused_template_entry = None
    
class Snipper_TopLevel(Snipper, tk.Toplevel):
    def __init__(self, master, cnf={}, **kw):
        tk.Toplevel.__init__(self, master, cnf, **kw)
        Snipper.__init__(self)

        self.resizable(False, False)

class Snipper_Frame(Snipper, tk.Frame):
    def __init__(self, master, cnf={}, **kw):
        tk.Frame.__init__(self, master, cnf, **kw)
        Snipper.__init__(self)

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


if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)

    frame = Snipper_Frame(root)
    frame.grid()
    root.mainloop()