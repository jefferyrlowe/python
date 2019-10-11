import tkinter as tk
from tkinter import *
import json
import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

api_token = '2028347509'
api_sessionid='836693639f88372215f300fa418a6d3a'
api_url_base = 'https://vulnmgmt.state.mi.us/rest/'
headers = {'Content-Type':'application/json'}

paramText=''
apiExtText=''
tkvar=''

# creating tkinter window 
root = Tk() 
root.title('Tenable.sc API Client') 
root.geometry('1450x1000') 
#Label(root, text = 'It\'s resizable').pack(side = TOP, pady = 10) 
root.resizable(True, True) 

def donothing():
    print ("nothing")

def rget(apiExt,params):
    api_token = tokenText.get('1.0',END)
    api_token=api_token.replace("\n","")
    #outPut(api_token)
    api_sessionid=cookieText.get('1.0',END)
    api_sessionid=api_sessionid.replace("\n","")
    #outPut(api_sessionid)
    headers = { 'X-SecurityCenter' : api_token }
    tnscookie= {'TNS_SESSIONID': api_sessionid }
    if params:
        r = requests.get(api_url_base+apiExt, headers=headers, verify=False, cookies=tnscookie, params=params)
    else:
        r = requests.get(api_url_base+apiExt, headers=headers, verify=False, cookies=tnscookie)
    return r
    
def rpatch(apiExt,params):
    headers = { 'X-SecurityCenter' : api_token }
    tnscookie= {'TNS_SESSIONID': api_sessionid }
    r = requests.patch(api_url_base+apiExt, headers=headers, verify=False, cookies=tnscookie, params=params)
    return r

def get_token():
    data = { 'username' : 'lowej5', 'password' : 'Rock@!Rolls' }
    r = requests.post('https://vulnmgmt.state.mi.us/rest/token', data=json.dumps(data), verify=False,headers=headers)
    #print("---- status ----")
    rstat=(r.status_code)

    try:
        
        all_data=(r.json())
        resp=all_data["response"]
        outPut(resp)
        outPut("---- token ----")
        outPut (resp["token"])
        tokenText.insert(END,resp["token"])
        
        outPut("---- cookie ----")
        for c in r.cookies:
            cookie_name=c.name
            cookie_value=c.value

        outPut(cookie_name)
        outPut(cookie_value)
        cookieText.insert(END,cookie_value)

    except Exception as e:
        outPut (e)

def get_assets():

    #params = {'id': "4114"}
    r = rget('asset','')

    all_data=(r.json())
    resp=all_data["response"]

    resultListBox.delete(0,END)
    outPutArea.delete('1.0',END)
    
    parseResp(resp)
    
def get_creds():

    r = rget('credential','')

    all_data=(r.json())
    resp=all_data["response"]
    usable=resp["usable"]
    j = json.loads(r.text)

    resultListBox.delete(0,END)
    outPutArea.delete('1.0',END)
    
    parseResp(resp)

def get_cred():

    #params={"id" : "1000158"}
    params=paramText.get('1.0',END)
    #params=str(params)
    params=params.replace("\\","")
    params=params.replace("'","")
    params=params.replace("\n","")
    #params = re.sub(r'([^\s\w]|_)+', '', params)
    pp={params}
    #params={"id" : "1000158"}
    print(params)
    
    #r = rget('credential',pp)
    r = rget('credential',params)
    j = json.loads(r.text)
    
    resultListBox.delete(0,END)
    outPutArea.delete('1.0',END)
    
    activateOutPut()

    outPutArea.insert(END,(params))
    
    #JSON Object raw output
    outPutArea.insert('1.0',j)

    #JSON Object pretty output
    #rec=(json.dumps(j, indent=1))
    #outPutArea.insert('1.0',rec)

    #paramText.insert(END,j)
   
    
    '''
    all_data=(r.json())
    resp=all_data["response"]
    
    #JSON Object parse
    for key, value in resp.items():
        outPut(key)
        if str(key)=="id":
            resultListBox.insert(END,key+": "+value)
   
        if str(key)=="name":
            resultListBox.insert(END,key+": "+value)
            
        for v in value:
            for key in v:
                outPutArea.insert(END,str(key))
                    
        outPut(" ")
    '''

            
    
def add_cred():
    headers = { 'X-SecurityCenter' : api_token }
    tnscookie= {'TNS_SESSIONID': api_sessionid }
    params = {"name" : "test_name",
    "tags" : "test tags",
    "description" : "test desc",
    "type" : "database",
    "dbType" : "Oracle",
    "authType" : "password",
    "password" : "temp1233PWD",
    "login" : "tenable_user",
    "oracleAuthType" : "normal",
    "oracle_service_type" : "SID",
    "sid" : "test1dv",
    "port" : "1521"}
    r = requests.post('https://vulnmgmt.state.mi.us/rest/credential', headers=headers, verify=False, cookies=tnscookie, params=params)
    j = json.loads(r.text)
    print (json.dumps(j, indent=4))

def edit_cred():

    params = {"password" : "0JwpfLEfa7dR3kBYWLHOcLRP"}
    r = rpatch ('credential/1000099',params)
    j = json.loads(r.text)
    print (json.dumps(j, indent=4)) 

def parseResp(indict):
    outPut("Response")
    
    for key, value in indict.items():
        outPut(key)
        for v in value:
            for key in v:
                outPutArea.insert(END,key+": ")
                outPutArea.insert(END,v[key]+" ")
                if str(key)=="id":
                    listItem=v[key]
                if str(key)=="name":
                    listItem=listItem+": "+v[key]
                    resultListBox.insert(END, listItem)
                    listItem=''
                    
            outPut(" ")

def activateOutPut():

    outPutArea.lift()
    outPutArea.focus()
    outPutArea.place(x=500, y=40, width=900, height=880)
    outPutArea.delete('1.0',END)
    
    enableButtons()
    outputButton.configure (state='disabled', bg="yellow")

def activateParam():

    paramArea.lift()
    paramArea.focus()
    paramArea.place(x=500, y=40, width=900, height=880)
    paramArea.delete('1.0',END)

    enableButtons()
    paramButton.configure (state='disabled', bg="yellow")

    apiExtLabel=Label(mainCanvas)
    apiExtLabel.config(text="API Extention credential/100012")
    apiExtLabel.place(x=550, y=75)
    '''
    global apiExtText
    apiExtText=Text(mainCanvas, bd=3)
    apiExtText.insert(END,"credential/1000099")
    apiExtText.place(x=550, y=105, width=600, height=25)
    '''
    tkvar = StringVar(root)
    choices = { 'asset','credential','scan','scanResult' }
    apiExtMenu = OptionMenu(mainCanvas, tkvar, *choices)
    Label(mainCanvas, text="Choose an API Extention")
    apiExtMenu.place(x=550, y=105, width=600, height=25)
    

    paramLabel=Label(mainCanvas)
    paramLabel.config(text="Parameters {Body}")
    paramLabel.place(x=550, y=170)
    global paramText
    paramText=Text(mainCanvas, bd=3)
    paramText.insert(END,"{}")
    paramText.place(x=550, y=200, width=600, height=300)

    getButton=Button(mainCanvas,text="Get", width=10, command=get_cred)
    getButton.place(x=550,y=530)
    patchButton=Button(mainCanvas,text="Patch", width=10, command=donothing)
    patchButton.place(x=650,y=530)
    #ActionButton.config(state='normal', text="Run Command", command=sshCommand)

    listAvailable()

def listAvailable():
    listApisText=Text(mainCanvas, bd=0)
    #listApisText.insert(END,"Available APIs \n")
    #listApisText.insert(END,"asset,credential,scan,scanResult")
    listApisText.place(x=550, y=580, width=600, height=300)

def enableButtons():
    outputButton.configure(state='normal', bg="white")
    paramButton.configure(state='normal', bg="white")
    
def outPut(text):
    outPutArea.insert(END,repr(text))
    outPutArea.insert(END,"\n")

def clearOutPut():  outPutArea.delete('1.0',END)

def exitProgram():
    root.quit()
    root.destroy()


def topMenu():

    #menu = Frame(root, width=800, height=3, bg="black")
    menu = Frame(root)
    menu.pack()
    #menu.bind_all("<Control-b>", controlB)
    menubar = Menu(root)

    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open File", command=donothing)
    filemenu.add_command(label="Save", command=donothing)
    filemenu.add_command(label="Clear <ctrl b>", command=clearOutPut)
    filemenu.add_command(label="View Log", command=donothing)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=exitProgram)
    menubar.add_cascade(label="File", menu=filemenu)

    listmenu = Menu(menubar, tearoff=0)
    #listmenu.add_command(label="Token", command=get_token)
    #listmenu.add_separator()
    listmenu.add_command(label="Credentials", command=get_creds)
    listmenu.add_command(label="Assets", command=get_assets)
    menubar.add_cascade(label="List", menu=listmenu)

    getmenu = Menu(menubar, tearoff=0)
    getmenu.add_command(label="Token", command=get_token)
    getmenu.add_separator()
    getmenu.add_command(label="Credential", command=get_creds)
    getmenu.add_command(label="Asset", command=get_assets)
    menubar.add_cascade(label="Get", menu=getmenu)

    
    '''
    dbmenu = Menu(menubar, tearoff=0)
    dbmenu.add_command(label="Update List", command=oraDBlistbox)
    dbmenu.add_separator()
    dbmenu.add_command(label="Edit DB File", command=openOraDbFile)
    menubar.add_cascade(label="Databases", menu=dbmenu)

    '''
    root.config(menu=menubar)
    
scrollbar = tk.Scrollbar(root, orient="horizontal")

mainCanvas = Canvas(root, bg="light grey", height=900, width=900)
mainCanvas.pack(fill="both", expand=True)

tokenLabel=Label(mainCanvas, text='Token', width=15)
tokenLabel.place (x=10, y=6)

tokenText=Text(mainCanvas, bg="light grey")
tokenText.insert(END,api_token)
tokenText.place(x=120, y=5, width=100,height=22)

cookieLabel=Label(mainCanvas, text='Cookie', width=15)
cookieLabel.place (x=250, y=6)

cookieText=Text(mainCanvas, bg="light grey")
cookieText.insert(END,api_sessionid)
cookieText.place(x=350, y=5, width=300,height=22)

resultListBox = Listbox(mainCanvas,height=25, width=68, bd=5,selectmode=tk.SINGLE, activestyle='dotbox',yscrollcommand=scrollbar.set)
resultListBox.place(x=10, y=40, width=400, height=880)
#scrollbar.config(command=resultListBox.yview)
#scrollbar.pack(side="right", fill="y")

resultListBox = Listbox(mainCanvas,height=25, width=68, bd=5,selectmode=tk.SINGLE, activestyle='dotbox',yscrollcommand=scrollbar.set)
resultListBox.place(x=10, y=40, width=400, height=880)

paramArea=Text(mainCanvas, bd=3)
#paramArea.place(x=500, y=40, width=900, height=880)

outPutArea=Text(mainCanvas, bd=3)
#outPutArea.place(x=500, y=40, width=900, height=880)

outputButton=Button(mainCanvas,text="OutPut", width=10, command=activateOutPut)
outputButton.place(x=420,y=60)
paramButton=Button(mainCanvas,text="Parameters", width=10, command=activateParam)
paramButton.place(x=420,y=90)




activateOutPut()
topMenu()
mainloop()

