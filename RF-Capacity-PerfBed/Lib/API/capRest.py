#-*-coding:utf-8-*-
import requests
import json
import urllib3
import pyotp
import os
urllib3.disable_warnings()






class capRest:

    def __init__(self, username, password):
        self.username = username
        self.password = password

    # Get current One-time Password
    def getOTP(self,secretKey):
        totp = pyotp.TOTP(secretKey)
        cur_otp = totp.now()
        return cur_otp


	# Create a file to save token
    def base_dir(self):
        return os.path.join(os.path.dirname(__file__), 'token.md')


	# Read token
    def getToken(self):
        with open(self.base_dir(), 'r') as f:
            return f.read()		


    # Login
    def Login(self,ipstr,secretKey):
        cur_otp = self.getOTP(secretKey)
        url = 'https://' + ipstr + '/api/sonicos/tfa'
        body = {'user': self.username, 'password': self.password, 'tfa': cur_otp, 'override': True}
        headers = {'Accept': 'application/json', 'Accept-Encoding': 'application/json'}
        r = requests.post(url, data=json.dumps(body), headers=headers, verify=False)
        res = str(r.content)
        token = res.split('BearToken: ')[-1].split('\"')[0]
        with open(self.base_dir(), 'w') as f:
            f.write(token)
        if (r.status_code == 200):
            print("Login successful." + "token:" + token)
        else:
            print ("status_code for login=" + str(r.status_code))
            print ("Login failed,please check session is valid.")
        return token

    # Logout
    def Logout(self,ipstr):
        url = 'https://' + ipstr + '/api/sonicos/auth'
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        r = requests.delete(url, headers=headers, verify=False)
        if (r.status_code == 200):
            print ("Logout successfully!")
        else:
            print ("status_code for logout=" + str(r.status_code))
            print ("Logout failed!")


    # Post data
    def post(self,ipstr,num):
        url = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        for i in range(num):
            name = "addr" + str(i)
            zone = "LAN"
            a = 1
            b = 1
            c = 1
            a += 1
            if a >= 255:
                a = 1
                b += 1
                if b >=255:
                    b = 1
                    c +=1
            host_ip = "18." +str(c)+ "."+str(b) + "." + str(a)
            body = {
                "address_objects": [
                    {
                        "ipv4": {
                            "name": name,
                            "zone": zone,
                            "host": {
                                "ip": host_ip
                            }
                        }
                    }
                ]
            }
            r = requests.post(url, data=json.dumps(body), headers=headers, verify=False)
            if (r.status_code == 200):
                print ("Post " + str(i + 1) + " object successfully!")
            else:
                print ("status_code for post=" + str(r.status_code))
                print ("Post" + str(i + 1) + "object failed!please check session is valid or objects added is exist")
            url1 = 'https://' + ipstr + '/api/sonicos/config/pending'
            r1 = requests.post(url1, headers=headers, verify=False)
            if (r1.status_code == 200):
                print ("Commit all pending configuration successfully!")
            else:
                print ("status_code for commit=" + str(r1.status_code))
                print ("Commit failed,please check session is valid.")

    # Commit configuration
    def commit(self,ipstr):
        url = 'https://' + ipstr + '/api/sonicos/config/pending'
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        r = requests.post(url, headers=headers, verify=False)
        if (r.status_code == 200):
            print ("Commit all pending configuration successfully!")
        else:
            print ("status_code for commit=" + str(r.status_code))
            print ("Commit failed,please check session is valid.")


	#address objects
    def getAO(self,ipstr):
        url = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        r = requests.get(url, headers=headers, verify=False)
        ss = r.json()
        list = ss["address_objects"]
        num = len(list)
        if (r.status_code == 200):
            print ("Current objects number=" + str(num))
        else:
            print ("status_code for get=" + str(r.status_code))
            print ("Get failed,please check session is valid.")
        return (num)


    def addAO(self,ipstr,num):
        url = 'https://'+ipstr+'/api/sonicos/address-objects/ipv4'
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        a = 1
        b = 1
        c = 1
        #Post objects 30 by 30
        loop_num=num/30
        last_num=num%30
        for j in range(loop_num):
            value_list=[]
            for i in range(j*30,(j+1)*30):
                name1="addr"+str(i)
                zone1="LAN"
                if a >= 255:
                    a = 1
                    b += 1
                    if b >= 255:
                        b = 1
                        c += 1
                host_ip1 = "19." + str(c) + "." + str(b) + "." + str(a)
                dic1={}
                dic={"ipv4":dic1}
                named=name1
                zoned=zone1
                hostd={"ip":host_ip1}
                dic1["name"]=named
                dic1["zone"]=zoned
                dic1["host"]=hostd
                value_list.append(dic)
                a += 1
            body = {"address_objects": value_list}
            data=json.dumps(body)
            print(data)
            r = requests.post(url, data=data, headers=headers, verify=False)
            print(r.status_code)
            if (r.status_code == 200):
                print ("Post "+str(loop_num*30)+ " object successfully!")
            else:
                print ("status_code for post="+str(r.status_code))
                print ("Post"+str(loop_num*30)+ "object failed!please check session is valid or objects added is exist")
            url1 = 'https://' + ipstr + '/api/sonicos/config/pending'
            r1 = requests.post(url1, headers=headers, verify=False)
            if (r1.status_code == 200):
                print ("Commit all pending configuration successfully!")
            else:
                print ("status_code for commit=" + str(r1.status_code))
                print ("Commit failed,please check session is valid.")

        if last_num != 0:
            for s in range(num-last_num,num):
                name = "addr" + str(s)
                zone = "LAN"
                a = 1
                b = 1
                c = 1
                a += 1
                if a >= 255:
                    a = 1
                    b += 1
                    if b >=255:
                        b = 1
                        c +=1
                host_ip = "19." +str(c)+ "."+str(b) + "." + str(a)
                body = {
                    "address_objects": [
                        {
                            "ipv4": {
                                "name": name,
                                "zone": zone,
                                "host": {
                                    "ip": host_ip
                                }
                            }
                        }
                    ]
                }
                r = requests.post(url, data=json.dumps(body), headers=headers, verify=False)
                if (r.status_code == 200):
                    print ("Post " + str(i + 1) + " object successfully!")
                else:
                    print ("status_code for post=" + str(r.status_code))
                    print ("Post" + str(i + 1) + "object failed!please check session is valid or objects added is exist")
                url1 = 'https://' + ipstr + '/api/sonicos/config/pending'
                r1 = requests.post(url1, headers=headers, verify=False)
                if (r1.status_code == 200):
                    print ("Commit all pending configuration successfully!")
                else:
                    print ("status_code for commit=" + str(r1.status_code))
                    print ("Commit failed,please check session is valid.")



    def delAO(self,ipstr,num):
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        for i in range(num):
            name = "addr" + str(i)
            url = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4/name/' + name
            r = requests.delete(url, headers=headers, verify=False)
            if (r.status_code == 200):
                print ("Delete " + name + " successfully!")
            else:
                print ("status_code for delete=" + str(r.status_code))
                print ("delete " + name + " failed!")
        url1 = 'https://' + ipstr + '/api/sonicos/config/pending'
        r1 = requests.post(url1, headers=headers, verify=False)
        if (r1.status_code == 200):
            print ("Commit all pending configuration successfully!")
        else:
            print ("status_code for commit=" + str(r1.status_code))
            print ("Commit failed,please check session is valid.")

	#service objects
    def getSO(self,ipstr):
        url = 'https://' + ipstr + '/api/sonicos/service-objects'
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        r = requests.get(url, headers=headers, verify=False)
        ss = r.json()
        list = ss["service_objects"]
        num = len(list)
        if (r.status_code == 200):
            print ("Current objects number=" + str(num))
        else:
            print ("status_code for get=" + str(r.status_code))
            print ("Get failed,please check session is valid.")
        return (num)

    def addSO(self,ipstr,num):
        url = 'https://' + ipstr + '/api/sonicos/service-objects'
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        for i in range(num):
            name = "service"+str(i)
            body = {
                "service_objects": [
                    {
                            "name": name,
                            "tcp":{
                            	"begin":2,
                            	"end":10
                            }
                        }
                ]
            }
            r = requests.post(url, data=json.dumps(body), headers=headers, verify=False)
            if (r.status_code == 200):
                print ("Post " + str(i + 1) + " object successfully!")
            else:
                print ("status_code for post=" + str(r.status_code))
                print ("Post " + str(i + 1) + " object failed!please check session is valid or objects added is exist")
        url1 = 'https://' + ipstr + '/api/sonicos/config/pending'
        r1 = requests.post(url1, headers=headers, verify=False)
        if (r1.status_code == 200):
            print ("Commit all pending configuration successfully!")
        else:
            print ("status_code for commit=" + str(r1.status_code))
            print ("Commit failed,please check session is valid.")

    def delSO(self,ipstr,num):
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        for i in range(num):
            name = "service" + str(i)
            url = 'https://' + ipstr + '/api/sonicos/service-objects/name/' + name
            r = requests.delete(url, headers=headers, verify=False)
            if (r.status_code == 200):
                print ("Delete " + name + " successfully!")
            else:
                print ("status_code for delete=" + str(r.status_code))
                print ("delete " + name + " failed!")
        url1 = 'https://' + ipstr + '/api/sonicos/config/pending'
        r1 = requests.post(url1, headers=headers, verify=False)
        if (r1.status_code == 200):
            print ("Commit all pending configuration successfully!")
        else:
            print ("status_code for commit=" + str(r1.status_code))
            print ("Commit failed,please check session is valid.")
			
			
#schedule objects
    def getSchedules(self,ipstr):
        url = 'https://' + ipstr + '/api/sonicos/schedules'
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        r = requests.get(url, headers=headers, verify=False)
        ss = r.json()
        list = ss["schedules"]
        num = len(list)
        if (r.status_code == 200):
            print ("Current objects number=" + str(num))
        else:
            print ("status_code for get=" + str(r.status_code))
            print ("Get failed,please check session is valid.")
        return (num)

    def addSchedules(self,ipstr,num):
        url = 'https://' + ipstr + '/api/sonicos/schedules'
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        loop_num=num/8
        last_num=num%8
        for j in range(loop_num):
            value_list=[]
            for i in range(j*8,(j+1)*8):
                name = "sche"+str(i)
                occurs ={"once": {"event": [{"start": "2000:10:02:10:10","end": "2001:10:02:10:10"}]}}
                named=name
                occursd=occurs
                dic={}
                dic["name"]=named
                dic["occurs"]=occurs
                value_list.append(dic)
                body={"schedules":value_list}
                data=json.dumps(body)
            r = requests.post(url, data=data, headers=headers, verify=False)
            print(data)
            if (r.status_code == 200):
                print ("Post " + str(i + 1) + " object successfully!")
            else:
                print ("status_code for post=" + str(r.status_code))
                print ("Post " + str(i + 1) + " object failed!please check session is valid or objects added is exist")
            url1 = 'https://' + ipstr + '/api/sonicos/config/pending'
            r1 = requests.post(url1, headers=headers, verify=False)
            if (r1.status_code == 200):
                print ("Commit all pending configuration successfully!")
            else:
                print ("status_code for commit=" + str(r1.status_code))
                print ("Commit failed,please check session is valid.")

        if last_num != 0:
            last_list=[]				
            for i in range(num-last_num,num):
                name = "schel"+str(i)
                body = {
                     "schedules": [
                        {
                             "name": name,
                             "occurs": {
                                "once": {
                                     "event": [
                                          {
                                            "start": "2000:10:02:10:10",
                                            "end": "2001:10:02:10:10"
                            }
                         ]
                     }
                }
            }
        ]
    }
                data=json.dumps(body)
                r = requests.post(url, data=data, headers=headers, verify=False)
                print(data)
                if (r.status_code == 200):
                    print ("Post " + str(i + 1) + " object successfully!")
                else:
                    print ("status_code for post=" + str(r.status_code))
                    print ("Post " + str(i + 1) + " object failed!please check session is valid or objects added is exist")
                url1 = 'https://' + ipstr + '/api/sonicos/config/pending'
                r1 = requests.post(url1, headers=headers, verify=False)
                if (r1.status_code == 200):
                    print ("Commit all pending configuration successfully!")
                else:
                    print ("status_code for commit=" + str(r1.status_code))
                    print ("Commit failed,please check session is valid.")

    def delSchedules(self,ipstr,num):
        headers = {'Authorization': 'Bearer ' + self.getToken(), 'Accept-Encoding': 'application/json'}
        for i in range(num):
            name = "sche" + str(i)
            url = 'https://' + ipstr + '/api/sonicos/schedules/name/' + name
            r = requests.delete(url, headers=headers, verify=False)
            if (r.status_code == 200):
                print ("Delete " + name + " successfully!")
            else:
                print ("status_code for delete=" + str(r.status_code))
                print ("delete " + name + " failed!")
            url1 = 'https://' + ipstr + '/api/sonicos/config/pending'
            r1 = requests.post(url1, headers=headers, verify=False)
            if (r1.status_code == 200):
                print ("Commit all pending configuration successfully!")
            else:
                print ("status_code for commit=" + str(r1.status_code))
                print ("Commit failed,please check session is valid.")
