import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#api_token = '2119754502'
#api_url_base = 'https://vulnmgmt.state.mi.us/rest/'

#headers = {'Content-Type':'application/json','X-SecurityCenter':''}
headers = {'Content-Type':'application/json'}
#print (headers)

def get_single_cred():

    api_url = '{0}scan'.format(api_url_base)
    print(api_url)
    response = requests.get(api_url, headers=headers, verify=False,cookies=cookies)
    print (response.status_code)
    print (json.loads(response.content.decode('utf-8')))

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        return None



def get_token():
    data = { 'username' : 'lowej5', 'password' : 'Rock@!Egg' }
    r = requests.post('https://vulnmgmt.state.mi.us/rest/token', data=json.dumps(data), verify=False,headers=headers)
    print("---- status ----")
    print(r.status_code)
    #rint("---- raw ----")
    #print(json.loads(r.text))
    #print("---- token ----")
    #res=json.loads(r.text)
    #token=res.get('token')
    #print ("token = ",token)
    #print("---- load ----")
    #print(json.loads(r.text))

    if r.status_code==200:
         
        all_data=(r.json())
        resp=all_data["response"]
        #print (all_data)
        
        if (resp["releaseSession"]):
            print ("Release session")
            print (resp["releaseSession"])
        else:
            print ("--- token ---")
            print (resp["token"])
        
            print("---- cookie ----")
            for c in r.cookies:
                cookie_name=c.name
                cookie_value=c.value

            print(cookie_name,cookie_value)

    else:
        print("Out of Luck")
        print(r.status_code)

get_token()


def get_test():
    headers = { 'X-SecurityCenter' : '2060235765' }
    tnscookie= {'TNS_SESSIONID':'ebd239edf60effab708f607b85417c39'}
    data = {"id ": "3391"}
    r = requests.get('https://vulnmgmt.state.mi.us/rest/asset', headers=headers, verify=False, cookies=tnscookie, json=data)
    j = json.loads(r.text)
    #print(j)
    print (json.dumps(j, indent=4))

#get_test()

    
