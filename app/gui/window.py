from dataclasses import dataclass
import logging
import tkinter as tk
import tkinter.ttk as ttk


class Window(tk.Tk):
    '''
        Instance of tk.Tk with a built in TreeView
    '''
    def __init__(self, title: str, w: int, h: int, x: int, y: int):
        super().__init__()
        
        self.title(title)
        self.geometry(str(w) + "x" + str(h) + "+" + str(x) + "+" + str(y))
        
        self.add_mode = tk.StringVar(value="keywords")

        self.create_info_labels()
        self.entry = self.create_entry_widget()
        self.tree = self.create_tree_widget()

        # variables for the newscraper
        self.keywords = []
        self.feedwords = []


    def create_info_labels(self):
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Helvetica', 20))
        style.configure('Desc.TLabel', font=('Helvetica', 10))
        
        l0 = ttk.Label(self, text='newscrape', style="Title.TLabel")
        l0.pack(pady=5)
        l1 = ttk.Label(self, text="Type in the keyword/feedword you want below. Then click 'add', then 'submit' once you are finished", style="Desc.TLabel")
        l1.pack(pady=5)
        l2 = ttk.Label(self, text="Keywords: Words that the app will look for and return in the article title", style="Desc.TLabel")
        l2.pack(pady=5)
        l3 = ttk.Label(self, text="Feedwords: Words that the app will look for and return in the article body text", style="Desc.TLabel")
        l3.pack(pady=5)

    def create_entry_widget(self) -> ttk.Entry:
        entry = ttk.Entry(self, width=20)
        entry.pack(pady=5)
        
        # things to go along with the entry button
        add_btn = ttk.Button(text='Add', command=self.treeview_add)
        add_btn.pack(pady=5)
        
        remove_btn = ttk.Button(self, text="Remove", command=self.treeview_remove)
        remove_btn.pack(pady=5)
        
        keyword_btn = ttk.Radiobutton(self, text='Keyword', variable=self.add_mode, value="keywords")
        keyword_btn.pack()

        feedword_btn = ttk.Radiobutton(self, text='Feedword', variable=self.add_mode, value="feedwords")
        feedword_btn.pack()
        
        return entry

    def create_tree_widget(self) -> ttk.Treeview:
        frame = ttk.Frame(self)
        frame.pack(pady=5, fill='both', expand=True)
        
        columns = ('keywords', 'feedwords')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        tree.heading('keywords', text='Keywords')
        tree.heading('feedwords', text='Feedwords')
        tree.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        submit_btn = ttk.Button(self, text='Submit', command=self.shutdown)
        submit_btn.pack(pady=5)

        l4 = ttk.Label(self, text='output is in output/news_articles.csv', style='Desk.TLabel')
        l4.pack(pady=5)

        return tree
    
    def treeview_add(self):
        text = self.entry.get()
        
        if not text.strip():
            return
        
        if self.add_mode.get() == "keywords":
            self.tree.insert('', 'end', values=(text, ''))
            self.keywords.append(text)
        elif self.add_mode.get() == "feedwords":
            self.tree.insert('', 'end', values=('', text))
            self.feedwords.append(text)
            
        self.entry.delete(0, 'end')
    
    def treeview_remove(self):
        selected = self.tree.selection()
        
        for item in selected:
            values = self.tree.item(item, 'values')
            if values[0]:
                self.keywords.remove(values[0])
            if values[1]:
                self.feedwords.remove(values[1])
            self.tree.delete(item)
            
    def shutdown(self):
        logging.debug('Exiting Window...')
        self.destroy()
