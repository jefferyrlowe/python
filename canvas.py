try:
   from tkinter import *
   import tkinter as tk
   from tkinter.filedialog import *
   import os
   import sys
   import time
   import getpass
   import paramiko
   import cx_Oracle
   from tinydb import TinyDB, Query
except ModuleNotFoundError as e:
   print(e)

desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
docsLib = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Documents/dba_remote')
desktop=desktop.replace("\\","/")
docsLib=docsLib.replace("\\","/")

user = os.environ.get('USERNAME')
ouser='oracle'
phost='Empty'
oraDb='Empty'
selectedlist=list()
sftp=''
transport=''
orapwd=''
orausr=''
dropMenuChoice=''
#selectedHosts = []

dbaConfig=TinyDB(docsLib+"/dbaConfig.json")

dbaToolLog=docsLib+"/dba_tool_log.txt"
hostList=docsLib+"/connhosts.lst"
oraList=docsLib+"/oradbs.lst"
sshList=docsLib+"/dba_ssh_scripts.lst"
sqlList=docsLib+"/dba_sql_scripts.lst"
kfile=docsLib+"/sshkey"
plog=docsLib+"/paramiko.log"
neededFiles=[plog,dbaToolLog,hostList,oraList,sshList,sqlList]

try:
   paramiko.util.log_to_file(plog)
except Exception as e:
   print(e)

try:
   outPutLog = open(dbaToolLog,"a")
except Exception as e:
   print(e)


root = Tk()
root.title('DBA Remote Tool')  # sets window title
root.geometry('1290x980')  # sets default window size (pixels)
  

def donothing():
    outPutArea.insert(END,"Nothing")

def populateTable():
   
   dbaConfig.table('sqlScripts').purge()
   dbaConfig.table('sqlScripts').all()
   table = dbaConfig.table('sqlScripts')
   table.insert({'name': 'GV Instance', 'script': 'select instance_number,instance_name,host_name,version,status,instance_role from gv$instance;'})
   table.insert({'name': 'PDB Info', 'script': 'select con_id,name,open_mode,restricted, trunc(total_size/1024/1024/1024,2) as total_gb from v$pdbs;'})
   table.insert({'name': 'DBA Views', 'script': "select * from dictionary where table_name like 'DBA_%';"})
   table.insert({'name': 'V$database', 'script': 'select name,log_mode,open_mode,database_role,db_unique_name from v$database;'})
   table.insert({'name': 'Current Sessions', 'script': "select inst_id,username,status,schemaname,machine from gv$session where username not in ('SYS');"})
   table.insert({'name': 'Long Ops', 'script': "select opname,totalwork/1024 as total_GB,sofar/1024 as completed_GB,(totalwork-sofar)/1024 as left_todo_GB,\
                                                trunc(sofar/totalwork*100,2) as percent_complete,start_time,elapsed_seconds as elapsed,time_remaining as to_go \
                                                from gv$session_longops where (totalwork-sofar)/1024 <> 0;"})
   table.insert({'name': 'Invalid Objects', 'script': "select object_name,object_type,last_ddl_time,status from dba_objects where owner='ICNINT' and status <> 'VALID';"})
   table.insert({'name': 'User Account Info', 'script': "select username,account_status,lock_date,expiry_date,profile,default_tablespace from dba_users where username= 'ICNINT';"})

def popSqlDropMenu():
   
   options=[]
   counter=0

   for row in dbaConfig.table('sqlScripts'):
      options.insert(counter,row["name"])
      counter+=counter

   #print(options)
   global dropMenuChoice
   dropMenuChoice = StringVar(mainCanvas)
   dropMenuChoice.set(options[0])
   dropMenu=OptionMenu(mainCanvas,dropMenuChoice,*options)
   dropMenu.configure(anchor='w')
   dropMenu.place(x=500,y=260, width=200)

   # link function to change dropdown
   dropMenuChoice.trace('w', change_dropdown)

# on change dropdown value
def change_dropdown(*args):

   script=dropMenuChoice.get()
   User = Query()
   mytext=dbaConfig.table('sqlScripts').search(User.name == script)[0]
   sqlArea.delete('1.0',END)
   sqlArea.insert(END,mytext["script"])
   

def validateNeededFiles():
   log("validateNeededFiles ran")

   ##if not there then create it
   if (os.path.isdir(docsLib))==1:
      outPut("Library :"+repr(docsLib)+" Exists")
   else:
      outPut("Library :"+repr(docsLib)+" Exists NOT exist")
      try:  
       os.mkdir(docsLib)
      except OSError:  
       outPut("Creation of the directory %s failed" % docsLib)
       log("Creation of the directory %s failed" % docsLib)
      else:  
       outPut("Successfully created the directory %s " % docsLib)
       log("Successfully createdthe directory %s " % docsLib)
       
   if (os.path.exists(kfile))==1:
      outPut("SSH Private Key File :"+repr(kfile)+" Exists")
   else:
      outPut("SSH Private Key File DOES NOT EXIST:"+repr(kfile))
      outPut("Create RSA private key file to connect to remote hosts")
      log("SSH Private Key File DOES NOT EXIST:"+repr(kfile))

   for file in neededFiles:
       if (os.path.exists(file))==1:
         outPut("File :"+repr(file)+" Exists")
       else:
         outPut("File :"+repr(file)+" Exists NOT exist")
         try:
            fo = open(file, "w")
            fo.close()
         except OSError:  
          outPut("Creation of the file %s failed" % file)
          log("Creation of the file %s failed" % file)
         else:  
          outPut("Successfully created the file %s " % file)
          log("Successfully created the file %s " % file)

## Populate host Listbox and allow user to choose single or multiple hosts      
def hostlistbox():

   hostListBox.lift()
   hostListBox.focus()
   hostListBox.delete(0,END)
   index=0
   
   try:
    fo = open(hostList, "r")

    with open(hostList,'r') as myFile:
        for line in myFile:
            if line[:1] == "#":
                hostListBox.insert(END, "#"+line+"##")
                hostListBox.itemconfig(index, fg="red")
            else:
                hostListBox.insert(END, line)
            index += 1
            
    fo.close()
      
   except IOError as e: 
      outPut(e)
      

def defaultOpen(fpath,fname):
   try:
      os.startfile(fpath+"/"+fname);
   except IOError as e: 
      outPut(e)
      log(e)

## Populate Oracle DB Listbox and allow user to choose single or multiple hosts      
def oraDBlistbox():

   oraListBox.lift()
   oraListBox.focus()
   oraListBox.delete(0,END)
   index=0
   
   try:
    fo = open(oraList, "r")

    with open(oraList,'r') as myFile:
        for line in myFile:
            if line[:1] == "#":
                oraListBox.insert(END, "#"+line+"##")
                oraListBox.itemconfig(index, fg="red")
            else:
                oraListBox.insert(END, line)
            index += 1
            
    fo.close()
      
   except IOError as e: 
      outPut(e)
      

def defaultOpen(fpath,fname):
   try:
      os.startfile(fpath+"/"+fname);
   except IOError as e: 
      outPut(e)
      log(e)

###SFTP Functions
      
def openHost(hostname):

   global transport
   global sftp

   paramiko.util.log_to_file(docsLib+"/paramiko.log")


   try:
      # Open a transport
      port = 22
      transport = paramiko.Transport((hostname, port))
      #Setup Public Key
      keyfile_path = docsLib+"/sshkey"
      key = paramiko.RSAKey.from_private_key(open(keyfile_path))
      transport.connect()
      transport.auth_publickey(username=ouser, key=key)
      # Go!
      sftp = paramiko.SFTPClient.from_transport(transport)

   except paramiko.ssh_exception.AuthenticationException as e:
      outPut(e)
      log(e)
   
def closeHost():
    # Close
    sftp.close()
    transport.close()
    
def sftpFileInfo(fqname):
   #outPut (sftp.getcwd())
   #outPut (sftp.listdir())
   #outPut (sftp.listdir(fpath))
   #outPut (sftp.listdir_attr())
   
   outPut (repr(fqname))
   finfo = sftp.stat(fqname)
   #outPut (finfo)
   fsize=((finfo.st_size)/1024/1024)
   fsize=("{:.{}f}".format(fsize,4))
   outPut(fsize+" MB")

    
#Button Commands

def enableButtons():
    sshButton.configure(state='normal', bg="white")
    sftpButton.configure(state='normal', bg="white")
    sqlButton.configure(state='normal', bg="white")
    scriptButton.configure (state='normal', bg="white")

def activateSSh():

    hostlistbox()

    sshArea.lift()
    sshArea.focus()
    sshArea.place(x=250, y=55, width=1015, height=200)
    sshArea.delete('1.0',END)

    enableButtons()
    sshButton.configure (state='disabled', bg="yellow")

    #log("SSH Command Set Selected")

    ActionButton.config(state='normal', text="Run Command", command=sshCommand)

def sshCommand():
   
   userEntry = sshArea.get('1.0',END)

   selection=(hostListBox.curselection())
   selectedlist=[]

   if not selection:
      outPut("No Host Selected")
   
   if selection:
      for i in selection:
           entrada = hostListBox.get(i)
           selectedlist.append(entrada)

      #outPut(selectedlist)
      
      for host in selectedlist:
         host=host.replace("\n","")
         if host[:1] != "#":

            try:
               
               myconn=paramiko.SSHClient()
               myconn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
               myconn.connect (host,port=22,username=ouser, key_filename=kfile)
                  
               time.sleep(1)
               myconn.invoke_shell()

               outPut(host)
         
               stdin, stdout, stderr = myconn.exec_command (userEntry)
               outPut(stdout.read())
               sshError=(stderr.read())
               outPut(sshError)
               mainCanvas.update_idletasks()
               
               log("As "+ouser+" On: "+host+" Command: "+repr(userEntry))

               if sshError:
                  log(sshError)

            except paramiko.ssh_exception.AuthenticationException as e:
               outPut(e)
            except paramiko.ssh_exception.SSHException as e:
               outPut(e)
            except TimeoutError as e:
               outPut(e)
               
               myconn.close();

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

def sftpGet():

   rFile=(remoteFile.get('1.0',END))
   rFile=rFile.replace("\n","")

   lFile=(localFile.get('1.0',END))
   lFile=lFile.replace("\n","")

   selection=(hostListBox.curselection())
   selectedlist=[]

   if not selection:
      outPut("No Host Selected")
   
   #outPut("Length")
   #outPut(len(selection))

   if len(selection)==1:
      for i in selection:
           entrada = hostListBox.get(i)
           selectedlist.append(entrada)
      
      for host in selectedlist:
         host=host.replace("\n","")

         try:
            outPut ("Downloading : "+rFile)
            outPut ("From Host : "+host)
            openHost(host)
            
            finfo = sftp.stat(rFile)
            fsize=((finfo.st_size)/1024/1024)
            fsize=("{:.{}f}".format(fsize,4))
            outPut("Size : "+fsize+" MB")

            sftp.get(rFile,lFile)
            outPut("Download Complete")
            log("Downloaded : "+repr(rFile)+" From : "+repr(host)+" Size : "+fsize+" MB")
      
            closeHost()
            sys.stdout.flush()
            
         except FileNotFoundError as e:
            outPut (e)

   else:
      outPut("Select only one Host for GET command")

def sftpPut():

   rFile=(remoteFile.get('1.0',END))
   rFile=rFile.replace("\n","")

   lFile=(localFile.get('1.0',END))
   lFile=lFile.replace("\n","")

   selection=(hostListBox.curselection())
   #outPut(selection)
   selectedlist=[]
   
   if not selection:
      outPut("No Host Selected")
   
   for i in selection:
       entrada = hostListBox.get(i)
       selectedlist.append(entrada)
   
   for host in selectedlist:
      host=host.replace("\n","")

      try:
         outPut ("Uploading : "+lFile)
         outPut ("To Host : "+host)
         openHost(host)
         
         #finfo = sftp.stat(rFile)
         #fsize=((finfo.st_size)/1024/1024)
         #fsize=("{:.{}f}".format(fsize,4))
         #outPut("Size : "+fsize+" MB")

         #log("Uploaded : "+repr(rFile)+" To : "+repr(host)+" Size : "+fsize+" MB")
         log("Uploaded : "+repr(rFile)+" To : "+repr(host))
         
         sftp.put(lFile,rFile)
          
         closeHost()
         sys.stdout.flush()
         
      except FileNotFoundError as e:
         outPut (e)
      except Exception as e:
          outPut (e)

      finally:
         outPut("Upload Complete")


def activateSql():

    oraDBlistbox()
    popSqlDropMenu()
    
    sqlArea.lift()
    sqlArea.focus()
    sqlArea.place(x=250, y=55, width=1015, height=200)
    sqlArea.delete('1.0',END)

    orapwdLabel=Label(mainCanvas)
    orapwdLabel.config(text="Password :")
    orapwdLabel.place(x=500, y=200)
    global orapwd
    orapwd=Entry(mainCanvas, bd=3, show="*")
    orapwd.place(x=500, y=225, width=200, height=26)

    orausrLabel=Label(mainCanvas)
    orausrLabel.config(text="Username : ")
    orausrLabel.place(x=255, y=200)

    global orausr
    orausr=Entry(mainCanvas, bd=3)
    orausr.place(x=255, y=225, width=200, height=26)
    orausr.insert(0,user)

    enableButtons()
    sqlButton.configure (state='disabled', bg="yellow")
    
    #log("SQL Command Set Selected")

    #ActionButton.config(state='normal', text="Run SQL", command=oraSqlCommand)
    ActionButton.config(state='normal', text="Run SQL", command=runOraSqlLoop)


def runOraSqlLoop():

   userEntry = sqlArea.get('1.0',END)
   selection=(oraListBox.curselection())
   selectedlist=[]

   if not selection:
      outPut("No Database Selected")
   
   if selection:
      outPut("SQL: "+userEntry)
      mainCanvas.update_idletasks()
      for i in selection:
         entrada = oraListBox.get(i)
         selectedlist.append(entrada)
      
      for conn in selectedlist:
         conn=conn.replace("\n","")
         if conn[:1] != "#":
            runOraSql(conn)
	  
def runOraSql(conn):

   passwd=orapwd.get()
   user=orausr.get()
   userEntry = sqlArea.get('1.0',END)

   outPut(conn)
   outPut(" ")
   try:
      passwd='Rock21Roll'
      connection = cx_Oracle.connect(user+'/'+passwd+'@'+conn)
      cursor = connection.cursor()
      sqllist=userEntry.split(";")
      #print(sqllist)
      for sql in sqllist:
         sql=sql.replace(";","")

         if sql !="\n":
            #print(sql)

            cursor = connection.cursor()
            run_sql= cursor.execute(sql)
            #outPut(cursor.description)

            if run_sql != None:

               #Show Headers
               #cursor 0=headers,1=class_name,2=column_width
               for result in cursor.description:
                  outPutArea.insert(END,str(result[0])[:20].ljust(21))
               outPutArea.insert(END,"\n")
               outPut(" ")

               for result in run_sql:
                  for word in result:
                     if word != None:
                        outPutArea.insert(END,str(word)[:20].ljust(21))
                     else:
                        outPutArea.insert(END,"None"[:20].ljust(21))   
                  outPutArea.insert(END,"\n")
                  mainCanvas.update_idletasks()

            else:
               outPut("No message received from DB, usually a good sign if no errors where raised")
               #outPut(str(run_sql))
               #outPut(str(cursor))
                        
            cursor.close()

            log(conn+" SQL: "+userEntry)
               
   except cx_Oracle.DatabaseError as e:
      outPut(e)
      log(e)
               
def activateScript():
    
    scriptArea.place(x=250, y=55, width=1015, height=200)
    scriptArea.lift()
    scriptArea.focus()
    scriptArea.delete('1.0',END)
    scriptArea.insert(END,"Script Area for future implementation")

    enableButtons()
    scriptButton.configure (state='disabled', bg="yellow")

    #log("Scripting Command Set Selected")

    ActionButton.config(state='normal', text="Run Script")



def outPut(text):
    outPutArea.insert(END,text)
    outPutArea.insert(END,"\n")

def outPutNR(text):
    outPutArea.insert(END,text)
    
def log(text):
   try:
       timeStamp=(time.strftime("%Y%m%d %H:%M:%S"))
       logArea.insert('1.0',text)
       logArea.insert(END,"\n")
       outPutLog.write(timeStamp+": "+repr(text)+"\n")
       outPutLog.flush()
   except Exception as e:
      print("Log Exception")
      print(e)

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
filemenu.add_command(label="View Log", command=openDbaLogFile)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=exit)
menubar.add_cascade(label="File", menu=filemenu)

hostmenu = Menu(menubar, tearoff=0)
hostmenu.add_command(label="Update List", command=hostlistbox)
hostmenu.add_separator()
hostmenu.add_command(label="Edit Hosts File", command=openHostsFile)
menubar.add_cascade(label="Hosts", menu=hostmenu)

dbmenu = Menu(menubar, tearoff=0)
dbmenu.add_command(label="Update List", command=oraDBlistbox)
dbmenu.add_separator()
dbmenu.add_command(label="Edit DB File", command=openOraDbFile)
menubar.add_cascade(label="Databases", menu=dbmenu)

scriptmenu = Menu(menubar, tearoff=0)
scriptmenu.add_command(label="Edit SSH Scripts", command=openSshScripts)
scriptmenu.add_command(label="Edit SQL Scripts", command=openSqlScripts)
scriptmenu.add_command(label="Edit SFTP Scripts", command=donothing)
scriptmenu.add_command(label="Populate SQL Scripts", command=populateTable)
menubar.add_cascade(label="Scripts", menu=scriptmenu)


helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="Help", command=donothing)
helpmenu.add_command(label="Validate Files", command=validateNeededFiles)
menubar.add_cascade(label="Help", menu=helpmenu)

root.config(menu=menubar)


#Canvas Config
mainCanvas = Canvas(root, bg="light grey", height=980, width=1280)

listLabel=Label(mainCanvas, text='Host List', width=28)
listLabel.place (x=13, y=5)

hostListBox = Listbox(mainCanvas,height=25, width=68, bd=5,selectmode=tk.MULTIPLE, activestyle='dotbox')
hostListBox.place(x=10, y=28, width=210, height=880)

oraListBox = Listbox(mainCanvas,height=25, width=68, bd=5,selectmode=tk.MULTIPLE, activestyle='dotbox')
oraListBox.place(x=10, y=28, width=210, height=880)

ActionLabel=Label(mainCanvas, text='Command Tabs', width=45)
ActionLabel.place (x=250, y=5)

sshButton=Button(mainCanvas,text="SSH", width=10, command=activateSSh)
sshButton.place(x=250,y=28)
sftpButton=Button(mainCanvas,text="SFTP", width=10, command=activateSftp)
sftpButton.place(x=330,y=28)
sqlButton=Button(mainCanvas,text="SQL", width=10, command=activateSql)
sqlButton.place(x=410,y=28)
scriptButton=Button(mainCanvas,text="Script", width=10, command=activateScript)
scriptButton.place(x=490,y=28)

ActionButton=Button(mainCanvas,text="Action", width=15, command=donothing)
ActionButton.place(x=250,y=260)
ActionButton.config(state='disable')

dropMenu=OptionMenu(mainCanvas,dropMenuChoice,dropMenuChoice)
dropMenu.place(x=500,y=260)

sshArea=Text(mainCanvas, bd=3)
sftpArea=Text(mainCanvas, bd=3)
sqlArea=Text(mainCanvas, bd=3)
scriptArea=Text(mainCanvas, bd=3)

remoteFile=Text(mainCanvas, bd=3)
localFile=Text(mainCanvas, bd=3)

outPutArea=Text(mainCanvas, bd=3)
#outPutArea.place(x=250, y=320, width=1015, height=570)

scrollb = tk.Scrollbar(mainCanvas, command=outPutArea.yview)
scrollb.place(in_=outPutArea, relx=1.0, relheight=1.0, bordermode="outside")
outPutArea['yscrollcommand'] = scrollb.set

outPutArea.place(x=250, y=320, width=1015, height=570)


listLabel=Label(mainCanvas, text='Results', width=28)
listLabel.place (x=250, y=293)

logArea=Text(mainCanvas, bg="light grey")
logArea.place(x=250, y=890, width=1015, height=22)

bottomLabel=Text(mainCanvas, bg="light grey")
bottomLabel.insert(END,"User: "+repr(user))
bottomLabel.insert(END,"    Doc Lib: "+repr(docsLib))
bottomLabel.place(x=10, y=915, width=1255, height=25)

#forgetAll()   
activateSSh()
hostlistbox()

mainCanvas.pack()
root.mainloop()


'''def oraSqlCommand():

   passwd=orapwd.get()
   user=orausr.get()
   userEntry = sqlArea.get('1.0',END)
   #outPut("SQL: "+userEntry)
   
   headers = []

   selection=(oraListBox.curselection())
   selectedlist=[]

   if not selection:
      outPut("No Database Selected")
   
   if selection:
      for i in selection:
           entrada = oraListBox.get(i)
           selectedlist.append(entrada)

      #outPut(selectedlist)
      
      for conn in selectedlist:
         conn=conn.replace("\n","")
         if conn[:1] != "#":

            outPut("SQL: "+userEntry)
                  
            #connection = cx_Oracle.connect(user+'/'+passwd+'@hcv431coreddc01:1521/expt1dv.michigan.gov')
            outPut(conn)
            outPut(" ")
            try:
               passwd='Rock21Roll'
               connection = cx_Oracle.connect(user+'/'+passwd+'@'+conn)
               cursor = connection.cursor()
               sql=userEntry
               sql=sql.replace(";","")

               cursor = connection.cursor()
               run_sql= cursor.execute(sql)
               #outPut(cursor.description)

               if run_sql != None:

                  #Show Headers
                  #cursor 0=headers,1=class_name,2=column_width
                  for result in cursor.description:
                     outPutArea.insert(END,str(result[0])[:20].ljust(21))
                  outPutArea.insert(END,"\n")

                  outPut(" ")

                  for result in run_sql:
                     for word in result:

                        if word != None:
                           outPutArea.insert(END,str(word)[:20].ljust(21))
                        else:
                           outPutArea.insert(END,"None"[:20].ljust(21))   
                     outPutArea.insert(END,"\n")

               else:
                  outPut("No message received from DB, usually a good sign if no errors where raised")
                  #outPut(str(run_sql))
                  #outPut(str(cursor))
                  
               cursor.close()

               log(conn+" SQL: "+userEntry)
               
            except cx_Oracle.DatabaseError as e:
               outPut(e)
               log(e)
'''

#Make Rectangles
#canvas.create_rectangle(x1, y1, x2, y2, **kwargs), with (x1,y1) the
#coordinates of the top left corner and (x2, y2) those of the bottom right corner. 
#listArea = mainCanvas.create_rectangle(50, 50, 200, 150, fill='red')
#mainCanvas.move(a, 20, 20)

#Make Generic Text
#canvas_id = mainCanvas.create_text(10, 10, anchor="nw")
#mainCanvas.itemconfig(canvas_id, text="this is the text \n")
#mainCanvas.itemconfig(canvas_id, text="this is also the text")
#mainCanvas.insert(canvas_id, 200, "This is also some text")

