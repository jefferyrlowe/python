try:
   from tkinter import *
   import tkinter as tk
   from tkinter.filedialog import *
   import os
   import sys
   import time
   import cx_Oracle
   import csv
   
except ModuleNotFoundError as e:
   print(e)

desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
docsLib = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Documents')
desktop=desktop.replace("\\","/")
docsLib=docsLib.replace("\\","/")

##Define Global Variables
user = os.environ.get('USERNAME')
tableNames='APPLICATION DATABASE PERSON PRIV_USER ITRI_SERVER SERVICE'
activeTable=''
schema='itri_owner'
passwd='Rock21Roll'
dbuser='Empty'
phost='Empty'
oraDb='Empty'
sqlResult='Empty'
activeTab='Empty'
selectedlist=list()
formFieldlist=list()

mainLog=docsLib+"/dba_main_log.txt"

root = Tk()
root.title('Information Technology Resource Inventory (ITRI)')  # sets window title
width = (root.winfo_screenwidth()*.8)
height = (root.winfo_screenheight()*.8)
#print(width)
#print(height)
rootSize="%dx%d" % (width,height)
root.geometry(rootSize)  # sets default window size (pixels)


def defineForm(formName):

   if formName=='host':

      global formFieldlist
      global activeTable

      activeTable='ITRI_SERVER'
      
      formFieldlist=["hostname","cluster_name","start_date","end_date","host_owner","os_name","server_type_cd","oe_cd","notes_txt"]
      
      formLabel=Label(mainCanvas, text='Add Host Form', width=50)
      formLabel.place (x=10, y=3)
      
   elif formName=='db':
      print ('Add Database Form')
   elif formName=='Application':
      print ('Add Database Form')

   displayForm()

def displayForm():

   x=1
   
   for field in formFieldlist:
      
      ltext=field
      field=Entry(mainCanvas, bd=3)
      field.place(x=130, y=x*30, width=300, height=25)

      fieldLabel=Label(mainCanvas, text=ltext, width=15, anchor=W)
      fieldLabel.place (x=10, y=x*30)
      
      x+=1

   #print (x)
  
   addButton=Button(mainCanvas,text="Add", width=10, command=sqlInsert)
   addButton.place(x=10,y=x*30)

   
def sqlInsert():

   #print('testing')

   sqlLabel=Text(mainCanvas, width=160, height=10)
   sqlLabel.place (x=10, y="{:.0f}".format(height-180))

   refs=getRefernce(activeTable)

   for result in refs:
      for word in result:
          sqlLabel.insert(END,word)
          sqlLabel.insert(END,' ')

   sqlLabel.insert(END,"\n")

   sql='insert into '+schema+'.'+activeTable+' ('

   for field in formFieldlist:
      sql=sql+field+','
      
   sql = sql[:-1]
   sql=sql+') values ('

   for id in mainCanvas.winfo_children():

      if (id.winfo_class() == "Entry"):
         #print (id.winfo_class())
         if id.get():
            sql=sql+"'"+str(id.get())+"',"
         else:
            sql=sql+"'',"

   sql = sql[:-1]
   sql=sql+')'
   sqlLabel.insert(END,sql)

def getRefernce(tName):
   sql="select a.constraint_name,a.table_name,a.column_name,a.position,b.constraint_type,b.r_constraint_name FROM dba_cons_columns a \
   join dba_constraints b on a.constraint_name=b.constraint_name where a.table_name='"+tName+"' and b.constraint_type='R' order by table_name"

   #print(sql)

   refResult=runSql(sql)
   return refResult
   '''
   for result in refResult:
      for word in result:
         if word != None:
            print(word)
   '''
   
def doNothing():
    outPutArea.insert(END,"Nothing")


#Button Commands

def enableButtons():
    hostButton.configure(state='normal', bg="white")
    dbButton.configure(state='normal', bg="white")
    appButton.configure(state='normal', bg="white")
    customButton.configure (state='normal', bg="white")

def runSql(sql):
            
   try:
         connection = cx_Oracle.connect(user+'/'+passwd+'@hcv431coreddc01:1521/expt1dv.michigan.gov')
         cursor = connection.cursor()

         cursor = connection.cursor()
         runSql = cursor.execute(sql)

         sqlResult = []

         for row in runSql:
            sqlResult.append(row)

         cursor.close()

   except cx_Oracle.DatabaseError as e:
         print(e)

   return sqlResult

'''
def outPut(text):
    outPutArea.insert(END,text)
    outPutArea.insert(END,"\n")

def outPutNR(text):
    outPutArea.insert(END,text)
'''




#Canvas Config
mainCanvas = Canvas(root, bg="light grey", height=height, width=width)


defineForm('host')

mainCanvas.pack()
root.mainloop()




'''

## Menu Frame

#menu = Frame(root, width=800, height=3, bg="black")
menu = Frame(root)
menu.pack()
menu.bind_all("<Control-b>", controlB)
menubar = Menu(root)

filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Open File", command=donothing)
filemenu.add_command(label="Save", command=donothing)
filemenu.add_command(label="Clear <ctrl b>", command=clearOutPut)
filemenu.add_command(label="View Log", command=donothing)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=exit)
menubar.add_cascade(label="File", menu=filemenu)

hostmenu = Menu(menubar, tearoff=0)
hostmenu.add_command(label="Update List", command=donothing)
hostmenu.add_separator()
hostmenu.add_command(label="Edit Hosts File", command=donothing)
menubar.add_cascade(label="Hosts", menu=hostmenu)

dbmenu = Menu(menubar, tearoff=0)
dbmenu.add_command(label="Update List", command=donothing)
dbmenu.add_separator()
dbmenu.add_command(label="Edit DB File", command=donothing)
menubar.add_cascade(label="Databases", menu=dbmenu)

scriptmenu = Menu(menubar, tearoff=0)
scriptmenu.add_command(label="Edit SSH Scripts", command=donothing)
scriptmenu.add_command(label="Edit SQL Scripts", command=donothing)
scriptmenu.add_command(label="Edit SFTP Scripts", command=donothing)
menubar.add_cascade(label="Apps", menu=scriptmenu)

helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="Help", command=donothing)
helpmenu.add_command(label="Validate Files", command=donothing)
menubar.add_cascade(label="Help", menu=helpmenu)

root.config(menu=menubar)

searchBox=Entry(mainCanvas, bd=3)
searchBox.place(x="{:.0f}".format(width*.007), y="{:.0f}".format(height*.005), width="{:.0f}".format(width*.15), height="{:.0f}".format(height*.03))

searchButton=Button(mainCanvas,text="Search", width=15, command=doNothing)
searchButton.place(x="{:.0f}".format(width*.007),y="{:.0f}".format(height*.04))

listLabel=Label(mainCanvas, text='Search List', width="{:.0f}".format(width*.02))
listLabel.place (x="{:.0f}".format(width*.007), y="{:.0f}".format(height*.083))


hostListBox = Listbox(mainCanvas,bd=5,selectmode=tk.MULTIPLE, activestyle='dotbox')
hostListBox.place(x="{:.0f}".format(width*.007), y="{:.0f}".format(height*.11), width=width*.16, height=height*.75)

orapwdLabel=Label(mainCanvas)
orapwdLabel.config(text="Password :")
orapwdLabel.place(x=10, y=height-95)

orapwd=Entry(mainCanvas, bd=3, show="*")
orapwd.place(x=10, y=height-70, width="{:.0f}".format(width*.15), height="{:.0f}".format(height*.03))

ActionLabel=Label(mainCanvas, text='Inventory Options', width="{:.0f}".format(width*.032))
ActionLabel.place (x="{:.0f}".format(width*.186), y=5)

hostButton=Button(mainCanvas,text="Host", width=10, command=doNothing)
hostButton.place(x="{:.0f}".format(width*.186),y=28)
dbButton=Button(mainCanvas,text="Database", width=10, command=doNothing)
dbButton.place(x="{:.0f}".format(width*.25),y=28)
appButton=Button(mainCanvas,text="Application", width=10, command=doNothing)
appButton.place(x="{:.0f}".format(width*.314),y=28)
customButton=Button(mainCanvas,text="Custom", width=10, command=doNothing)
customButton.place(x="{:.0f}".format(width*.378),y=28)

actionButton=Button(mainCanvas,text="Report", width=15, command=doNothing)
actionButton.place(x="{:.0f}".format(width*.45),y=28)

outPutLabel=Label(mainCanvas, text='Results', width=28)
outPutLabel.place (x="{:.0f}".format(width*.186), y="{:.0f}".format(height*.083))

outPutArea=Text(mainCanvas, bd=3)
#outPutArea.place(x=250, y=height-745, width=width*.8, height=height*.8)
outPutArea.place(x="{:.0f}".format(width*.186), y="{:.0f}".format(height*.11), width=width*.8, height=height*.8)

logArea=Text(mainCanvas, bg="light grey")
logArea.place(x="{:.0f}".format(width*.186), y=height-52, width=width*.82, height=22)

bottomLabel=Text(mainCanvas, bg="light grey")
bottomLabel.insert(END,"User: "+repr(user))
bottomLabel.insert(END,"    Doc Lib: "+repr(docsLib))
bottomLabel.place(x=1, y=height-28, width=width, height=25)

#hostlistbox()
'''
