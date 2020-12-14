try:
   import cx_Oracle
   from tkinter import *
   import tkinter as tk
   from tkinter.filedialog import *
   import os
   import sys
   import time
   import datetime
   import csv
   import getpass
   import hashlib
   import threading
   import paramiko
   import multiprocessing 
except ModuleNotFoundError as e:
   print(e)

desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
docsLib = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Documents')
kfile=docsLib+"/sshkey_conv"
htmlfile=desktop+"/dashboard.html"
log=docsLib+"/dashboard_log.txt"
user = os.environ.get('USERNAME')
username = "lowejef2"
userpwd = "Rock21Roll"
db = "SISMASKDV"
resultSet = []
timeStamp = []
        
def donothing():
    print("Nothing")

def defaultOpen(fname):
   try:
      os.startfile(fname);
   except IOError as e: 
      print(e)

def outPut(text):
   outPutArea.insert(END,text)
   outPutArea.insert(END,"\n")
   outPutArea.see("end")


def runSQL(sql):
   global username
   global userpwd
   global db
   sqlResult = []
   
   #print("running sql now")
   
   try:
         connection = cx_Oracle.connect(username, userpwd, db)
         cursor = connection.cursor()
         runSql = cursor.execute(sql)

         for row in runSql:
            sqlResult.append(row)

         cursor.close
         connection.close

   except cx_Oracle.DatabaseError as e:
         print("DB Error : ")
         print(e)
         print(END, e)
         #print(END, "")
   else:
         #print(sql+" COMPLETE")
         return sqlResult

def insertSQL(sql):
   global username
   global userpwd
   global db
   sqlResult = []
   
   #print("running update sql now")
   
   try:
      connection = cx_Oracle.connect(username, userpwd, db)
      cursor = connection.cursor()
      cursor.execute(sql)
      connection.commit()
      connection.close

   except cx_Oracle.DatabaseError as e:
      print("DB Error : ")
      print(e)
      print(END, e)
      #print(END, "")
      
def sshCommand(host,command):

   global kfile
   global username
   results=[]
   
   try:
      #print("try to connect "+host+" "+command)
            
      myconn=paramiko.SSHClient()
      myconn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      myconn.connect (host,port=22,username=username, key_filename = kfile)
      #print("after kfile ")
                  
      time.sleep(1)
      myconn.invoke_shell()

      #print(host)
         
      stdin, stdout, stderr = myconn.exec_command (command)

      resultLines=stdout.readlines()

      for row in resultLines:
         results.append(row)   
      #results=(stdout.read())

      sshError=(stderr.read())
      #print(sshError)
      mainCanvas.update_idletasks()

      if sshError:
         print(sshError)
      else:
         return results

   except paramiko.ssh_exception.AuthenticationException as e:
      print(e)
   except paramiko.ssh_exception.SSHException as e:
      print(e)
   except TimeoutError as e:
      print(e)
               
      myconn.close();

def getDbTimeStamp():
   global timeStamp
   tsArea.delete('1.0',END)
   timeStamp=runSQL("select to_char(systimestamp,'YYYYMMDDHH24MISS' ) from dual")

   for row in timeStamp:
      tsArea.insert(END,row)

def dashBoardList():
   global resultSet
   sql="select s.hostname,s.service_id,s.query,h.domain,s.count from lowejef2.services s, lowejef2.hosts h where s.hostname=h.hostname"
   resultSet = runSQL(sql)
   queryArea.insert(END,sql)
   numrows = len(resultSet)
   numcols = len(resultSet[0])
   hostsArea.delete('1.0',END)
   hostsArea.insert(END,numrows)
   hostsArea.insert(END," ")
   #hostsArea.insert(END,numcols)
   
   #for row in resultSet:
      #tsArea.insert(END,row)
      #print(row)

def getLastRun():
   sql="select max(status_ts) from lowejef2.status"
   resultSet = runSQL(sql)
   
   for row in resultSet:
      output("Last run timestamp: ")
      output(row)

def fullRun():
   #getDbTimeStamp()
   #mainCanvas.update_idletasks()
   #dashBoardList()
   #mainCanvas.update_idletasks()
   #getStatus()
   #MainCanvas.update_idletasks()


   if __name__ == "__main__": 
      p1 = multiprocessing.Process(target=getDbTimeStamp())
      p2 = multiprocessing.Process(target=dashBoardList())
      p3 = multiprocessing.Process(target=getStatus(),daemon=True)
      p1.start()
      print("ID of process p1: {}".format(p1.pid))
      p2.start()
      print("ID of process p2: {}".format(p2.pid))
      p3.start()
      print("ID of process p3: {}".format(p3.pid))      
            
      p1.join()
      p2.join()
      p3.join()


def getStatus():
   global resultSet
   global timeStamp
   print("getStatus")

   ts = tsArea.get("1.0",END).rstrip()
   status=[]
   
   for row in resultSet:
      host=row[0]
      service_id=row[1]
      command=row[2]
      domain=row[3]
      basecount=row[4]
      
      fullHost=host+"."+domain

      status = sshCommand(fullHost,command)
      mainCanvas.update_idletasks()

      #for row in status:
         #print("")

      numrows = len(status)
      strrows = str(numrows)

      output(host+" "+service_id+" Service count : "+strrows+"/"+basecount)
      mainCanvas.update_idletasks()
      sql="insert into lowejef2.status (status_ts, hostname, service_id,service_cnt)VALUES ('"+ts+"','"+host+"','"+service_id+"','"+strrows+"')"
      #print(sql)
      insertSQL(sql)

   output("Get status run complete")

def htmlButton():
   htmlPrep()
      
def htmlPrep():
   if os.path.isfile(htmlfile):
      os.remove(htmlfile)
   
   ts = tsArea.get("1.0",END).rstrip()

   text="""
   <!DOCTYPE html>
   <html>
   <head>
   <style>
   h1 {text-align: center;}
   p {text-align: center;}
   th {text-align: center;}
   cdiv {text-align: center;}

      .column {
     float: left;
     width: 33.33%;
   }

   /* Clear floats after the columns */
   .row:after {
     content: "";
     display: table;
     clear: both;
   }

   </style>
   </head>
   <body>
   <p><b><div><p style="background-color:FloralWhite;">Service Per Host Status  """+ts+"""</div></b></p>
   <body style="background-color:LightSkyBlue;">
      
   <div class="row">
 
   <div class="column">
   
   <table style="width:90%">
   """
   writeFile(htmlfile,text)

   htmlBody()

def htmlBody():
   ts = tsArea.get("1.0",END).rstrip()
   sql="""select s.hostname,s.app,s.service,service_cnt,h.tier,h.environment,s.count
   from lowejef2.services s, lowejef2.status t, lowejef2.hosts h
   where s.hostname=t.hostname
   and h.hostname=s.hostname
   and s.service_id=t.service_id   
   and t.status_ts='"""+ts+"""' order by s.app,h.tier,h.environment,s.hostname"""
   #and t.status_ts='20201208145058' order by s.app,h.tier,h.environment,s.hostname"""
   
   #print(sql)
   bodySet = runSQL(sql)
   rowCount=1
   rowsPerCol = rowsArea.get("1.0",END).rstrip()

   writeFile(htmlfile,"""<tr><td><d style="background-color:Crimson;">Failures</td></tr>""")   
   for row in bodySet:
      if int(row[3]) < int(row[6]):
         writeFile(htmlfile,"<tr>")
         writeFile(htmlfile,"<td>"+row[0]+"</td>")
         writeFile(htmlfile,"<td>"+str(row[1])+"</td>")
         writeFile(htmlfile,"<td>"+row[2]+"</td>")
         writeFile(htmlfile,"""<td><d style="background-color:Crimson;">"""+row[3]+" / "+row[6]+"""</td>""")
         writeFile(htmlfile,"<td>"+row[4]+"</td>")
         writeFile(htmlfile,"<td>"+row[5]+"</td>")
         writeFile(htmlfile,"</tr>")

   writeFile(htmlfile,"""<tr><td><d style="background-color:FloralWhite;">ALL Other</td></tr>""")     
   for row in bodySet:
      if int(row[3]) < int(row[6]):
         donothing()
      else:

         #Move column
         if rowCount % int(rowsPerCol) == 0:

            writeFile(htmlfile,"</table>") 
            writeFile(htmlfile,"""</div><div class="column">""")
            writeFile(htmlfile,"""<table style="width:90%"><tbody>""")
        
         writeFile(htmlfile,"<tr>")
         writeFile(htmlfile,"<td>"+row[0]+"</td>")
         writeFile(htmlfile,"<td>"+str(row[1])+"</td>")
         writeFile(htmlfile,"<td>"+row[2]+"</td>")
         
         if int(row[3]) == int(row[6]):
            writeFile(htmlfile,"<td>"+row[3]+"/"+row[6]+"</td>")
         else:
            writeFile(htmlfile,"""<td><d style="background-color:Yellow;">"""+row[3]+"/"+row[6]+"""</td>""")
            
         writeFile(htmlfile,"<td>"+row[4]+"</td>")
         writeFile(htmlfile,"<td>"+row[5]+"</td>")
         writeFile(htmlfile,"</tr>")

         rowCount += 1

   htmlEnd()
   
def htmlEnd():
   text="""
   </div>
   </div>
   </table> 
   </body>
   </html>
    """
   writeFile(htmlfile,text)

   output("HTML file created")
   defaultOpen(htmlfile)
      
def output(text):
   outPutArea.insert(END,text)
   outPutArea.insert(END,"\n")
   outPutArea.see("end")

def writeFile(writeFile,text):
   
   try:
      wFile = open(writeFile,"a")
      wFile.write(text)
      wFile.write("\n")
      wFile.flush()
   except Exception as e:
      print(e)

def focus_next_widget(event):
    event.widget.tk_focusNext().focus()
    return("break")
   
#Canvas
wdt = 640
hgt = 480
root = Tk()
root.title('HTML Dashboard Generator')  # sets window title
root.geometry('640x480')  # sets default window size (pixels)

mainCanvas = Canvas(root, bg="light grey", height=hgt, width=wdt)

compareButton=Button(mainCanvas,text="Run", width=10, fg="red", command=fullRun)
compareButton.place(x=(wdt * .8), y=(hgt * .01))

compareButton=Button(mainCanvas,text="HTML", width=10, fg="red", command=htmlButton)
compareButton.place(x=(wdt * .6), y=(hgt * .01))

tsLabel=Label(mainCanvas, text='Time Stamp : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=30)
tsLabel.place (x=(wdt * .01), y=(hgt * .1))
tsArea=Text(mainCanvas, bd=2)
tsArea.bind("<Tab>", focus_next_widget)
tsArea.place(x=(wdt * .2), y=(hgt * .1), width=(wdt * .4), height=(hgt * .05))

rowsLabel=Label(mainCanvas, text='Rows per Column : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=30)
rowsLabel.place (x=(wdt * .65), y=(hgt * .1))
rowsArea=Text(mainCanvas, bd=2)
rowsArea.bind("<Tab>", focus_next_widget)
rowsArea.place(x=(wdt * .85), y=(hgt * .1), width=(wdt * .1), height=(hgt * .05))
rowsArea.insert(END,"30")

hostsLabel=Label(mainCanvas, text='Hosts to conatct : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=30)
hostsLabel.place (x=(wdt * .01), y=(hgt * .2))
hostsArea=Text(mainCanvas, bd=2)
hostsArea.bind("<Tab>", focus_next_widget)
hostsArea.place(x=(wdt * .2), y=(hgt * .2), width=(wdt * .4), height=(hgt * .05))

queryLabel=Label(mainCanvas, text='Setup Query : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=50)
queryLabel.place (x=(wdt * .01), y=(hgt * .3))
queryArea=Text(mainCanvas, bd=2)
queryArea.bind("<Tab>", focus_next_widget)
queryArea.place(x=(wdt * .2), y=(hgt * .3), width=(wdt * .6), height=(hgt * .15))

outPutLabel=Label(mainCanvas, text='Message Log : ', fg="black", anchor=W, justify=LEFT, bg="light grey", width=30)
outPutLabel.place (x=(wdt * .05), y=(hgt * .55))
outPutArea=Text(mainCanvas, bd=2)
outPutArea.place(x=(wdt * .05), y=(hgt * .6), width=(wdt * .9), height=(hgt * .35))

mainCanvas.pack()
getLastRun()

"""
if __name__ == "__main__": 
   p1 = multiprocessing.Process(target=getLastRun())
   p1.start()
   p1.join() 

"""

def htmlheader():
   
   ts = tsArea.get("1.0",END).rstrip()
   sql="select hostname from lowejef2.status where status_ts='"+ts+"'"
   hostSet = runSQL(sql)

   for row in hostSet:
      host=row[0]
      writeFile(htmlfile,"""<th><div style="writing-mode: tb-rl; background-color:FloralWhite;">"""+host+"</div></th>")
      
   writeFile(htmlfile,"<tr>")


   
def htmldata():
   ts = tsArea.get("1.0",END).rstrip()
   sql="select s.app||' '||s.service from lowejef2.services s, lowejef2.status t where s.hostname=t.hostname and s.service_id=t.service_id and t.status_ts='"+ts+"'"
   serviceSet = runSQL(sql)

   writeFile(htmlfile,"<tr>")
   writeFile(htmlfile,"""<td width="(100/3)%"><p style="background-color:FloralWhite;">""" "</p></td>")
   
   for row in serviceSet:
      service_id=row[0]
      writeFile(htmlfile,"<tr>")
      writeFile(htmlfile,"""<td width="(100/3)%"><p style="background-color:FloralWhite;">"""+service_id+"</p></td>")
      writeFile(htmlfile,"</tr>")

   writeFile(htmlfile,"</tr>")

