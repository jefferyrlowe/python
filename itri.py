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
#docsLib = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Documents/dba_remote')
desktop=desktop.replace("\\","/")
docsLib=docsLib.replace("\\","/")

##Define Global Variables
user = os.environ.get('USERNAME')
tablenames='APPLICATION DATABASE PERSON PRIV_USER SERVER SERVICE'
schema='itri_owner'
passwd='Rock21Roll'
dbuser='Empty'
phost='Empty'
oraDb='Empty'
sqlResult='Empty'
activeTab='Empty'
selectedlist=list()

mainLog=docsLib+"/dba_main_log.txt"

root = Tk()
root.title('Infromation Technology Resource Inventory (ITRI)')  # sets window title
width = (root.winfo_screenwidth()*.8)
height = (root.winfo_screenheight()*.8)
#print(width)
#print(height)
rootSize="%dx%d" % (width,height)
root.geometry(rootSize)  # sets default window size (pixels)

def donothing():
    outPutArea.insert(END,"Nothing")

## Populate host Listbox and allow user to choose single or multiple hosts      
def hostlistbox():

   global activeTab
   activeTab='host'
   #print(activeTab)
   
   #listLabel.config(text='Server List')
   #listLabel.place (x=13, y=5)
   listLabel.place()

   hostListBox.lift()
   hostListBox.focus()
   hostListBox.delete(0,END)
   outPutArea.delete('1.0',END)
   index=0

   try:
      hostResult=runSql('select lower(hostname) from '+schema+'.itri_server')


      for result in hostResult:
          hostListBox.insert(END, result)

      hostResult=runSql('select hostname,server_type_cd,oe_cd,host_owner from '+schema+'.itri_server order by host_owner,server_type_cd,oe_cd')

      #cols=(len(hostResult[0]))
      #rows=(len(hostResult))

      for result in hostResult:
         for word in result:
            if word != None:

               
               wordlen=len(word)

               
               outPutArea.insert(END,word[:20].ljust(21))
            else:
               outPutArea.insert(END," "[:20].ljust(21))
         outPutArea.insert(END,"\n")

   except Exception as e:
      outPut(e)


   enableButtons()
   hostButton.configure (state='disabled', bg="yellow")

## Populate DB Listbox and allow user to choose single or multiple dbs      
def dblistbox():

   global activeTab
   activeTab='db'
   #print(activeTab)

   #listLabel.config(text='DB List')
   #listLabel.place (x=13, y=5)
   listLabel.place()

   hostListBox.lift()
   hostListBox.focus()
   hostListBox.delete(0,END)
   outPutArea.delete('1.0',END)
   index=0

   hostResult=runSql('select lower(dbname) from '+schema+'.itri_database order by lower(dbname)')

   for result in hostResult:
       hostListBox.insert(END, result)

   hostResult=runSql('select lower(dbname),lower(cdb),lower(hostname) from '+schema+'.itri_database order by lower(dbname)')

   #for result in hostResult:
      #outPut(result)

   for result in hostResult:
      for word in result:
         if word != None:
            wordlen=len(word)
            outPutArea.insert(END,word[:20].ljust(21))
         else:
            outPutArea.insert(END," "[:20].ljust(21))
      outPutArea.insert(END,"\n")

   enableButtons()
   dbButton.configure (state='disabled', bg="yellow")

## Populate DB Listbox and allow user to choose single or multiple dbs      
def applistbox():

   global activeTab
   activeTab='app'
   #print(activeTab)

   #listLabel.config(text='Application List')
   listLabel.place()

   hostListBox.lift()
   hostListBox.focus()
   hostListBox.delete(0,END)
   outPutArea.delete('1.0',END)
   index=0

   hostResult=runSql('select app from '+schema+'.apps')

   for result in hostResult:
       hostListBox.insert(END, result)

   hostResult=runSql('select * from '+schema+'.apps')

   #for result in hostResult:
      #outPut(result)

   for result in hostResult:
      for word in result:
         if word != None:
            wordlen=len(word)
            outPutArea.insert(END,word[:20].ljust(21))
         else:
            outPutArea.insert(END," "[:20].ljust(21))
      outPutArea.insert(END,"\n")

   enableButtons()
   appButton.configure (state='disabled', bg="yellow")

def customlistbox():

   global activeTab
   activeTab='custom'
   #print(activeTab)

   #listLabel.config(text='Column Names')
   listLabel.place()

   hostListBox.lift()
   hostListBox.focus()
   hostListBox.delete(0,END)
   outPutArea.delete('1.0',END)
   index=0

   #hostResult=runSql("select table_name from user_tables where table_name in ('APPS','DBS','HOSTS','SERVICES','CONTACTS')")

   #for result in hostResult:
       #hostListBox.insert(END, result)

   
   hostResult=runSql("select table_name,column_name from user_tab_cols where table_name in ('APPS','DBS','HOSTS','SERVICES','CONTACTS') order by 1")

   #for result in hostResult:
      #outPut(result)
   #outPutArea.insert(END,"Columns")
   #outPutArea.insert(END,"\n")

   listTuple=''
   
   for result in hostResult:
      for word in result:
         if word != None:
            #outPutArea.insert(END,word[:20].ljust(21))
            listTuple=listTuple+word[:16].ljust(18)
      hostListBox.insert(END, listTuple)
      #outPutArea.insert(END,listTuple)
      #outPutArea.insert(END,"\n")
      listTuple=""
      
   enableButtons()
   customButton.configure (state='disabled', bg="yellow")

def hostReport():
   outPutArea.delete('1.0',END)

   selection=(hostListBox.curselection())
   selectedlist=[]

   if not selection:
      outPut("No Host Selected")
   
   if selection:
      for i in selection:
           entrada = hostListBox.get(i)
           selectedlist.append(entrada)

      for host in selectedlist:
         #outPut(host)
         #outPutArea.insert(END,repr(host))
         chost=str(host)
         chost=chost.replace("(","")
         chost=chost.replace(")","")
         chost=chost.replace(",","")
         outPutArea.insert(END,'----'+chost+'---- \n')
         
         try:
            outPutArea.insert(END,"----Databases---- \n")
            sql='select lower(dbname) as Database, cdb as CDB_Container from itri_owner.itri_database \
                  where hostname='+chost+' order by cdb,dbname'

            hostResult=runSql(sql)
     
            for result in hostResult:
               for word in result:
                  if word != None:
                     outPutArea.insert(END,word[:20].ljust(21))
               outPutArea.insert(END,"\n")

            outPutArea.insert(END,"----Services---- \n")
            #sql='select service_name, lower(dbname),x.app_id,app_name from itri_owner.itri_service s left join itri_owner.itri_service_application_xref x \
            #  on x.service_id=s.service_name left join itri_owner.itri_application a on a.app_id=x.app_id where lower(dbname) in \
            # (select lower(dbname) from itri_owner.itri_database  where hostname='+chost+') order by dbname'

            sql='select service_name, lower(dbname),s.app_id,app_name from itri_owner.itri_service s left join itri_owner.itri_application a on a.app_id=s.app_id \
            where lower(dbname) in (select lower(dbname) from itri_owner.itri_database  where hostname='+chost+') order by dbname'

            hostResult=runSql(sql)
     
            for result in hostResult:
               for word in result:
                  if word != None:
                     outPutArea.insert(END,word[:20].ljust(21))
               outPutArea.insert(END,"\n")

            outPutArea.insert(END,"----App Contacts---- \n")
            #sql='select x.ref_id as app_abbreviation, x.person_id as contact_som_id,p.person_type_cd \
            #   from itri_owner.itri_person_app_xref x join itri_owner.itri_person p on x.person_id=p.person_id where ref_id in ( \
            #   select distinct(app_id) from (select x.app_id from itri_owner.itri_service s  left join itri_owner.itri_service_application_xref x on s.service_name=x.service_id \
            #   left join itri_owner.itri_application a on x.app_id=a.app_id where lower(dbname) in (select lower(dbname) from itri_owner.itri_database  where hostname='+chost+') \
            #   order by dbname) where app_id is not null) order by x.ref_id'
            sql='SELECT x.ref_id      AS app_abbreviation, x.person_id   AS contact_som_id, p.person_type_cd \
               FROM itri_owner.itri_person_app_xref x JOIN itri_owner.itri_person p  ON x.person_id = p.person_id \
               WHERE ref_id IN (SELECT DISTINCT( app_id ) FROM (SELECT a.app_id FROM itri_owner.itri_service s \
               left join itri_owner.itri_application a on s.app_id=a.app_id WHERE \
               lower(dbname) IN (SELECT lower(dbname) FROM itri_owner.itri_database WHERE hostname = '+chost+') \
               ORDER BY dbname) WHERE app_id IS NOT NULL) ORDER BY x.ref_id'

            hostResult=runSql(sql)
     
            for result in hostResult:
               for word in result:
                  if word != None:
                     outPutArea.insert(END,word[:20].ljust(21))
               outPutArea.insert(END,"\n")

            #Email Only List
            sql='SELECT distinct(x.person_id)  AS contact_som_id FROM itri_owner.itri_person_app_xref x JOIN itri_owner.itri_person p  ON x.person_id = p.person_id \
               WHERE ref_id IN (SELECT DISTINCT( app_id ) FROM (SELECT a.app_id FROM itri_owner.itri_service s \
               left join itri_owner.itri_application a on s.app_id=a.app_id WHERE \
               lower(dbname) IN (SELECT lower(dbname) FROM itri_owner.itri_database WHERE hostname = '+chost+') \
               ORDER BY dbname) WHERE app_id IS NOT NULL) ORDER BY 1'
               
         except Exception as e:
            outPut(e)
 

#Button Commands

def enableButtons():
    hostButton.configure(state='normal', bg="white")
    dbButton.configure(state='normal', bg="white")
    appButton.configure(state='normal', bg="white")
    customButton.configure (state='normal', bg="white")

def runSql(sql):
            
   try:

         connection = cx_Oracle.connect(user+'/'+passwd+'@hcv431coreddc01:1521/expt1dv.michigan.gov')
         logArea.insert(END,"Connection : "+user+'/*****@hcv431coreddc01:1521/expt1dv.michigan.gov \n')
         cursor = connection.cursor()

         cursor = connection.cursor()
         runSql = cursor.execute(sql)

         sqlResult = []

         for row in runSql:
            sqlResult.append(row)

         cursor.close()

         '''
         #headers = []
         #Show Headers
         #for i in cursor.description:
            #headers.append(i[0])
            #outPutNR(i[0])
            #outPutNR(" ")

            #outPut(" ")

         for result in run_sql:
            #outPut(result)
            hostListBox.insert(END, result)
         
         #for result in cursor.execute(sql):
            #outPut(result)

         #Show Headers
         for i in cursor.description:
            headers.append(i[0])
            outPutNR(i[0])
            outPutNR(", ")
         '''
   
               
   except cx_Oracle.DatabaseError as e:
         outPut(e)
         #log(e)
         
   return sqlResult

def runSqlV(sql):
            
   try:

         connection = cx_Oracle.connect(user+'/'+passwd+'@hcv431coreddc01:1521/expt1dv.michigan.gov')
         logArea.insert(END,"Connection : "+user+'/*****@hcv431coreddc01:1521/expt1dv.michigan.gov \n')
         cursor = connection.cursor()

         cursor = connection.cursor()
         runSql = cursor.execute(sql)

         sqlResult = []

         for row in runSql:
            sqlResult.append(row)

         cursor.close()
              
   except cx_Oracle.DatabaseError as e:
         outPut(e)
         
   return sqlResult 

def outPut(text):
    outPutArea.insert(END,text)
    outPutArea.insert(END,"\n")

def outPutNR(text):
    outPutArea.insert(END,text)

#Menu Commands

def openHostsFile(): defaultOpen(docsLib,'connhosts.lst')
def openOraDbFile(): defaultOpen(docsLib,'oradbs.lst')
def openDbaLogFile(): defaultOpen(docsLib,'dba_tool_log.txt')
def openSqlScripts(): defaultOpen(docsLib,'dba_sql_scripts.lst')
def openSshScripts(): defaultOpen(docsLib,'dba_ssh_scripts.lst')
def clearOutPut():  outPutArea.delete('1.0',END)
def controlB(test):  outPutArea.delete('1.0',END)

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


#Canvas Config
mainCanvas = Canvas(root, bg="light grey", height=height, width=width)

searchBox=Entry(mainCanvas, bd=3)
searchBox.place(x="{:.0f}".format(width*.007), y="{:.0f}".format(height*.005), width="{:.0f}".format(width*.15), height="{:.0f}".format(height*.03))

searchButton=Button(mainCanvas,text="Search", width=15, command=donothing)
searchButton.place(x="{:.0f}".format(width*.007),y="{:.0f}".format(height*.04))

listLabel=Label(mainCanvas, text='Search List', width="{:.0f}".format(width*.02))
listLabel.place (x="{:.0f}".format(width*.007), y="{:.0f}".format(height*.083))

#hostListBox = Listbox(mainCanvas,height=25, width=68, bd=5,selectmode=tk.MULTIPLE, activestyle='dotbox')
hostListBox = Listbox(mainCanvas,bd=5,selectmode=tk.MULTIPLE, activestyle='dotbox')
hostListBox.place(x="{:.0f}".format(width*.007), y="{:.0f}".format(height*.11), width=width*.16, height=height*.75)

orapwdLabel=Label(mainCanvas)
orapwdLabel.config(text="Password :")
orapwdLabel.place(x=10, y=height-95)

orapwd=Entry(mainCanvas, bd=3, show="*")
orapwd.place(x=10, y=height-70, width="{:.0f}".format(width*.15), height="{:.0f}".format(height*.03))

ActionLabel=Label(mainCanvas, text='Inventory Options', width="{:.0f}".format(width*.032))
ActionLabel.place (x="{:.0f}".format(width*.186), y=5)

hostButton=Button(mainCanvas,text="Host", width=10, command=hostlistbox)
hostButton.place(x="{:.0f}".format(width*.186),y=28)
dbButton=Button(mainCanvas,text="Database", width=10, command=dblistbox)
dbButton.place(x="{:.0f}".format(width*.25),y=28)
appButton=Button(mainCanvas,text="Application", width=10, command=applistbox)
appButton.place(x="{:.0f}".format(width*.314),y=28)
customButton=Button(mainCanvas,text="Custom", width=10, command=customlistbox)
customButton.place(x="{:.0f}".format(width*.378),y=28)

actionButton=Button(mainCanvas,text="Report", width=15, command=hostReport)
actionButton.place(x="{:.0f}".format(width*.45),y=28)
#ActionButton.config(state='disable')

#sshArea=Text(mainCanvas, bd=3)
#sftpArea=Text(mainCanvas, bd=3)
#sqlArea=Text(mainCanvas, bd=3)
#scriptArea=Text(mainCanvas, bd=3)

#remoteFile=Text(mainCanvas, bd=3)
#localFile=Text(mainCanvas, bd=3)

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

hostlistbox()

mainCanvas.pack()
root.mainloop()

'''

def defaultOpen(fpath,fname):
   try:
      os.startfile(fpath+"/"+fname);
   except IOError as e: 
      outPut(e)
      log(e)

def log(text):
   try:
       timeStamp=(time.strftime("%Y%m%d %H:%M:%S"))
       outPutLog.write(timeStamp+": "+repr(text)+"\n")
       outPutLog.flush()
   except Exception as e:
      print("Log Exception")
      print(e)
      
def activateSftp():

    hostlistbox()
    
    sftpArea.place(x=250, y=55, width=1015, height=200)
    sftpArea.lift()
    sftpArea.focus()
    sftpArea.delete('1.0',END)
    sftpArea.insert(END,"Secure File Transfer Protocol Command \n")
    sftpArea.config(state='disable')

    localLabel=Label(mainCanvas)
    localLabel.config(text="Local Path and Filename")
    localLabel.place(x=255, y=85)
    global localFile
    localFile=Text(mainCanvas, bd=3)
    localFile.insert(END,desktop+"/filename")
    localFile.place(x=255, y=105, width=900, height=26)

    remoteLabel=Label(mainCanvas)
    remoteLabel.config(text="Remote Path and Filename")
    remoteLabel.place(x=255, y=135)
    global remoteFile
    remoteFile=Text(mainCanvas, bd=3)
    remoteFile.insert(END,'/u02/users/lowej5/scripts/filename')
    remoteFile.place(x=255, y=155, width=900, height=26)

    warningLabel=Label(mainCanvas)
    warningLabel.config(bg="yellow")
    warningLabel.config(text="Warning - No file checking is happening so existing files WILL be over written")
    warningLabel.place(x=255, y=185)

    getButton=Button(mainCanvas,text="GET", width=10, command=sftpGet)
    getButton.place(x=260 ,y=220)
    putButton=Button(mainCanvas,text="PUT", width=10, command=sftpPut)
    putButton.place(x=350 ,y=220)

    enableButtons()
    sftpButton.configure (state='disabled', bg="yellow")

    #log("SFTP Command Set Selected")

    ActionButton.config(state='disable', text="")

    
def activateSftp():

    hostlistbox()
    
    sftpArea.place(x=250, y=55, width=1015, height=200)
    sftpArea.lift()
    sftpArea.focus()
    sftpArea.delete('1.0',END)
    sftpArea.insert(END,"Secure File Transfer Protocol Command \n")
    sftpArea.config(state='disable')

    localLabel=Label(mainCanvas)
    localLabel.config(text="Local Path and Filename")
    localLabel.place(x=255, y=85)
    global localFile
    localFile=Text(mainCanvas, bd=3)
    localFile.insert(END,desktop+"/filename")
    localFile.place(x=255, y=105, width=900, height=26)

    remoteLabel=Label(mainCanvas)
    remoteLabel.config(text="Remote Path and Filename")
    remoteLabel.place(x=255, y=135)
    global remoteFile
    remoteFile=Text(mainCanvas, bd=3)
    remoteFile.insert(END,'/u02/users/lowej5/scripts/filename')
    remoteFile.place(x=255, y=155, width=900, height=26)

    warningLabel=Label(mainCanvas)
    warningLabel.config(bg="yellow")
    warningLabel.config(text="Warning - No file checking is happening so existing files WILL be over written")
    warningLabel.place(x=255, y=185)

    getButton=Button(mainCanvas,text="GET", width=10, command=sftpGet)
    getButton.place(x=260 ,y=220)
    putButton=Button(mainCanvas,text="PUT", width=10, command=sftpPut)
    putButton.place(x=350 ,y=220)

    enableButtons()
    sftpButton.configure (state='disabled', bg="yellow")

    #log("SFTP Command Set Selected")

    ActionButton.config(state='disable', text="")

    ---Report SQL
DEFINE host = hcv431coreddc01;
set pages 8000
set echo off
set verify off

select count(*) as Total_DBs from itri_owner.itri_database  where hostname='&host' order by cdb,dbname;
select lower(dbname),lower(cdb) from itri_owner.itri_database  where hostname='&host' order by cdb,dbname;

col lower(service_name) format a20
col lower(dbname) format a10
col APP_ID format a10
select lower(service_name),lower(dbname),x.app_id,a.app_name
from itri_owner.itri_service s 
left join itri_owner.itri_service_application_xref x
on s.service_name=x.service_id
left join itri_owner.itri_application a
on x.app_id=a.app_id
where lower(s.dbname) in
(select lower(s.dbname) from itri_owner.itri_database  where hostname='&host')
order by dbname;

select ref_id as app_abbreviation, person_id as som_id
from itri_owner.itri_person_xref where ref_id in (
select distinct(app_id) from (
select x.app_id
from itri_owner.itri_service s 
left join itri_owner.itri_service_application_xref x
on s.service_name=x.service_id
left join itri_owner.itri_application a
on x.app_id=a.app_id
where lower(s.dbname) in
(select lower(s.dbname) from itri_owner.itri_database  where hostname='&host')
order by dbname)
where app_id is not null);



    
'''

