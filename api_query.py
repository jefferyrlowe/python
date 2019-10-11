import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

api_token = '2073094558'
api_sessionid='a6ccc497e7f37aa828971604a7f6b834'
api_url_base = 'https://vulnmgmt.state.mi.us/rest/'
headers = {'Content-Type':'application/json'}

def rget(apiExt,params):
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
    data = { 'username' : 'lowej5', 'password' : 'Rock@!Egg' }
    r = requests.post('https://vulnmgmt.state.mi.us/rest/token', data=json.dumps(data), verify=False,headers=headers)
    #print("---- status ----")
    rstat=(r.status_code)

    try:
        
        all_data=(r.json())
        resp=all_data["response"]
        print("---- token ----")
        print (resp["token"])
        
        print("---- cookie ----")
        for c in r.cookies:
            cookie_name=c.name
            cookie_value=c.value

        print(cookie_name,cookie_value)

    except Exception as e:
        print (e)

def get_asset():

    params = {'id': "4114"}
    r = rget('asset',params)

    all_data=(r.json())
    resp=all_data["response"]
    print (resp["name"])
    print (resp["type"])
    print (resp["description"])
    print (resp["tags"])
    print (resp["typeFields"])

def get_creds():

    r = rget('credential','')

    all_data=(r.json())
    resp=all_data["response"]
    usable=resp["usable"]

    for c in usable:
        print ('{0:<15} {1:<15} {2:<15}'.format(c['id'],c['name'],c['type']))

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

        
def get_scans():
    r = rget('scan','')
    #j = json.loads(r.text)
    #print(j)
    #print (json.dumps(j, indent=4))
    all_data=(r.json())
    resp=all_data["response"]
    usable=resp["usable"]

    for c in usable:
        print (c)

def get_scan_runs():
    r = rget('scanResult','')
    j = json.loads(r.text)
    #print(j)
    #print (json.dumps(j, indent=4))
    all_data=(r.json())
    resp=all_data["response"]
    usable=resp["usable"]
    #print(usable)

    for c in usable:
        print (c)

def get_scan_res():
    #params = {'id': "20940"}
    r = rget('scanResult/20940','')
    j = json.loads(r.text)
    #print(j)
    print (json.dumps(j, indent=4))
    #all_data=(r.json())
    #resp=all_data["response"]
    #usable=resp["usable"]
    #print(usable)

    #for c in usable:
        #print (c)

def get_scan(id):
    params = {'id': id}
    r = rget('scan',params)
    j = json.loads(r.text)
    #print(j)
    #print (json.dumps(j["response"]["name"], indent=4))

    outPutResults=['assets','credentials']
    outPutResults=['credentials']

    for opr in outPutResults:
        all_data=(r.json())
        resp=all_data["response"]
        usable=resp[opr]

        for c in usable:
            print (json.dumps(j["response"]['name']),c)
            #print (c)
    
    
#get_token()
#get_asset()
#get_creds()
#add_cred()
#edit_cred()
#get_scans()
#get_scan()
#get_scan_runs()
#get_scan_res()

def scan_loop():
    print("scan loop")
    scan_ids="5444 5445 6918 6923 7076 7107 7458"
    scan_ids=scan_ids.split()
    for s in scan_ids:
        get_scan(s)

scan_loop()    
