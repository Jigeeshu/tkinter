# -*- coding: cp1252 -*-

"""
Status on 2016-09-08
@author: Jigeeshu Joshi
"""

from Tkinter import *
from tkFileDialog import askopenfilename, askopenfile
import ttk
from ttk import Treeview
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import csv
from calculateheatsource import *
import pandas as pd
from math import *
import gc

large_font = ("Verdana", 18)
small_font = ("Verdana", 10)
verysmall_font = ("Verdana", 6)

# reading csv file containing source information 
filepath = "source.csv"
reader = csv.DictReader(open(filepath))

### dictionary to populate  source type dropdown list 
dict1= {}
for row in reader:
    for column, value in row.iteritems():
        dict1.setdefault(column, []).append(value.decode('latin-1'))

choices = list(set(dict1['Source Typ']))

### dictionary to populate capacity drop down list
with open(filepath, 'rb') as f:
    reader = csv.reader(f)
    l = list(reader)

tl = [[x[i] for x in l] for i in range(len(l[0]))]

dict2 = {}
for i in range(len(choices)):

    maximum = [tl[4][j] for j in range(len(tl[0])) if tl[0][j] == choices[i].encode('latin-1')]
    minimum = [tl[3][j] for j in range(len(tl[0])) if tl[0][j] == choices[i].encode('latin-1')]
    
    dict2[choices[i]] = [minimum, maximum]
    del(minimum)    
    del(maximum)

#global variables
dict_math ={}
testdemand = []
show_plot= False
stc = None  #declaring variable for storage capacity

estimated_storage = None
storage_capacity = 0.0

class myApp(Frame):
    
    def __init__(self, master):
        Frame.__init__(self, master)
        self.master = master
        self.frame_gui = Frame(master) # frame for widgets
        self.frame_gui.pack(side = LEFT, fill = Y)
        self.frame_canvas = Frame(master, bg = 'white') # frame to display table and chart
        self.frame_canvas.pack(side = RIGHT,fill = BOTH,expand =1)
        
        self.GUI() # starting function for GUI
        self.combo = [] # reference to dynamic dropdown list
        self.l = [] # reference to label for rated power
        self.p = [] # reference to label for priority
        self.priority = [] # reference to drop down list for priority
        self.lfile = []  # path to csv file
        self.cnt_id = 0 # initialize idd for treeview 
        self.cbox = []
        self.pbox = []
        self.toolbar = []
        self.storage = []
        self.s = []
        self.store = []
        self.star= []
        self.instruction = []
        self.custom = False
        self.custom_min = []
        self.custom_eff =[]
        
        #self.testdemand = []
        #self.teststorage = {}
        #self.testsource ={}

    def remove_widget(self, w):
        for widget in w:
            widget.destroy()
        self.w= []

    def dynamic_widgets(self, master):
        
        self.remove_widget(self.l)  #remove existing widgets
        self.remove_widget(self.combo)
        self.remove_widget(self.p)
        self.remove_widget(self.priority)

        clabel = Label(self.frame_gui, text = 'Select Capacity (kW):', font = small_font)
        self.l.append(clabel)
        #clabel.pack(pady = 10, padx = 10)
        clabel.grid(row = 60, column = 0,  padx = 10, columnspan = 2, sticky = W)

        cbox_options = []
        if self.source_value.get() in dict2.keys():
            cbox_options = dict2[self.source_value.get()][1]
        
        self.capacity_value = StringVar()
        self.cbox = ttk.Combobox(self.frame_gui, textvariable=self.capacity_value)
        self.cbox['values'] = cbox_options
        self.cbox.current(0)
        self.combo.append(self.cbox)
        #cbox.pack()
        self.cbox.grid(row = 70, column = 0, pady = 5, padx = 10, columnspan = 2, sticky = W+E)

        plabel = Label(self.frame_gui, text = 'Select Priority:', font = small_font)
        self.l.append(plabel)
        #plabel.pack(pady = 10, padx = 10)
        plabel.grid(row = 80, column = 0,  padx = 10,  columnspan = 2, sticky = W)

        self.p_value = StringVar()
        self.pbox= Entry(self.frame_gui, textvariable =self.p_value)
        self.pbox.grid(row = 90, column = 0, pady = 5, padx = 10,  columnspan = 2, sticky = W+E)

        self.var = IntVar()
        c = Checkbutton(self.frame_gui, variable = self.var, text ='Check to use for storage',  font = small_font)
        c.grid(row =100, column = 0, padx = 10, sticky = W)

        #self.TableUI()
        

    def load_file(self):
        self.fname = askopenfilename(filetypes=(("CSV files", "*.csv"),
                                           ("All files", "*.*") ))
        fn = self.fname.split("/")
        label5 = Label(self.frame_gui, text = str('.../' +fn[-1]), font = small_font)
        #label5.pack(pady = 10, padx = 10)
        label5.grid(row = 20, column = 0, sticky = E)

        with open(self.fname, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if row[1] == "demand":
                    continue
                else:        
                    testdemand.append(float(row[1]))
        
    def TableUI(self):
        tv = Treeview(self.frame_canvas, selectmode = 'extended' )
        tv['columns'] = ('type','max', 'priority', 'storage','vlh')
        tv.heading("#0", text='Nr.', anchor='w')
        tv.column("#0", anchor="w", width = 40)
        tv.heading('type', text='Source', anchor='w')
        tv.column('type', anchor="w", width = 100)
        tv.heading('max', text='Capacity (kW)', anchor='w')
        tv.column('max', anchor='w', width=100)
        tv.heading('priority', text='Priority', anchor='w')
        tv.column('priority', anchor='w', width=100)
        tv.heading('storage', text='Storage', anchor='w')
        tv.column('storage', anchor='w', width=100)
        tv.heading('vlh', text='VLh', anchor='w')
        tv.column('vlh', anchor='w', width=100)

        tv.pack(fill = BOTH, expand = True)
        #tv.grid(row= 0 , column = 0,  sticky = (N,S,W,E))
        self.treeview = tv
        #self.grid_rowconfigure(0, weight = 1)
        #self.grid_columnconfigure(0, weight = 1)

        
    def print_table(self):
        
        if self.custom == True:
            self.cnt_id = self.cnt_id +1
            self.treeview.insert('', 'end', str(self.cnt_id),text= self.cnt_id, values=( self.source_c.get(),
                            self.rated_power_c.get(), self.priority_c.get(), self.var_c.get(), ''))
            self.custom_min.append(int(self.min_power_c.get()))
            self.custom_eff.append(float(self.eff_c.get()))
        else:
            self.cnt_id = self.cnt_id +1
            self.treeview.insert('', 'end', str(self.cnt_id),text= self.cnt_id, values=( self.source_value.get(),
                            self.capacity_value.get(), self.p_value.get(), self.var.get(), ''))

        self.remove_widget(self.storage)
        self.remove_widget(self.s)

        ### setting storage capacity ###
        
        slabel = Label(self.frame_gui, text = 'Storage Capacity(kWh)* :', font = small_font)
        self.s.append(slabel)
        slabel.grid(row = 120, column = 0, pady = 15, padx = 10, sticky = W)

        self.instruction = Label(self.frame_gui, text = '*Value is suggested based on the selection of Source Type with priority of 1. \n You may enter a new value.', font = verysmall_font)
        self.star.append(self.instruction) 
        self.instruction.grid(row = 200, column = 0, columnspan = 2)

        
        global storage_capacity, estimated_storage
        
        info = self.treeview.get_children()
        info2 = self.treeview.set(info[-1])
        for j in info2.keys():
                if j == 'storage':
                    if info2[j] == '1':
                        if self.custom == False:
                            storage_capacity = storage_capacity + float(self.capacity_value.get())
                        else:
                            storage_capacity = storage_capacity + float(self.rated_power_c.get())
                            
                            
        #print ('storage_capacity:',storage_capacity)
                        
        estimated_storage = ceil(CalculateStorage(storage_capacity, 85, 60))
        #print ('esimtated:' ,estimated_storage)
        
        v = StringVar()
        self.store= Entry(self.frame_gui, textvariable =v)
        self.storage.append(self.store)
        self.store.grid(row =120, column= 1, pady = 15, padx = 10, sticky = W )
        v.set(str(estimated_storage))
    
    def print_graph(self):

        ## get user selected options into lists for use in plotting the profile ##
        global estimated_storage
        source = []
        rated_power = []
        priority = []
        min_power = []
        eff_factor= []
        storage = []
        testsource = {}
        teststorage = {}
        
        info = self.treeview.get_children()
        
        for i in info:
            info2 = self.treeview.set(i)
            for j in info2.keys():
                if j == 'type':
                    source.append(info2[j].encode('latin-1')) 
                elif j == 'max':
                    rated_power.append(int(info2[j]))
                elif j == 'priority':
                    priority.append(int(info2[j]))
                elif j == 'storage':
                    storage.append(info2[j])
                #print (j, ':', info2[j])

        #for k in range(len(source)):
            for k in range(len(tl[0])):
                if tl[0][k] == source[-1] and tl[4][k] == str(rated_power[-1]):
                    min_power.append(int(tl[3][k]))
                    eff_factor.append(float(tl[7][k]))

        min_power.extend(self.custom_min)
        eff_factor.extend(self.custom_eff)
        
        ### set arguements for function CalculateHeatSources ###

        testsource ={'type': source, 'rated_power' : rated_power, 'priority' : priority,
                'minimum_power':min_power, 'efficiency_factor':eff_factor, 'storage':storage}
        teststorage = {"capacity" : CalculateStorage(estimated_storage, 85, 60),
                       "lossfactor" : 0.02, "load" : 0}
        
        print '-----------------------'
        print testsource
        print teststorage
        
        df = CalculateHeatSources(testdemand, teststorage, testsource)
        
        ### print graph ###
        f = plotprofile(df)
        
        #remove existing plot and toolbar widgets
        global show_plot
        if show_plot:
            self.canvas.get_tk_widget().pack_forget()
            self.toolbar.destroy()
            gc.collect() #flush memory
        
        
        self.canvas = FigureCanvasTkAgg(f, self.frame_canvas)
        self.canvas.get_tk_widget().pack(fill = BOTH, expand = True)
        #self.canvas.get_tk_widget().grid(row = 1, column = 0 ,  sticky = (N,S,W,E))
        #self.grid_rowconfigure(1, weight = 1)
        #self.grid_columnconfigure(0, weight = 1)
   
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.frame_canvas)
        self.toolbar.pack()
        #self.canvas._tkcanvas.grid(row = 2, column = 0)
        show_plot= True
        
    def delete_row(self):  ## delete selected rows from table
        
        selected_item = self.treeview.selection()[0] ## get selected item
        self.treeview.delete(selected_item)

    def reset_all(self):
        
        self.box.delete(0, 'end')
        self.cbox.delete(0, 'end')
        self.pbox.delete(0, 'end')
        self.store.delete(0, 'end')
        #self.instruction.grid_forget()

        self.cnt_id = 0
        for i in self.treeview.get_children():
            self.treeview.delete(i)
        
        self.canvas.get_tk_widget().delete("all")

    def close_dialog(self):
        self.toplevel.destroy()
        self.custom = False

    def custom_source(self, event):
        print 'called'
        self.custom = True
        self.toplevel = Toplevel()
        self.slable = Label(self.toplevel, text = 'Source :')
        self.slable.grid(row =0, column= 0, padx = 10, pady = 10, sticky = E)

        self.source_c = Entry(self.toplevel, textvariable ='')
        self.source_c.grid(row =0, column= 1, padx = 10, pady = 10, sticky = W )

        self.rlable = Label(self.toplevel, text = 'Maximum capacity :')
        self.rlable.grid(row =11, column= 0,padx = 10, pady = 10,  sticky = E )
        self.rated_power_c= Entry(self.toplevel, textvariable ='')
        self.rated_power_c.grid(row =11, column= 1, padx = 10, pady = 10, sticky = W )

        self.plable = Label(self.toplevel, text = 'Priority :')
        self.plable.grid(row =20, column= 0, padx = 10, pady = 10, sticky = E )
        self.priority_c= Entry(self.toplevel, textvariable ='')
        self.priority_c.grid(row =20, column= 1, padx = 10, pady = 10, sticky = W )

        self.mlable = Label(self.toplevel, text = 'Minimum capacity :')
        self.min_power_c= Entry(self.toplevel, textvariable ='')
        self.mlable.grid(row =30, column= 0, padx = 10, pady = 10, sticky = E )
        self.min_power_c.grid(row =30, column= 1, padx = 10, pady = 10, sticky = W )

        self.elable = Label(self.toplevel, text = 'Efficiency :')
        self.elable.grid(row =40, column= 0, padx = 10, pady = 10, sticky = E )
        self.eff_c= Entry(self.toplevel, textvariable ='')
        self.eff_c.grid(row =40, column= 1, padx = 10, pady = 10, sticky = W )

        self.var_c = IntVar()
        c = Checkbutton(self.toplevel, variable = self.var_c, text ='Check to use for storage',  font = small_font)
        c.grid(row =45, column = 1, padx = 10, pady = 10, sticky = W)
        
        button2 = Button(self.toplevel, text="Add", width=20, command = self.print_table)
        #b.pack(side='bottom',padx=0,pady=0)
        button2.grid(row = 50 , column = 0 ,padx=5,pady=20)

        button2 = Button(self.toplevel, text="Close", width=20, command = self.close_dialog)
        #b.pack(side='bottom',padx=0,pady=0)
        button2.grid(row = 50 , column = 1 ,padx=5,pady=20)
        print self.custom
    
    def GUI(self):
        
        self.master.title('Source & Storage Design')
    
        label1 = Label(self.frame_gui, text = 'Source & Storage \n Design', font = large_font)
        #label1.pack(pady = 10, padx = 10, side = TOP)
        label1.grid(row = 0, column = 0, pady = 50, padx = 60, columnspan = 2)

        
        label3 = Label(self.frame_gui, text = 'Upload .csv file with Lastprofil:', font = small_font)
        #label3.pack(pady = 10, padx = 10)
        label3.grid(row = 10, column = 0, padx = 10,  sticky = W)

        self.browse = ttk.Button(self.frame_gui, text = "Upload File", command = self.load_file)
        #browse.pack()
        self.browse.grid(row = 20, column = 0,padx = 10, sticky = W)
        self.browse.columnconfigure(1, weight = 0)
        
        label2 = Label(self.frame_gui, text = '')
        #label2.pack(pady = 10, padx = 10)
        label2.grid(row = 30, column = 0, sticky = W)

        link = Label(self.frame_gui, text="Click to add custom source", fg="blue", cursor="hand2")
        link.grid(row =35, column=0, pady = 10, padx = 10,sticky = W)
        link.bind("<Button-1>", self.custom_source)
        
        label4 = Label(self.frame_gui, text = 'Select Source Type:', font = small_font)
        #label4.pack(pady = 10, padx = 10)
        label4.grid(row = 40, column = 0, padx = 10, columnspan = 2, sticky = W)
        
        self.source_value = StringVar()
        self.box = ttk.Combobox(self.frame_gui, textvariable=self.source_value)
        self.box.bind("<<ComboboxSelected>>", self.dynamic_widgets)
        self.box['values'] = choices
        #self.box.current(0)
        #self.box.pack()
        self.box.grid(row = 50, column = 0, pady = 5, padx = 10, columnspan = 2, sticky = W+E)

        add = ttk.Button(self.frame_gui, text = 'Add', command = self.print_table)
        add.grid(row = 110, column = 0, pady = 20, padx = 10, sticky = W)

        delete = ttk.Button(self.frame_gui, text = 'Delete', command = self.delete_row)
        delete.grid(row = 110, column = 1, pady = 20, padx = 10, sticky = W) 

        self.TableUI()
        
        submit = ttk.Button(self.frame_gui, text = 'Submit', command = self.print_graph)
        submit.grid(row = 150, column = 0, pady = 30, padx = 10, sticky = W)

        reset = ttk.Button(self.frame_gui, text = 'Reset', command = self.reset_all)
        reset.grid(row = 150, column = 1, pady = 30, padx = 10, sticky = W)

#dict_math ={'type': source, 'rated_power' : rated_power, 'priority' : priority,
                #'minimum_power':min_power, 'efficency_factor':eff_factor}

def main():
    root = Tk()
    app= myApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()

