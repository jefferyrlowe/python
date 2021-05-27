try:
   from tkinter import *
   import tkinter as tk
   from tkinter.filedialog import *
   import os
   import sys
   import time
   import csv
   import getpass
   import hashlib
   import cx_Oracle
   import paramiko
except ModuleNotFoundError as e:
   print(e)


#Define for global use
desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
docsLib = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Documents')
desktop=desktop.replace("\\","\\")
docsLib=docsLib.replace("\\","\\")
tnsadmin = os.getenv('TNS_ADMIN')
user = os.environ.get('USERNAME')

ouser='oracle'
phost='Empty'
oraDb='Empty'
transport=''
username = ""
userpwd = ""
username = ""
userpwd = ""

dba = ""
dbb = ""
sql = ""

sqlMetaData = []

#Files
kfile=docsLib+"/sshkey_conv"
qresulta=docsLib+"/qresulta.csv"
qresultb=docsLib+"/qresultb.csv"
tablereport=docsLib+"/compare_report.txt"
listReport=docsLib+"/list_compare_out.txt"
log=docsLib+"/compare_log.txt"
oraList=docsLib+"/oradbs.lst"
sqlscripts=docsLib+"/dba_ssh_scripts.lst"
tnsfile=docsLib+"/tnsnames.ora"


def donothing():
    outPutArea.insert(END,"Nothing")

def convertTuple(tup): 
    str =  ''.join(tup) 
    return str

def defaultOpen(fpath,fname):
   try:
      os.startfile(fpath+"/"+fname);
   except IOError as e: 
      print(e)

def outPut(text):
   outPutArea.insert(END,text)
   outPutArea.insert(END,"\n")
   outPutArea.see("end")

def runCompare():

   sql = sqlArea.get("1.0",END).rstrip()
   dba = dbaArea.get("1.0",END).rstrip()
   dbb = dbbArea.get("1.0",END).rstrip()

   if sql == "":
      outPut("SEARCH string is Empty")
   elif dba == "":
      outPut("SOURCE is Empty")
   elif dbb == "":
      outPut("COMPARATE is Empty")
   else:
      rbvSelect = rbv.get()
      rbvTypeSelect = typeRbv.get()

      if rbvTypeSelect == 1:
            
         if rbvSelect == 1:
            outPut("List Compare")
            outPut(" ")
            sqlToList(sql)
         elif rbvSelect == 2:
            outPut("Table Compare")
            sqlToFile()
         elif rbvSelect == 3:
            outPut("getCreds()")
            getCreds()
            print(sqlMetaData)
         else:
            outPut("Select Compare type, List or Table")
            
      elif rbvTypeSelect == 2:

         outPut("Host command")
         sshCommand()
         
      else:
         outPut("Select Compare function DB or HOST")

def getMetaData():

   sql = sqlArea.get("1.0",END).rstrip()
   dba = dbaArea.get("1.0",END).rstrip()
   dbb = dbbArea.get("1.0",END).rstrip()
   
   try:
         connection = cx_Oracle.connect(username, userpwd, dba)
         cursor = connection.cursor()
         runSql = cursor.execute(sql)

         for column in runSql.description:
            #print(column[0])
            sqlMetaData.append(column[0])

         cursor.close
         connection.close

   except cx_Oracle.DatabaseError as e:
         print(e)
         outPutArea.insert(END, e)
         outPutArea.insert(END, " ")
   


def sqlToList(sql):
   #print("running sql to list now")
   dba = dbaArea.get("1.0",END).rstrip()
   dbb = dbbArea.get("1.0",END).rstrip()

   
   
   try:
         #connection = cx_Oracle.connect(username, userpwd, dba, encoding="UTF-8")
         connection = cx_Oracle.connect(username, userpwd, dba)
         cursor = connection.cursor()
         runSql = cursor.execute(sql)

         dbaResult = []

         for row in runSql:
            dbaResult.append(row)

         cursor.close
         connection.close
         
         connection = cx_Oracle.connect(username, userpwd, dbb, encoding="UTF-8")
         cursor = connection.cursor()
         runSql = cursor.execute(sql)

         dbbResult = []

         for row in runSql:
            dbbResult.append(row)

         cursor.close
         connection.close

   except cx_Oracle.DatabaseError as e:
         print(e)
         outPutArea.insert(END, e)
         outPutArea.insert(END, " ")
   else:
         outPut("List SQL Ran successfully")

   listCompare(dbaResult,dbbResult)


def listCompare(dbaResult,dbbResult):

   sql = sqlArea.get("1.0",END).rstrip()
   dba = dbaArea.get("1.0",END).rstrip()
   dbb = dbbArea.get("1.0",END).rstrip()

   timeStamp=(time.strftime("%Y%m%d %H:%M:%S"))
   writeFile(listReport,"------------"+timeStamp+"--------------")
   writeFile(listReport,sql)

   writeFile(listReport," ")
   t1=dba +" values MISSING in "+dbb
   
   writeFile(listReport,t1)
   for a in dbaResult:
      if a not in dbbResult:
         #print(a)
         str = convertTuple(a)
         writeFile(listReport,str)
   writeFile(listReport," ")
   t1=dbb +" values MISSING in "+dba
   
   writeFile(listReport,t1)
   for b in dbbResult:
      if b not in dbaResult:
         #print(b)
         str = convertTuple(b)
         writeFile(listReport,str)
         
   
   outPut("List Report Complete "+listReport)
   defaultOpen(docsLib,"list_compare_out.txt")

def writeFile(writeFile,text):
   
   try:
      wFile = open(writeFile,"a")
      wFile.write(text)
      wFile.write("\n")
      wFile.flush()
   except Exception as e:
      print(e)
      

def getCreds():

   global username
   global userpwd

   userEntry = userNameArea.get("1.0",END).rstrip()
   #pwdEntry = pwdArea.get("1.0",END).rstrip()
   pwdEntry = pwdArea.get()
   
   if userEntry != "":
      #print("Using Entered Username")
      username = userEntry
      #print(userEntry)
   else:
      print("Using STORED Username")
      #print(username)

      
   if pwdEntry != "":
      #print("Using Entered Password")
      userpwd = pwdEntry
      #print(pwdEntry)
   else:
      print("Using STORED Password")
      #print(userpwd)

def sshCommand():

   global kfile
   
   sshCommand = sqlArea.get("1.0",END).rstrip()
   hostA = dbaArea.get("1.0",END).rstrip()
   hostB = dbbArea.get("1.0",END).rstrip()
   ResultListA = []
   ResultListB = []

   try:
            
      myconn=paramiko.SSHClient()
      myconn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      myconn.connect (hostA,port=22,username=user, key_filename=kfile)
                  
      time.sleep(1)
      myconn.invoke_shell()

      outPut(hostA)
         
      stdin, stdout, stderr = myconn.exec_command (sshCommand)

      resultA=stdout.readlines()

      #for line in resultA:
         #print(line)
         #outPut(line)
      
      sshError=(stderr.read())
      outPut(sshError)
      mainCanvas.update_idletasks()

      if sshError:
         outPut(sshError)

   except paramiko.ssh_exception.AuthenticationException as e:
      outPut(e)
   except paramiko.ssh_exception.SSHException as e:
      outPut(e)
   except TimeoutError as e:
      outPut(e)
               
      myconn.close();

   try:
            
      myconn=paramiko.SSHClient()
      myconn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      myconn.connect (hostB,port=22,username=user, key_filename=kfile)
                  
      time.sleep(1)
      myconn.invoke_shell()

      outPut(hostB)
         
      stdin, stdout, stderr = myconn.exec_command (sshCommand)

      resultB=stdout.readlines()
      
      sshError=(stderr.read())
      outPut(sshError)
      mainCanvas.update_idletasks()

      if sshError:
         outPut(sshError)

   except paramiko.ssh_exception.AuthenticationException as e:
      outPut(e)
   except paramiko.ssh_exception.SSHException as e:
      outPut(e)
   except TimeoutError as e:
      outPut(e)
               
      myconn.close();

   listCompare(resultA,resultB)


      
def sqlToFile():

   getCreds()

   dba = dbaArea.get("1.0",END).rstrip()
   dbb = dbbArea.get("1.0",END).rstrip()
   sql = sqlArea.get("1.0",END).rstrip()
   sql=sql.replace(";","")
   
   dbbList = dbb.split(",")
   #print(dbbList)

   for dbbRow in dbbList:
   
      try:
            
            connection = cx_Oracle.connect(username, userpwd, dba, encoding="UTF-8")
            cursor = connection.cursor()
             
            try:
              
               csv_file = open(qresulta, "w")
               writer = csv.writer(csv_file, delimiter=',', lineterminator="\n", quoting=csv.QUOTE_NONNUMERIC)
               r = cursor.execute(sql)
               for row in cursor:
                   writer.writerow(row)

               dbaRows = r.rowcount
               cursor.close()
               connection.close()
               csv_file.close()

            except Exception as e:
               print(e)
               outPutArea.insert(END, e + "\n")
                   
      except cx_Oracle.DatabaseError as e:
            print(e)
            outPutArea.insert(END, e)

      try:
            #print(dbbRow)
            connection = cx_Oracle.connect(username, userpwd, dbbRow, encoding="UTF-8")
            cursor = connection.cursor()
             
            try:
           
               csv_file = open(qresultb, "w")
               writer = csv.writer(csv_file, delimiter=',', lineterminator="\n", quoting=csv.QUOTE_NONNUMERIC)
               r = cursor.execute(sql)
               for row in cursor:
                   writer.writerow(row)

               dbbRows = r.rowcount
               cursor.close()
               connection.close()
               csv_file.close()

            except Exception as e:
               print(e)
               outPutArea.insert(END, e)
                   
      except cx_Oracle.DatabaseError as e:
            print(e)
            outPutArea.insert(END, e)
      else:
            outPutArea.insert(END, "Table SQL Ran successfully \n")

      #print(dbbRows)
      #print(dbaRows)
      text=str(dba)+","+str(dbbRow)
      outPut(text)
      if dbbRows == dbaRows:
         simpleFileCompare(dba,dbbRow)
      else:
         text=str(dbaRows)+","+str(dbbRows)
         outPut("Results from database have different number of rows "+text)
         writeTEXT="Results from database have different number of rows "+text
         writeFile(tablereport,writeTEXT)

def simpleFileCompare(dba,dbbRow):

   if dba != "":
      global sqlMetaData
      getMetaData()
      
   sql = sqlArea.get("1.0",END).rstrip()
   dba = dba
   dbb = dbbRow
   detRbvSelect = detRbv.get()
   rowIndex=1

   timeStamp=(time.strftime("%Y%m%d %H:%M:%S"))
   #print("---------------"+timeStamp+"-----------------")
   #print(dba+" , "+dbb)
   #print(str(sqlMetaData))
   writeFile(tablereport,"------------"+timeStamp+"--------------")
   text = dba+" , "+dbb
   writeFile(tablereport,text)
   writeFile(tablereport," ")
   writeFile(tablereport,str(sqlMetaData))
   
   try:
      
      foa = open(qresulta, "r")
      fob = open(qresultb, "r")

      with open(qresulta) as textfile1, open(qresultb) as textfile2: 
         for x, y in zip(textfile1, textfile2):
            x = x.strip()
            y = y.strip()
            
            #print(x)
            hash_x = hashlib.sha1(x.encode())
            hex_x = (hash_x.hexdigest())
                        
            #print(y)
            hash_y = hashlib.sha1(y.encode())
            hex_y = (hash_y.hexdigest())

            if hex_x != hex_y:
               
               print(" ")
               print("Row "+str(rowIndex))
               writeFile(tablereport," ")
               text="Row "+str(rowIndex)
               writeFile(tablereport,text)
               


               x=x.replace('"','')
               split_x = x.split(",")
               
               y=y.replace('"','')
               split_y = y.split(",")


               #print(set(split_x) - set(split_y))
               recIndex=0
               for a,b in zip(split_x,split_y):
                 recIndex +=1
                 if a != b:
                    #print("Column "+str(recIndex))
                    #print(sqlMetaData[recIndex-1])
                    #print(a+" , "+b)
                    
                    writeFile(tablereport,sqlMetaData[recIndex-1])
                    text=a+" , "+b
                    writeFile(tablereport,text)

                    #Write report detail
                    if detRbvSelect == 2:
                       xtext = dba+" , "+x
                       ytext = dbb+" , "+y
                       writeFile(tablereport,xtext)
                       writeFile(tablereport,ytext)
               
            rowIndex +=1


      foa.close()
      fob.close()

   except IOError as e: 
         print(e)
         outPutArea.insert(END, e)

   sqlMetaData = []
   defaultOpen(docsLib,"compare_report.txt")

def getText():
   dba = dbaArea.get("1.0",END).rstrip()
   dbb = dbbArea.get("1.0",END).rstrip()
   sql = sqlArea.get("1.0",END).rstrip()
   sql=sql.replace(";","")

def clearText():
   sqlArea.delete('1.0', END)
   dbaArea.delete('1.0', END)
   dbbArea.delete('1.0', END)
   outPutArea.delete('1.0', END)
   radioa.deselect()
   radiob.deselect()
   radioc.deselect()
   rbv=0

def focus_next_widget(event):
    event.widget.tk_focusNext().focus()
    return("break")
   
#Canvas
wdt = 640
hgt = 480
root = Tk()
root.title('Database Custom Compare Report Generator')  # sets window title
root.geometry('640x480')  # sets default window size (pixels)

mainCanvas = Canvas(root, bg="light grey", height=hgt, width=wdt)

rbv = IntVar()
radioa=Radiobutton(mainCanvas, text="List Compare", variable=rbv, value=1, width=15, anchor=W, justify=LEFT)
radioa.place(x=(wdt * .05),y=(hgt * .06))
radiob=Radiobutton(mainCanvas, text="Table Compare", variable=rbv, value=2, width=15, anchor=W, justify=LEFT)
radiob.place(x=(wdt * .05),y=(hgt * .10))
radioc=Radiobutton(mainCanvas, text="Other", variable=rbv, value=3, width=15, anchor=W, justify=LEFT)
radioc.place(x=(wdt * .05),y=(hgt * .14))


typeRbv = IntVar()
radioDB=Radiobutton(mainCanvas, text="DB (SQL)", variable=typeRbv, value=1, width=15, anchor=W, justify=LEFT)
radioDB.place(x=(wdt * .35),y=(hgt * .06))
radioHost=Radiobutton(mainCanvas, text="Host (SSH)", variable=typeRbv, value=2, width=15, anchor=W, justify=LEFT)
radioHost.place(x=(wdt * .35),y=(hgt * .10))
#radioc=Radiobutton(mainCanvas, text="Other", variable=typeRbv, value=3, width=15, anchor=W, justify=LEFT)
#radioc.place(x=(wdt * .5),y=(hgt * .05))

detRbv = IntVar()
radioDB=Radiobutton(mainCanvas, text="Summary Report", variable=detRbv, value=1, width=15, anchor=W, justify=LEFT)
radioDB.place(x=(wdt * .65),y=(hgt * .06))
radioHost=Radiobutton(mainCanvas, text="Detail Report", variable=detRbv, value=2, width=15, anchor=W, justify=LEFT)
radioHost.place(x=(wdt * .65),y=(hgt * .10))


compareButton=Button(mainCanvas,text="COMPARE", width=10, fg="red", command=runCompare)
compareButton.place(x=(wdt * .82),y=(hgt * .74))

clearButton=Button(mainCanvas,text="Clear", width=10, fg="red", command=clearText)
clearButton.place(x=(wdt * .65),y=(hgt * .74))

dbaLabel=Label(mainCanvas, text='SOURCE : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=30)
dbaLabel.place (x=(wdt * .05), y=(hgt * .25))
dbaArea=Text(mainCanvas, bd=2)
dbaArea.bind("<Tab>", focus_next_widget)
dbaArea.place(x=(wdt * .18), y=(hgt * .25), width=(wdt * .2), height=(hgt * .05))

dbbLabel=Label(mainCanvas, text='COMPARATE : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=30)
dbbLabel.place (x=(wdt * .4), y=(hgt * .25))
dbbArea=Text(mainCanvas, bd=2)
dbbArea.bind("<Tab>", focus_next_widget)
dbbArea.place(x=(wdt * .55), y=(hgt * .25), width=(wdt * .2), height=(hgt * .05))

sqlAreaLabel=Label(mainCanvas, text='Search command to use for COMPARE : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=30)
sqlAreaLabel.place (x=(wdt * .05), y=(hgt * .35)) 
sqlArea=Text(mainCanvas, bd=2)
sqlArea.bind("<Tab>", focus_next_widget)
sqlArea.place(x=(wdt * .05), y=(hgt * .4), width=(wdt * .9), height=(hgt * .2))

userNameAreaLabel=Label(mainCanvas, text='Username : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=30)
userNameAreaLabel.place (x=(wdt * .05), y=(hgt * .65))
userNameArea=Text(mainCanvas, bd=2)
userNameArea.bind("<Tab>", focus_next_widget)
userNameArea.place(x=(wdt * .18), y=(hgt * .65), width=(wdt * .2), height=(hgt * .05))

pwdAreaLabel=Label(mainCanvas, text='Password : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=30)
pwdAreaLabel.place (x=(wdt * .40), y=(hgt * .65))

pwdArea=Entry(mainCanvas, bd=2, show="*")
pwdArea.place(x=(wdt * .55), y=(hgt * .65), width=(wdt * .2), height=(hgt * .05))

#pwdArea=Text(mainCanvas, bd=2, show="*")
#pwdArea.place(x=(wdt * .55), y=(hgt * .65), width=(wdt * .2), height=(hgt * .05))


outPutLabel=Label(mainCanvas, text='Message Log : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=30)
outPutLabel.place (x=(wdt * .05), y=(hgt * .75))
outPutArea=Text(mainCanvas, bd=2)
outPutArea.place(x=(wdt * .05), y=(hgt * .8), width=(wdt * .9), height=(hgt * .15))

mainCanvas.pack()

menu = Frame(root)
menu.pack()

menubar = Menu(root)

filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Open Final Report", command=donothing)
filemenu.add_command(label="Open Result A", command=donothing)
filemenu.add_command(label="Open Result B", command=donothing)
filemenu.add_command(label="Open TNS File", command=donothing)
filemenu.add_command(label="View Log", command=donothing)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=exit)
menubar.add_cascade(label="File", menu=filemenu)

helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="Help", command=donothing)
menubar.add_cascade(label="Help", menu=donothing)

root.config(menu=menubar)

#Check Windows Environment Variabels
def win_env():
   os.environ['TNS_ADMIN'] = 'C:/Users/i5desktop/Documents/' 
   test = os.getenv('TNS_ADMIN')
   print(test)
   #outPutArea.insert(END, test)

def echo_stuff():

   outPutArea.insert(END, "Current User : " + user + "\n")
   outPutArea.insert(END, "TNS_ADMIN    : " + tnsadmin + "\n")
   outPutArea.insert(END, "Doc Library  : " + docsLib + "\n")
   #outPutArea.insert(END, "Final Report : " + report + "\n")
   #outPut(hashlib.algorithms_guaranteed)

echo_stuff()

root.mainloop()
























   

"""
    
#Button Commands

def enableButtons():
    sshButton.configure(state='normal', bg="white")
    sftpButton.configure(state='normal', bg="white")
    sqlButton.configure(state='normal', bg="white")
    scriptButton.configure (state='normal', bg="white")

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

"""


