#-*-coding:utf-8-*-

import requests
import re
from requests.auth import HTTPBasicAuth
import json
import pyotp
import os,time
import urllib3
import time
import functools
import csv
import xlrd
import xlwt
import telnetlib
import datetime
import sys
import logging
import random
urllib3.disable_warnings()

LOG_FORMAT="%(asctime)s %(name)s %(levelname)s %(message)s"
DATE_FORMAT="%Y-%m-%d %H:%M:%S"
LOG_PATH=os.getcwd()+'test.log'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    filename=LOG_PATH
    # filemode="w"
)


class apiRest:

    def __init__(self,username,password):
        self.username = username
        self.password = password

    def get_info(self,model):
        filename = os.getcwd()+'\\topology.xlsx'
        data = self.read_xls_file(filename, self.model)
        type_list = list(data)
        ipstr = type_list[0]["HOST_IP"]
        console_server = type_list[0]["CONSOLE_SERVER"]
        console_port = int(float(type_list[0]["CONSOLE_TELNETPORT"]))
        return ipstr,console_server,console_port


    def do_telnet(self,host,port,time):
        telobj = telnetlib.Telnet(host,port,timeout=10)
        telobj.set_debuglevel(2)
        try:
            telobj.read_until('login:')
            telobj.write('root' + '\r')
            telobj.read_until('Password:')
            telobj.write('123456' + 'r')
            time.sleep(0.3)
            telobj.write('\r')
            command_res = telobj.read_some()
            if 'User:' in command_res:
                telobj.write('admin' + '\r')
                telobj.read_until('Password:')
                telobj.write('password' + '\r')
                telobj.write('\r')
            elif '#' in command_res:
                for count in range(0,3):
                    telobj.write('cancel' | '\r')
            elif '->' in command_res:
                telobj.write('exit' + '\r')
                telobj.write('\r')
            elif '--MORE--' in command_res:
                for i in range(3):
                    telobj.write(chr(32))
            elif '[cancel]' in command_res:
                telobj.write('\r')
            else:
                telobj.write('\r')
            time.sleep(time)
            # all_res = telobj.read_very_eager()
            # all_res = telobj.read()
            result = telobj.read()
            print ("result {}".format(result))
            if "tracelog" in result:
                print "console crashed."
            # pattern = "User"
            # reg = re.compile(pattern)
            # idx,obj,response = telobj.expect(reg,timeout=time)
            # print idx,obj,response
            all_res = result
            telobj.close()
        except:
            telobj.close()
            all_res = "console_fail"
        return all_res


    def xls_to_csv(self,filename, wsheet):
        wb = xlrd.open_workbook(filename)
        sh = wb.sheet_by_name(wsheet)
        curr_dir = os.getcwd()
        csvfile = curr_dir + '\\tmp.csv'
        with open(csvfile, 'wb') as f:
            wr = csv.writer(f, quoting=csv.QUOTE_ALL)
            for rownum in xrange(sh.nrows):
                wr.writerow(sh.row_values(rownum))

    def read_csv_file(self,filename):
        f = open(filename)
        csv_dict = csv.DictReader(f)
        # with open(fiame,len'r') as f:
        #     csv_dict = csv.DictReader(f)
        return csv_dict

    def read_xls_file(self,filename, worksheet):
        self.xls_to_csv(filename, worksheet)
        curr_dir = os.getcwd()
        cf = curr_dir + "\\tmp.csv"
        xls_data = self.read_csv_file(cf)
        return xls_data

    def login(self,ipstr):
        url = 'https://' + ipstr + '/api/sonicos/auth'
        body = {'override': True}
        headers = {'Content-Type': 'application/json', 'Accept-Encoding': 'application/json'}
        try:
            r = requests.post(url, auth=HTTPBasicAuth('admin', 'password'), data=json.dumps(body), headers=headers,
                              verify=False)
            msg_res = r.json()['status']['info'][0]['message']
            if (r.status_code==200):
                print("Login successful.")
                logging.info("login response msg:{}".format(msg_res))
            else:
                logging.error("login error msg:{}".format(msg_res))
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print "- LoginERROR - Web service exception, msg = {}".format(e)
            
    def set_configMode(self, ipstr):
        url = 'https://' + ipstr + '/api/sonicos/config-mode'
        body = {}
        headers = {'Content-Type': 'application/json', 'Accept-Encoding': 'application/json'}
        try:
            r = requests.post(url,data=body, headers=headers,verify=False)
            msg_res = r.json()['status']['info'][0]['message']
            logging.info("set config mode response msg:{}".format(msg_res))
            if (r.status_code == 200):
                print("set config mode successful.")
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print "- set_config_mode_ERROR - Web service exception, msg = {}".format(e)


    def get_objects(self,ipstr,casename,location_script):
        filename = location + "/api_url_info.xlsx"
        print filename
        data = self.read_xls_file(filename, 'get_object')
        content_get = list(data)
        link = content_get[0][casename]
        json_obj = content_get[1][casename]
        url = 'https://' + ipstr + '/api/sonicos/' + link
        headers = {'Content-Type': 'application/json'}
        try:
            r = requests.get(url, headers=headers, verify=False)
            ss = r.json()
            ll = ss[json_obj]
            num = len(ll)
            if (r.status_code==200):
                print("Current {} is {}".format(casename,num))
            r.raise_for_status()
            return (num)
        except requests.exceptions.RequestException as e:
            print "- GetERROR - Web service exception, msg = {}".format(e)

    def export_coredump(self,ipstr,filepath,query):
        url = 'https://' + ipstr + '/api/sonicos/export/core-dump' +query
        try:
            r = requests.get(url, verify=False)
            if (r.status_code==200):
                print("export core dump successfully")
                with open(filepath, "wb") as f:
                    f.write(r.content)
            else:
                msg_r = r.json()['status']['info'][0]['message']
                t = datetime.datetime.now()
                logging.error("{}-API_URL:{}".format(t,url))
                logging.error("-export error message: {}".format(msg_r))
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print "- GetERROR - Web service exception, msg = {}".format(e)

    def export_config(self,ipstr,filepath):
        url = 'https://' + ipstr + '/api/sonicos/export/current-config/exp'
        try:
            r = requests.get(url, verify=False)
            if (r.status_code==200):
                print("export config successfully")
                with open(filepath, "wb") as f:
                    f.write(r.content)
            else:
                msg_r = r.json()['status']['info'][0]['message']
                t = datetime.datetime.now()
                logging.error("{}-API_URL:{}".format(t,url))
                logging.error("-export error message: {}".format(msg_r))
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print "- GetERROR - Web service exception, msg = {}".format(e)

    def export_tsr(self,ipstr,filepath):
        url = 'https://' + ipstr + '/api/sonicos/export/tech-support-report'
        try:
            r = requests.get(url, verify=False)
            if (r.status_code==200):
                print("export TSR successfully")
                with open(filepath, "wb") as f:
                    f.write(r.content)
            else:
                msg_r = r.json()['status']['info'][0]['message']
                t = datetime.datetime.now()
                logging.error("{}-API_URL:{}".format(t,url))
                logging.error("-export tsr error message: {}".format(msg_r))
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print "- GetERROR - Web service exception, msg = {}".format(e)
        

    def post(self,ipstr, casename, num):
        url = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        headers = {'Content-Type': 'application/json'}
        # if casename=='address object':
        os.path.join(os.path.dirname(__file__), 'addressObj.json')
        for i in range(num):
            jsonname = casename + str(i) + '.json'
            with open('addressObject1.json', 'r') as f2:
                params = json.load(f2)
                # print params['address_objects']
                # b = params['address_objects']
            data = json.dumps(params)
            print data
            try:
                r = requests.post(url, data=data, headers=headers, verify=False, timeout=20)
                if (r.status_code == 200):
                    print ("Post successfully!")
                r.raise_for_status()
            except requests.exceptions.RequestException as e:
                print "- PostERROR - Web service exception, msg = {}".format(e)

    def get_SystemInfo(self,ipstr,infoname,location,filepath):
        self.login(ipstr)
        filename = location + "/api_url_info.xlsx"
        data = self.read_xls_file(filename, 'system_info')
        content_get = list(data)
        url_tail = content_get[0][infoname]
        url_head = 'https://' + ipstr + '/api/sonicos/'
        url = url_head + url_tail
        headers = {'Content-Type': 'application/json'}
        save_name=filepath+'/'+infoname+'.json'
        try:
            r = requests.get(url, headers=headers, verify=False)
            if (r.status_code==200):
                print("Get {} successfully".format(infoname))
                with open(save_name, "wb") as f:
                    f.write(r.content)
            else:
                msg_r = r.json()['status']['info'][0]['message']
                logging.info("-get info message: {}".format(msg_r))
                t = datetime.datetime.now()
                logging.error("{}-API_URL:{}".format(t,url))
                logging.error("-get error message: {}".format(msg_r))
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print "- GetERROR - Web service exception, msg = {}".format(e)  


    def restart_box(self,ipstr):
        url = 'https://' + ipstr + '/api/sonicos/restart'
        headers = {'Content-Type': 'application/json', 'Accept-Encoding': 'application/json'}
        data = {}
        try:
            r = requests.post(url, data=data, headers=headers, verify=False, timeout=150)
            if (r.status_code == 200):
                print ("Restart box {} successfully! Please wait some minutes....".format(ipstr))
            else:
                msg_res = r.json()['status']['info'][0]['message']
                t = datetime.datetime.now()
                logging.error("{}-API_URL:{}".format(t,url))
                logging.error("-post error message: Restart {} failed. error info:{}".format(ipstr,msg_res))
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(e)
            print "- PostERROR - Web service exception, msg = {}".format(e)

    def change_password(self,ipstr,old_pw,new_pw):
        self.login(ipstr)
        url = 'https://' + ipstr + '/administration/password'
        headers = {'Content-Type': 'application/json', 'Accept-Encoding': 'application/json'}
        body = {'administration': {'admin_password': {'old': old_pw, 'new': new_pw}}}
        l=json.load(body)
        d=json.dumps(l)
        try:
            r = requests.post(url, data=d, headers=headers, verify=False, timeout=150)
            if (r.status_code == 200):
                print ("For {},it is avaliable to change old password:{} to new password:{},please commit the configuration!!".format(ipstr,old_pw,new_pw))
            else:
                msg_res = r.json()['status']['info'][0]['message']
                t = datetime.datetime.now()
                logging.error("{}-API_URL:{}".format(t,url))
                logging.error("-post error message: change password {} failed. error info:{}".format(ipstr,msg_res))
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(e)
            print "- PostERROR - Web service exception, msg = {}".format(e)
        finally:
            self.commit(ipstr)

    def post_object(self,ipstr,url,data,sn,en):
        headers = {'Content-Type': 'application/json', 'Accept-Encoding': 'application/json'}
        try:
            r = requests.post(url, data=data, headers=headers, verify=False, timeout=150)
            msg_res = r.json()['status']['info'][0]['message']
            logging.info("post {} to {} objects, status_code=={},response msg:{}".format(sn,en,r.status_code,msg_res))
            if "Unauthorized" in msg_res:
                print "For post {}-{} object msg error--{}. Try to login again.".format(sn,en,msg_res)
                self.login(ipstr)
            elif "Not allowed in current mode" in msg_res:
                print "For post {}-{} object msg error--{}. Try to set config mode.".format(sn, en, msg_res)
                self.set_configMode(ipstr)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(e)
            print "- PostERROR - Web service exception, msg = {}".format(e)
        finally:
            self.commit(ipstr)
            

    def dealwith_FOR_loop(self,sn,num,step):
        n = sn + step
        if n <= num and sn <= num:
            loop = n
        elif n > num and num > sn:
            loop = num
        else:
            print "please enter right num!!"
        return loop

    def dealwith_abc(self,a,b,c):
        if a > 255:
            a = 1
            b += 1
        if b > 255:
            b = 1
            c += 1
        return a,b,c

    def run_start_params(self, sn):
        if sn >= 255:
            b = sn/255 + 1
            a = sn % 255
        else:
            b = 1
            a = sn
        return a, b

    def post_AddressObject(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        json_path = os.getcwd() + "\\JSON_FILE\\AddressObject\\AddressObject.json"
        url = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        print json_path
        a, b = self.run_start_params(sn)
        c = 1
        num = en + 1
        for i in range(sn, num, step):
            caseobj=[]
            casebody = {'address_objects': caseobj}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                name = "addressObj-" + str(j)
                a, b, c = self.dealwith_abc(a, b, c)
                host_ip = "112." + str(c) + "." + str(b) + "." + str(a)
                with open(json_path, 'rb') as f:
                    json_dict = json.load(f)
                    params = json_dict['address_objects'][0]
                    params['ipv4']['host']['ip'] = host_ip
                    params['ipv4']['name'] = name
                caseobj.append(params)
                a += 1
            data = json.dumps(casebody)
            print data
            self.post_object(ipstr,url, data,i,loop-1)


    def post_AddressGRP(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        url_ag = 'https://' + ipstr + '/api/sonicos/address-groups/ipv4'
        json_path_ao = os.getcwd() + "\\JSON_FILE\\AddressGroup\\AddressObject.json"
        json_path_ag = os.getcwd() + "\\JSON_FILE\\AddressGroup\\AddressGroup.json"
        # ##############################Address one address object###############################
        with open(json_path_ao, 'rb') as f_ao:
            json_dict = json.load(f_ao)
        data_ao = json.dumps(json_dict)
        print data_ao
        self.post_object(url_ao,data_ao,1,1)
        # ##############################Add address group#####################################
        num = en + 1
        for i in range(sn, num, step):
            grp = []
            grp_body = {'address_groups': grp}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                ao_grp = 'addressGrp_' + str(j)
                with open(json_path_ag, 'rb') as f_ag:
                    json_dict = json.load(f_ag)
                    ag_params = json_dict['address_groups'][0]
                    ag_params['ipv4']['name'] = ao_grp
                grp.append(ag_params)
            data_grp = json.dumps(grp_body)
            print data_grp
            self.post_object(url_ag, data_grp,i,loop-1)


    def post_AddressPerGRP(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        url_ag = 'https://' + ipstr + '/api/sonicos/address-groups/ipv4'
        json_path_ao = os.getcwd() + "\\JSON_FILE\\AddressGroup\\AddressObject.json"
        json_path_ag = os.getcwd() + "\\JSON_FILE\\AddressGroup\\AddressGroup.json"
        # ##############################Add address object###############################
        a, b = self.run_start_params(sn)
        c = 10
        num = en + 1
        for i in range(sn, num, step):
            grp_ao = []
            ao_body = {'address_objects': grp_ao}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                ao_name = 'ao_perGrp_' + str(j)
                ao_zone = 'LAN'
                a, b, c = self.dealwith_abc(a, b, c)
                ao_ip = "177." + str(c) + "." + str(b) + "." + str(a)
                print ao_ip
                with open(json_path_ao, 'rb') as f_ao:
                    json_dict = json.load(f_ao)
                    ao_params = json_dict['address_objects'][0]
                    ao_params['ipv4']['name'] = ao_name
                    ao_params['ipv4']['zone'] = ao_zone
                    ao_params['ipv4']['host']['ip'] = ao_ip
                grp_ao.append(ao_params)
                a += 1
            data_address = json.dumps(ao_body)
            self.post_object(ipstr,url_ao, data_address,i,loop-1)
        # ##############################Add address per group#####################################
        perGrp = []
        perGrp_body = {"address_groups":[{"ipv4":{"name": "ADDR_PER_GROUP","address_object":{"ipv4":perGrp}}}]}
        for k in range(sn,num):
            addr_name = 'ao_perGrp_' + str(k)
            with open(json_path_ag, 'rb') as f_ag:
                json_dict = json.load(f_ag)
                ag_params = json_dict['address_groups'][0]['ipv4']['address_object']['ipv4'][0]
                ag_params['name'] = addr_name
            perGrp.append(ag_params)
        data_perGrp = json.dumps(perGrp_body)
        print perGrp_body
        self.post_object(ipstr,url_ag, data_perGrp, 1, 1)

    def post_AddressGrpDepth(self,ipstr,sn,en):
        sn,en=int(sn),int(en)
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        url_ag = 'https://' + ipstr + '/api/sonicos/address-groups/ipv4'
        json_path_ao = os.getcwd() + "\\JSON_FILE\\AddressGrpDepth\\AddressObject.json"
        json_path_agd0 = os.getcwd() + "\\JSON_FILE\\AddressGrpDepth\\AddressGrpDepth0.json"
        json_path_agd = os.getcwd() + "\\JSON_FILE\\AddressGrpDepth\\AddressGrpDepth.json"
        # ##############################Add one address object###############################
        with open(json_path_ao,'rb') as f_ao:
            json_dict = json.load(f_ao)
        data_ao = json.dumps(json_dict)
        self.post_object(ipstr,url_ao, data_ao, 1, 1)
        #################################Add address group depth #############################
        num = en + 1
        for i in range(sn, num):
            in_num = i - 1
            agd_name = "Address_Grp_Depth" + str(i)
            if i == sn:
                with open(json_path_agd0, 'rb') as f_agd0:
                    json_dict_agd0 = json.load(f_agd0)
                    json_dict_agd0['address_groups'][0]['ipv4']['name'] = agd_name
                data_agd0 = json.dumps(json_dict_agd0)
                print data_agd0
                self.post_object(ipstr,url_ag, data_agd0, i, i)
            else:
                agd_include_name = "Address_Grp_Depth" + str(in_num)
                with open(json_path_agd, 'rb') as f_agd:
                    json_dict_agd = json.load(f_agd)
                    json_dict_agd['address_groups'][0]['ipv4']['name'] = agd_name
                    json_dict_agd['address_groups'][0]['ipv4']['address_group']['ipv4'][0]['name'] = agd_include_name
                data_agd = json.dumps(json_dict_agd)
                self.post_object(ipstr,url_ag, data_agd, i, i)



    def post_ServiceObject(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        json_path = "D:\\JK\\API-BasicAUTH\\API-Capacity\\JSON_FILE\\ServiceObject\\ServiceObject.json"
        url = 'https://' + ipstr + '/api/sonicos/service-objects'
        num = en + 1
        for i in range(sn, num, step):
            caseobj = []
            casebody = {'service_objects': caseobj}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                name = "ServiceObj-" + str(j)
                with open(json_path, 'rb') as f:
                    json_dict = json.load(f)
                    params = json_dict['service_objects'][0]
                    params['name'] = name
                caseobj.append(params)
            data = json.dumps(casebody)
            print data
            self.post_object(ipstr,url, data,i,loop-1)

    def post_ServiceGroup(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_sg = 'https://' + ipstr + '/api/sonicos/service-groups'
        json_path_ag = os.getcwd() + "\\JSON_FILE\\ServiceGroup\\ServiceGroup.json"
        # ##############################Add service group#####################################
        num = en + 1
        for i in range(sn, num, step):
            grp = []
            grp_body = {'service_groups': grp}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                so_grp_name = 'serviceGrp_' + str(j)
                with open(json_path_ag, 'rb') as f_ag:
                    json_dict = json.load(f_ag)
                    ag_params = json_dict['service_groups'][0]
                    ag_params['name'] = so_grp_name
                grp.append(ag_params)
            data_grp = json.dumps(grp_body)
            print data_grp
            self.post_object(ipstr,url_sg, data_grp, i, loop - 1)

    def post_ServicePerGRP(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_so = 'https://' + ipstr + '/api/sonicos/service-objects'
        url_sg = 'https://' + ipstr + '/api/sonicos/service-groups'
        json_path_sg = os.getcwd() + "\\JSON_FILE\\ServicePerGroup\\ServicePerGroup.json"
        json_path_so = os.getcwd() + "\\JSON_FILE\\ServicePerGroup\\ServiceObject.json"
        # ##############################Add service object###############################
        num = en + 1
        for i in range(sn, num, step):
            grp_so = []
            ao_body = {'service_objects': grp_so}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                so_name = 'so_perGrp_' + str(j)
                with open(json_path_so, 'rb') as f_so:
                    json_dict = json.load(f_so)
                    so_params = json_dict['service_objects'][0]
                    so_params['name'] = so_name
                grp_so.append(so_params)
            data_address = json.dumps(ao_body)
            self.post_object(ipstr,url_so, data_address,i,loop-1)
        # ##############################Add service object per group#####################################
        perGrp = []
        perGrp_body = {"service_groups":[{"name":"SVC_PER_GROUP","service_object":perGrp}]}
        for k in range(sn,num):
            svc_name = 'so_perGrp_' + str(k)
            with open(json_path_sg, 'rb') as f_sg:
                json_dict = json.load(f_sg)
                sg_params = json_dict['service_groups'][0]['service_object'][0]
                sg_params['name'] = svc_name
            perGrp.append(sg_params)
        data_perGrp = json.dumps(perGrp_body)
        print perGrp_body
        self.post_object(ipstr,url_sg, data_perGrp, 1, 1)

    def post_ServiceGrpDepth(self,ipstr,sn,en):
        sn,en=int(sn),int(en)
        url_sg = 'https://' + ipstr + '/api/sonicos/service-groups'
        json_path_sgd = os.getcwd() + "\\JSON_FILE\\ServiceGrpDepth\\ServiceGrpDepth.json"
        ###################post grp including grp ##################
        num = en + 1
        for i in range(sn,num):
            in_num = i - 1
            if i == sn:
                sgd_include_name = "ICMP"
            else:
                sgd_include_name = "Service_Grp_Depth" + str(in_num)
            sgd_name = "Service_Grp_Depth" + str(i)
            with open(json_path_sgd, 'rb') as f_sgd:
                json_dict_sgd = json.load(f_sgd)
                json_dict_sgd['service_groups'][0]['name'] = sgd_name
                json_dict_sgd['service_groups'][0]['service_group'][0]['name'] = sgd_include_name
            data_sgd = json.dumps(json_dict_sgd)
            print data_sgd
            self.post_object(ipstr,url_sg, data_sgd, i, i)

    def post_VLAN(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        json_path = os.getcwd() + "\\JSON_FILE\\VLAN\\VLAN.json"
        url = 'https://' + ipstr + '/api/sonicos/interfaces/ipv4'
        print json_path
        a, b = self.run_start_params(sn)
        c = 57
        num = en + 1
        for i in range(sn, num, step):
            caseobj = []
            casebody = {'interfaces': caseobj}
            print casebody
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                a, b, c = self.dealwith_abc(a, b, c)
                static_ip = str(c) + "." + str(b) + "." + str(a)+".3"
                vlan_tag = j
                with open(json_path, 'rb') as f:
                    json_dict = json.load(f)
                    params = json_dict['interfaces'][0]
                    params['ipv4']['vlan'] = vlan_tag
                    params['ipv4']['ip_assignment']['mode']['static']['ip'] = static_ip
                caseobj.append(params)
                a += 1
            data = json.dumps(casebody)
            print data
            self.post_object(ipstr,url, data,i,loop-1)

    def post_DHCP(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        json_path = os.getcwd() + "\\JSON_FILE\\DHCP\\DHCP.json"
        url = 'https://' + ipstr + '/api/sonicos/dhcp-server/ipv4/scopes/dynamic'
        a,b = self.run_start_params(sn)
        c = 10
        num = en + 1
        for i in range(sn, num, step):
            caseobj = []
            casebody = {'dhcp_server':{'ipv4':{'scope':{'dynamic':caseobj}}}}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                a, b, c = self.dealwith_abc(a, b, c)
                dynamic_ip = "17." + str(c) + "." + str(b) + "." + str(a)
                with open(json_path, 'rb') as f:
                    json_dict = json.load(f)
                    params = json_dict['dhcp_server']['ipv4']['scope']['dynamic'][0]
                    params['from'] = dynamic_ip
                    params['to'] = dynamic_ip
                caseobj.append(params)
                a += 1
            data = json.dumps(casebody)
            # print data
            self.post_object(ipstr,url, data,i,loop-1)

    def post_ARP(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        json_path = os.getcwd() + "\\JSON_FILE\\ARP\\ARP.json"
        url = 'https://' + ipstr + '/api/sonicos/arp/entries'
        print json_path
        a, b = self.run_start_params(sn)
        c = 1
        num = en + 1
        for i in range(sn, num, step):
            caseobj = []
            casebody = {'arp':{'entry': caseobj}}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                a, b, c = self.dealwith_abc(a, b, c)
                host_ip = "9." + str(c) + "." + str(b) + "." + str(a)
                mac = "001100000"+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))
                with open(json_path, 'rb') as f:
                    json_dict = json.load(f)
                    params = json_dict['arp']['entry'][0]
                    params['ip'] = host_ip
                    params['mac'] = mac
                caseobj.append(params)
                a += 1
            data = json.dumps(casebody)
            print data
            self.post_object(ipstr,url, data,i,loop-1)

###############don't support post for grp vpn now###############################
    def post_GrpVPN(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        json_path = os.getcwd() + "\\JSON_FILE\\GrpVPN\\GrpVPN.json"
        url = 'https://' + ipstr + '/api/sonicos/vpn/policies/ipv4/group-vpn'
        num = en + 1
        for i in range(sn, num, step):
            caseobj = []
            casebody = {'vpn':{'policy': caseobj}}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                name = "group_vpn_" + str(j)
                with open(json_path, 'rb') as f:
                    json_dict = json.load(f)
                    params = json_dict['vpn']['policy'][0]
                    params['ipv4']['group_vpn']['name'] = name
                caseobj.append(params)
            data = json.dumps(casebody)
            print data
            self.post_object(ipstr,url, data,i,loop-1)

    def post_Schedule(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        json_path = os.getcwd() + "\\JSON_FILE\\Schedule\\Schedule.json"
        url = 'https://' + ipstr + '/api/sonicos/schedules'
        num = en + 1
        for i in range(sn, num, step):
            caseobj = []
            casebody = {'scheduler':{'schedule': caseobj}}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                name = "schedule_obj_" + str(j)
                with open(json_path, 'rb') as f:
                    json_dict = json.load(f)
                    params = json_dict['scheduler']['schedule'][0]
                    params['name'] = name
                caseobj.append(params)
            data = json.dumps(casebody)
            print data
            self.post_object(ipstr,url, data,i,loop-1)

    def post_Zone(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        json_path = os.getcwd() + "\\JSON_FILE\\Zone\\Zone.json"
        url = 'https://' + ipstr + '/api/sonicos/zones'
        num = en + 1
        for i in range(sn, num, step):
            caseobj = []
            casebody = {'zones': caseobj}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                name = "zone_" + str(j)
                with open(json_path, 'rb') as f:
                    json_dict = json.load(f)
                    params = json_dict['zones'][0]
                    params['name'] = name
                caseobj.append(params)
            data = json.dumps(casebody)
            print data
            self.post_object(ipstr,url, data,i,loop-1)

    def post_GuestUser(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        json_path = os.getcwd() + "\\JSON_FILE\\GuestUser\\GuestUser.json"
        url = 'https://' + ipstr + '/api/sonicos/user/guest/users'
        num = en + 1
        for i in range(sn, num, step):
            caseobj = []
            casebody = {'user':{'guest':{'user':caseobj}}}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                name = "guest_" + str(j)
                with open(json_path, 'rb') as f:
                    json_dict = json.load(f)
                    params = json_dict['user']['guest']['user'][0]
                    params['name'] = name
                caseobj.append(params)
            data = json.dumps(casebody)
            print data
            self.post_object(ipstr,url, data,i,loop-1)

    def post_LocalUser(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        json_path = os.getcwd() + "\\JSON_FILE\\LocalUser\\LocalUser.json"
        url = 'https://' + ipstr + '/api/sonicos/user/local/users'
        num = en + 1
        for i in range(sn, num, step):
            caseobj = []
            casebody = {'user':{'local':{'user': caseobj}}}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                name = "loc_user_" + str(j)
                with open(json_path, 'rb') as f:
                    json_dict = json.load(f)
                    params = json_dict['user']['local']['user'][0]
                    params['name'] = name
                    params['display_name'] = name
                caseobj.append(params)
            data = json.dumps(casebody)
            print data
            self.post_object(ipstr,url, data,i,loop-1)

    def post_vpn_pol_bymanual(self,ipstr,sn,en,step,grp_ao_num):
        sn,en=int(sn),int(en)
        url_vpn = 'https://' + ipstr + '/api/sonicos/vpn/policies/ipv4/site-to-site'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        url_ag = 'https://' + ipstr + '/api/sonicos/address-groups/ipv4'
        json_path_vpn = os.getcwd() + "\\JSON_FILE\\VPN_Policy_byManual\\VPN_Policy_byManual.json"
        json_path_ao = os.getcwd() + "\\JSON_FILE\\VPN_Policy_byManual\\AddressObject.json"
        json_path_ag = os.getcwd() + "\\JSON_FILE\\VPN_Policy_byManual\\AddressGroup.json"
        # ##############################Add address group#####################################
        num=grp_ao_num+1
        grp_ao = []
        grp = []
        for i in range(1,num):
            ao_body={'address_objects': grp_ao}
            grp_body={'address_groups': grp}
            print grp_body
            ao_name='Phase2_AO_'+str(i)
            ao_zone='WAN'
            ao_ip='152.7.'+str(i)+'.0'
            with open(json_path_ao, 'rb') as f_ao:
                json_dict = json.load(f_ao)
                ao_params = json_dict['address_objects'][0]
                ao_params['ipv4']['name'] = ao_name
                ao_params['ipv4']['zone'] = ao_zone
                ao_params['ipv4']['network']['subnet'] = ao_ip
            with open(json_path_ag, 'rb') as f_ag:
                json_dict = json.load(f_ag)
                ag_params = json_dict['address_groups'][0]
                ag_params['ipv4']['address_object']['ipv4'][0]['name'] = ao_name
            grp_ao.append(ao_params)
            grp.append(ag_params)
        data_grp = json.dumps(grp_body)
        data_address = json.dumps(ao_body)
        self.post_object(ipstr,url_ao, data_address)
        self.post_object(ipstr,url_ag, data_grp)
        ##########################post vpn policies by manual key#######################################
        a, b = self.run_start_params(sn)
        c = 10
        num = en + 1
        for i in range(sn, num, step):
            caseobj_ao = []
            caseobj_vpn = []
            casebody_ao = {'address_objects': caseobj_ao}
            casebody_vpn = {"vpn": {"policy": caseobj_vpn}}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                dict = {}
                name = "m_vpn" + str(j)
                in_spi = hex(11000 + j)
                out_spi = hex(19000 + j)
                remote_name = "m_remote" + str(j)
                name = "vpn_bymanual_-" + str(j)
                a, b, c = self.dealwith_abc(a, b, c)
                subnet_ip = "40." + str(b) + "." + str(a) + ".0"
                gw_ip = "17." + str(c) + "." + str(b) + "." + str(a)
                # create json file for vpn policy
                with open(json_path_vpn, 'r') as f:
                    json_dict = json.load(f)
                    params_vpn = json_dict['vpn']['policy'][0]
                    params_vpn['ipv4']['site_to_site']['name'] = name
                    params_vpn['ipv4']['site_to_site']['gateway']['primary'] = gw_ip
                    params_vpn['ipv4']['site_to_site']['network']['remote']['destination_network']['name'] = remote_name
                    params_vpn['ipv4']['site_to_site']['proposal']['ipsec']['in_spi'] = in_spi
                    params_vpn['ipv4']['site_to_site']['proposal']['ipsec']['out_spi'] = out_spi
                # create json file for address objects
                with open(json_path_ao, 'rb') as f0:
                    json_dict = json.load(f0)
                    params_ao = json_dict['address_objects'][0]
                    params_ao['ipv4']['network']['subnet'] = subnet_ip
                    params_ao['ipv4']['name'] = remote_name
                caseobj_vpn.append(params_vpn)
                caseobj_ao.append(params_ao)
                a += 1
            data_vpn = json.dumps(casebody_vpn)
            data_ao = json.dumps(casebody_ao)
            self.post_object(ipstr,url_ao, data_ao,i,loop-1)
            self.post_object(ipstr,url_vpn, data_vpn,i,loop-1)

    def post_vpn_pol_site2site(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_vpn = 'https://' + ipstr + '/api/sonicos/vpn/policies/ipv4/site-to-site'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        json_path_vpn = os.getcwd() + "\\JSON_FILE\\SiteToSite\\SiteToSite.json"
        json_path_ao = os.getcwd() + "\\JSON_FILE\\SiteToSite\\AddressObject.json"
        a, b = self.run_start_params(sn)
        c = 2
        num = en + 1
        for i in range(sn, num, step):
            caseobj_ao = []
            caseobj_vpn = []
            casebody_ao = {'address_objects': caseobj_ao}
            casebody_vpn = {"vpn": {"policy": caseobj_vpn}}
            loop = self.dealwith_FOR_loop(i,num,step)
            for j in range(i, loop):
                a,b,c=  self.dealwith_abc(a,b,c)
                pol_name = "VPN_Ixia" + str(j)
                des_ip = "21." + str(b) + "." + str(a) + ".0"
                remote_name = des_ip
                gw_ip = "7." + str(c) + "." + str(b) + "." + str(a)
                peer_ike_id = "13." + str(c) + "." + str(b) + "." + str(a)
                # create json file for vpn policy
                with open(json_path_vpn, 'r') as f:
                    json_dict = json.load(f)
                    params_vpn = json_dict['vpn']['policy'][0]
                    params_vpn['ipv4']['site_to_site']['name'] = pol_name
                    params_vpn['ipv4']['site_to_site']['gateway']['primary'] = gw_ip
                    params_vpn['ipv4']['site_to_site']['network']['remote']['destination_network']['name'] = remote_name
                    params_vpn['ipv4']['site_to_site']['auth_method']['shared_secret']['ike_id']['peer']['ipv4'] = peer_ike_id
                caseobj_vpn.append(params_vpn)
                # create json file for address objects
                with open(json_path_ao, 'rb') as f0:
                    json_dict = json.load(f0)
                    params_ao = json_dict['address_objects'][0]
                    params_ao['ipv4']['network']['subnet'] = des_ip
                    params_ao['ipv4']['name'] = des_ip
                caseobj_ao.append(params_ao)
                a += 1
            data_ao = json.dumps(casebody_ao)
            data_vpn = json.dumps(casebody_vpn)
            print data_vpn
            self.post_object(ipstr,url_ao,data_ao,i,loop-1)
            self.post_object(ipstr,url_vpn,data_vpn,i,loop-1)

    def post_vpn_pol_forPraveen(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_vpn = 'https://' + ipstr + '/api/sonicos/vpn/policies/ipv4/site-to-site'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        url_ag = 'https://' + ipstr + '/api/sonicos/address-groups/ipv4'
        json_path_vpn = os.getcwd() + "\\JSON_FILE\\SiteToSite_forPraveen\\SiteToSite.json"
        json_path_ao = os.getcwd() + "\\JSON_FILE\\SiteToSite_forPraveen\\AddressObject.json"
        json_path_ag = os.getcwd() + "\\JSON_FILE\\SiteToSite_forPraveen\\AddressGroup.json"
        a, b = self.run_start_params(sn)
        c = 2
        num = en + 1
        for i in range(sn, num, step):
            caseobj_ao = []
            caseobj_vpn = []
            perGrp = []
            casebody_ao = {'address_objects': caseobj_ao}
            casebody_vpn = {"vpn": {"policy": caseobj_vpn}}
            loop = self.dealwith_FOR_loop(i,num,step)
            for j in range(i, loop):
                grp_name="Lgrp"+str(j)
                a,b,c=  self.dealwith_abc(a,b,c)
                pol_name = "ppnm" + str(j)
                addr_ip = "9.1."+ str(a) + ".0"
                remote_name = "10.1.1.0/24"
                gw_ip = "100.1.1." + str(j+1)
                peer_ike_id = "Rppnm" + str(j) + ".com"
                local_ike_id = "Lppnm" + str(j) + ".com"
                # create json file for vpn policy
                with open(json_path_vpn, 'r') as f:
                    json_dict = json.load(f)
                    params_vpn = json_dict['vpn']['policy'][0]
                    params_vpn['ipv4']['site_to_site']['name'] = pol_name
                    params_vpn['ipv4']['site_to_site']['gateway']['primary'] = gw_ip
                    params_vpn['ipv4']['site_to_site']['network']['remote']['destination_network']['name'] = remote_name
                    params_vpn['ipv4']['site_to_site']['network']['local']['group'] = grp_name
                    params_vpn['ipv4']['site_to_site']['auth_method']['shared_secret']['ike_id']['peer']['domain_name'] = peer_ike_id
                    params_vpn['ipv4']['site_to_site']['auth_method']['shared_secret']['ike_id']['local']['domain_name'] = local_ike_id
                caseobj_vpn.append(params_vpn)
                # create json file for address objects
                for k in range(5*j-4,5*j+1):
                    addr_name = "9.1."+ str(k) + ".0"
                    perGrp_body = {"address_groups":[{"ipv4":{"name": grp_name,"address_object":{"ipv4":perGrp}}}]}
                    with open(json_path_ao, 'rb') as f0:
                        json_dict = json.load(f0)
                        params_ao = json_dict['address_objects'][0]
                        params_ao['ipv4']['network']['subnet'] = addr_name
                        params_ao['ipv4']['name'] = addr_name
                    caseobj_ao.append(params_ao)
                    # create json file for address grp
                    with open(json_path_ag, 'rb') as f_ag:
                        json_dict = json.load(f_ag)
                        ag_params = json_dict['address_groups'][0]['ipv4']['address_object']['ipv4'][0]
                        ag_params['name'] = addr_name
                    perGrp.append(ag_params)
                a += 1
            data_perGrp = json.dumps(perGrp_body)
            data_ao = json.dumps(casebody_ao)
            data_vpn = json.dumps(casebody_vpn)
            print data_perGrp
            self.post_object(ipstr,url_ao,data_ao,i,loop-1)
            self.post_object(ipstr,url_ag, data_perGrp,i,loop-1)
            self.post_object(ipstr,url_vpn,data_vpn,i,loop-1)

    def post_AccessRules(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_rule = 'https://' + ipstr + '/api/sonicos/security-policies/ipv4'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        json_path_rule = os.getcwd() + "\\JSON_FILE\\AccessRules\\AccessRules.json"
        json_path_src = os.getcwd() + "\\JSON_FILE\\AccessRules\\AddressObject_src.json"
        json_path_des = os.getcwd() + "\\JSON_FILE\\AccessRules\\AddressObject_des.json"
        a, b = self.run_start_params(sn)
        c = 20
        num = en + 1
        for i in range(sn, num, step):
            caseobj_ao_src = []
            caseobj_ao_des = []
            caseobj_rule = []
            casebody_ao_src = {'address_objects': caseobj_ao_src}
            casebody_ao_des = {'address_objects': caseobj_ao_des}
            casebody_rule = {"security_policies": caseobj_rule}
            loop = self.dealwith_FOR_loop(i,num,step)
            for j in range(i, loop):
                a,b,c=  self.dealwith_abc(a,b,c)
                rule_name = "access-rule-" + str(j)
                src_name = "acc-src-" + str(j)
                des_name = "acc-des-" + str(j)
                src_ip = "162." + str(c) + "." + str(b) +"."+ str(a) 
                des_ip = "21." + str(c) + "." + str(b) +"."+ str(a)
                # create json file for access rules policy
                with open(json_path_rule, 'r') as f:
                    json_dict = json.load(f)
                    params_rule = json_dict['security_policies'][0]
                    params_rule['ipv4']['name'] = rule_name
                    params_rule['ipv4']['source']['address']['name'] = src_name
                    params_rule['ipv4']['destination']['address']['name'] = des_name
                caseobj_rule.append(params_rule)
                # create json file for src address objects
                with open(json_path_src, 'rb') as f0:
                    json_dict = json.load(f0)
                    params_ao_src = json_dict['address_objects'][0]
                    params_ao_src['ipv4']['name'] = src_name
                    params_ao_src['ipv4']['host']['ip'] = src_ip
                caseobj_ao_src.append(params_ao_src)
                # create json file for des address objects
                with open(json_path_des, 'rb') as f1:
                    json_dict = json.load(f1)
                    params_ao_des = json_dict['address_objects'][0]
                    params_ao_des['ipv4']['name'] = des_name
                    params_ao_des['ipv4']['host']['ip'] = des_ip
                caseobj_ao_des.append(params_ao_des)
                a += 1
            data_ao_src = json.dumps(casebody_ao_src)
            data_ao_des = json.dumps(casebody_ao_des)
            data_rule = json.dumps(casebody_rule)
            self.post_object(ipstr,url_ao,data_ao_src,i,loop-1)
            self.post_object(ipstr,url_ao,data_ao_des,i,loop-1)
            self.post_object(ipstr,url_rule,data_rule,i,loop-1)

    def post_DosPolicy(self,ipstr,sn,en,step=1):
        sn,en,step=int(sn),int(en),int(step)
        url_dos = 'https://' + ipstr + '/api/sonicos/dos-policies'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        json_path_dos = os.getcwd() + "\\JSON_FILE\\DosPolicy\\DosPolicy.json"
        json_path_src = os.getcwd() + "\\JSON_FILE\\DosPolicy\\AddressObject_src.json"
        json_path_des = os.getcwd() + "\\JSON_FILE\\DosPolicy\\AddressObject_des.json"
        a, b = self.run_start_params(sn)
        c = 20
        num = en + 1
        for i in range(sn, num, step):
            caseobj_ao_src = []
            caseobj_ao_des = []
            caseobj_dos = []
            casebody_ao_src = {'address_objects': caseobj_ao_src}
            casebody_ao_des = {'address_objects': caseobj_ao_des}
            casebody_dos = {"dos_policies": caseobj_dos}
            loop = self.dealwith_FOR_loop(i,num,step)
            for j in range(i, loop):
                a,b,c=  self.dealwith_abc(a,b,c)
                dos_name = "dos-pol-" + str(j)
                src_name = "dos-src-" + str(j)
                des_name = "dos-des-" + str(j)
                src_ip = "152." + str(c) + "." + str(b) +"."+ str(a) 
                des_ip = "31." + str(c) + "." + str(b) +"."+ str(a)
                uuid = "00000000-0000-0006-1d00-0040109" +str(i)
                # create json file for access rules policy
                with open(json_path_dos, 'r') as f:
                    json_dict = json.load(f)
                    params_dos = json_dict['dos_policies'][0]
                    params_dos['uuid'] = uuid
                    params_dos['name'] = dos_name
                    params_dos['source']['address']['name'] = src_name
                    params_dos['destination']['address']['name'] = des_name
                caseobj_dos.append(params_dos)
                # create json file for src address objects
                with open(json_path_src, 'rb') as f0:
                    json_dict = json.load(f0)
                    params_ao_src = json_dict['address_objects'][0]
                    params_ao_src['ipv4']['name'] = src_name
                    params_ao_src['ipv4']['host']['ip'] = src_ip
                caseobj_ao_src.append(params_ao_src)
                # create json file for des address objects
                with open(json_path_des, 'rb') as f1:
                    json_dict = json.load(f1)
                    params_ao_des = json_dict['address_objects'][0]
                    params_ao_des['ipv4']['name'] = des_name
                    params_ao_des['ipv4']['host']['ip'] = des_ip
                caseobj_ao_des.append(params_ao_des)
                a += 1
            data_ao_src = json.dumps(casebody_ao_src)
            data_ao_des = json.dumps(casebody_ao_des)
            data_dos = json.dumps(casebody_dos)
            print data_dos
            self.post_object(ipstr,url_ao,data_ao_src,i,loop-1)
            self.post_object(ipstr,url_ao,data_ao_des,i,loop-1)
            self.post_object(ipstr,url_dos,data_dos,i,loop-1)

    def post_DosPolicy_250(self,ipstr,sn,en,step=1):
        sn,en,step=int(sn),int(en),int(step)
        url_dos = 'https://' + ipstr + '/api/sonicos/dos-policies'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        json_path_dos = os.getcwd() + "\\JSON_FILE\\DosPolicy\\DosPolicy.json"
        json_path_src = os.getcwd() + "\\JSON_FILE\\DosPolicy\\AddressObject_src.json"
        json_path_des = os.getcwd() + "\\JSON_FILE\\DosPolicy\\AddressObject_des.json"
        a, b = self.run_start_params(sn)
        d, e = self.run_start_params(sn)
        c = 2
        f = 2
        num = en/250
        for i in range(sn, num): 
            for j in range(250*i-249, 250*i+1):
                a,b,c=  self.dealwith_abc(a,b,c)
                src_name = "dos-src-" + str(j)
                caseobj_ao_src = []
                casebody_ao_src = {'address_objects': caseobj_ao_src}
                src_ip = "152." + str(c) + "." + str(b) +"."+ str(a)
                print src_ip
                # create json file for src address objects
                with open(json_path_src, 'rb') as f0:
                    json_dict = json.load(f0)
                    params_ao_src = json_dict['address_objects'][0]
                    params_ao_src['ipv4']['name'] = src_name
                    params_ao_src['ipv4']['host']['ip'] = src_ip
                caseobj_ao_src.append(params_ao_src)
                a += 1
                data_ao_src = json.dumps(casebody_ao_src)
                self.post_object(ipstr,url_ao,data_ao_src,j,j)
            for k in range(250*i-249, 250*i+1):
                d,e,f=  self.dealwith_abc(d,e,f)
                des_name = "dos-des-" + str(k)
                caseobj_ao_des = []
                casebody_ao_des = {'address_objects': caseobj_ao_des}
                des_ip = "31." + str(f) + "." + str(e) +"."+ str(d)
                print des_ip
                # create json file for des address objects
                with open(json_path_des, 'rb') as f1:
                    json_dict = json.load(f1)
                    params_ao_des = json_dict['address_objects'][0]
                    params_ao_des['ipv4']['name'] = des_name
                    params_ao_des['ipv4']['host']['ip'] = des_ip
                caseobj_ao_des.append(params_ao_des)
                d += 1
                data_ao_des = json.dumps(casebody_ao_des)
                self.post_object(ipstr,url_ao,data_ao_des,k,k)
            for l in range(250*i-249, 250*i+1):
                dos_name = "dos-pol-" + str(l)
                src_name = "dos-src-" + str(l)
                des_name = "dos-des-" + str(l)
                caseobj_dos = []
                casebody_dos = {"dos_policies": caseobj_dos}
                uuid = str(l)
                # create json file for access rules policy
                with open(json_path_dos, 'rb') as f:
                    json_dict = json.load(f)
                    params_dos = json_dict['dos_policies'][0]
                    params_dos['uuid'] = uuid
                    params_dos['name'] = dos_name
                    params_dos['source']['address']['name'] = src_name
                    params_dos['destination']['address']['name'] = des_name
                caseobj_dos.append(params_dos)
                data_dos = json.dumps(casebody_dos)
                self.post_object(ipstr,url_dos,data_dos,l,l)
            

    def post_TunnelInterface(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_TI = 'https://' + ipstr + '/api/sonicos/tunnel-interfaces/vpn'
        url_TP = 'https://' + ipstr + '/api/sonicos/vpn/policies/ipv4/tunnel-interface'
        json_path_pol = os.getcwd() + "\\JSON_FILE\\TunnelInterface\\VPN_Tunnel_Policy.json"
        json_path_TI =os.getcwd() + "\\JSON_FILE\\TunnelInterface\\TunnelInterface.json"
        a, b = self.run_start_params(sn)
        c = 2
        num = en + 1
        for i in range(sn, num, step):
            caseobj_pol = []
            caseobj_TI = []
            casebody_TI = {'tunnel_interfaces':caseobj_TI}
            casebody_pol = {"vpn":{"policy":caseobj_pol}}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                TI_name = "TI_" + str(j)
                policy_name = "test" + str(j)
                a, b, c = self.dealwith_abc(a, b, c)
                ip = "10." + str(b) + "." + str(a) + ".4"
                gw_ip = "10." + str(c) + "." + str(b) + "." + str(a)
                peer_ike_id = "125." + str(c) + "." + str(b) + "." + str(a)
                # create json file for tunnel interfaces
                with open(json_path_TI, 'r') as f:
                    json_dict = json.load(f)
                    params_TI = json_dict['tunnel_interfaces'][0]
                    params_TI['vpn']['name'] = TI_name
                    params_TI['vpn']['policy'] = policy_name
                    params_TI['vpn']['ip_assignment']['mode']['static']['ip'] = ip
                # create json file for policy
                with open(json_path_pol, 'rb') as f0:
                    json_dict0 = json.load(f0)
                    params_TP = json_dict0['vpn']['policy'][0]
                    params_TP['ipv4']['tunnel_interface']['name'] = policy_name
                    params_TP['ipv4']['tunnel_interface']['gateway']['primary'] = gw_ip
                    params_TP['ipv4']['tunnel_interface']['auth_method']['shared_secret']['ike_id']['peer']['ipv4'] = peer_ike_id
                a += 1
                caseobj_pol.append(params_TP)
                caseobj_TI.append(params_TI)
            data_pol = json.dumps(casebody_pol)
            data_TI = json.dumps(casebody_TI)
            self.post_object(ipstr,url_TP, data_pol,i,loop-1)
            self.post_object(ipstr,url_TI, data_TI,i,loop-1)

    def post_NatPolicy(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_nat = 'https://' + ipstr + '/api/sonicos/nat-policies/ipv4'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        json_path_nat = os.getcwd() + "\\JSON_FILE\\NatPolicy\\NatPolicy.json"
        json_path_src = os.getcwd() + "\\JSON_FILE\\NatPolicy\\SourceAddress.json"
        json_path_ori_dst = os.getcwd() + "\\JSON_FILE\\NatPolicy\\ori_dst.json"
        json_path_trans_dst = os.getcwd() + "\\JSON_FILE\\NatPolicy\\trans_dst.json"
        ##############################add one original destination address and one transfer destination address####################
        with open(json_path_ori_dst,'r') as f_od:
            json_dict_od = json.load(f_od)
        data_od = json.dumps(json_dict_od)
        with open(json_path_trans_dst,'r') as f_td:
            json_dict_td = json.load(f_td)
        data_td = json.dumps(json_dict_td)
        self.post_object(ipstr,url_ao, data_od, 1, 1)
        self.post_object(ipstr,url_ao, data_td, 1, 1)
        ################################add nat policies with variable parameter#####################################################
        a, b = self.run_start_params(sn)
        c = 2
        num = en + 1
        for i in range(sn, num, step):
            caseobj_ao = []
            caseobj_nat = []
            casebody_ao = {'address_objects': caseobj_ao}
            casebody_nat = {"nat_policies":caseobj_nat}
            loop = self.dealwith_FOR_loop(i,num,step)
            for j in range(i, loop):
                a,b,c = self.dealwith_abc(a,b,c)
                nat_name = "NAT_POL_Custom_" + str(i)
                src_name = "source-" + str(j)
                host_ip = "9." + str(c) + "." + str(b) + "." + str(a)
                # create json file for nat policy
                with open(json_path_nat, 'r') as f:
                    json_dict = json.load(f)
                    params_nat = json_dict['nat_policies'][0]
                    params_nat['ipv4']['name'] = nat_name
                    params_nat['ipv4']['source']['name'] = src_name
                caseobj_nat.append(params_nat)
                # create json file for address objects
                with open(json_path_src, 'rb') as f0:
                    json_dict = json.load(f0)
                    params_ao = json_dict['address_objects'][0]
                    params_ao['ipv4']['name'] = src_name
                    params_ao['ipv4']['host']['ip'] = host_ip
                caseobj_ao.append(params_ao)
                a += 1
            data_ao = json.dumps(casebody_ao)
            data_nat = json.dumps(casebody_nat)
            self.post_object(ipstr,url_ao,data_ao,i,loop-1)
            self.post_object(ipstr,url_nat,data_nat,i,loop-1)

    def post_StaticRoute(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_rt = 'https://' + ipstr + '/api/sonicos/route-policies/ipv4'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        json_path_rt = os.getcwd() + "\\JSON_FILE\\StaticRoute\\StaticRoute.json"
        json_path_src = os.getcwd() + "\\JSON_FILE\\StaticRoute\\Src_Address.json"
        json_path_dst = os.getcwd() + "\\JSON_FILE\\StaticRoute\\Des_Address.json"
        json_path_gw = os.getcwd() + "\\JSON_FILE\\StaticRoute\\TB_Gateway.json"
        ##############################add one destination address and one TB Gateway address####################
        with open(json_path_dst,'r') as f_dst:
            json_dict_dst = json.load(f_dst)
        data_dst = json.dumps(json_dict_dst)
        with open(json_path_gw,'r') as f_gw:
            json_dict_gw = json.load(f_gw)
        data_gw = json.dumps(json_dict_gw)
        self.post_object(ipstr,url_ao, data_dst, 1, 1)
        self.post_object(ipstr,url_ao, data_gw, 1, 1)
        ################################add static route policies with variable parameter#####################################################
        a, b = self.run_start_params(sn)
        c = 4
        num = en + 1
        for i in range(sn, num, step):
            caseobj_ao = []
            caseobj_rt = []
            casebody_ao = {'address_objects': caseobj_ao}
            casebody_rt = {"route_policies":caseobj_rt}
            loop = self.dealwith_FOR_loop(i,num,step)
            for j in range(i, loop):
                a,b,c = self.dealwith_abc(a,b,c)
                rt_name = "RoutePol-Custom-" + str(i)
                src_name = "src-" + str(j)
                host_ip = "51." + str(c) + "." + str(b) + "." + str(a)
                # create json file for nat policy
                with open(json_path_rt, 'r') as f:
                    json_dict = json.load(f)
                    params_rt = json_dict['route_policies'][0]
                    params_rt['ipv4']['name'] = rt_name
                    params_rt['ipv4']['source']['name'] = src_name
                caseobj_rt.append(params_rt)
                # create json file for address objects
                with open(json_path_src, 'rb') as f0:
                    json_dict = json.load(f0)
                    params_ao = json_dict['address_objects'][0]
                    params_ao['ipv4']['name'] = src_name
                    params_ao['ipv4']['host']['ip'] = host_ip
                caseobj_ao.append(params_ao)
                a += 1
            data_ao = json.dumps(casebody_ao)
            data_rt = json.dumps(casebody_rt)
            self.post_object(ipstr,url_ao,data_ao,i,loop-1)
            self.post_object(ipstr,url_rt,data_rt,i,loop-1)

    def post_StaticRouteFQDN(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_rt = 'https://' + ipstr + '/api/sonicos/route-policies/ipv4'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/fqdn'
        json_path_rt = os.getcwd() + "\\JSON_FILE\\StaticRouteFQDN\\StaticRouteFQDN.json"
        json_path_dst = os.getcwd() + "\\JSON_FILE\\StaticRouteFQDN\\DesAddressFQDN.json"
        ################################add static route FQDN policies with variable parameter#####################################################
        num = en + 1
        for i in range(sn, num, step):
            caseobj_ao = []
            caseobj_rt = []
            casebody_ao = {'address_objects': caseobj_ao}
            casebody_rt = {"route_policies":caseobj_rt}
            loop = self.dealwith_FOR_loop(i,num,step)
            for j in range(i, loop):
                rt_name = "RoutePolFQDN-" + str(i)
                des_name = "www.ng6s" + str(j) +".com"
                # create json file for nat policy
                with open(json_path_rt, 'r') as f:
                    json_dict = json.load(f)
                    params_rt = json_dict['route_policies'][0]
                    params_rt['ipv4']['name'] = rt_name
                    params_rt['ipv4']['destination']['name'] = des_name
                caseobj_rt.append(params_rt)
                # create json file for address objects
                with open(json_path_dst, 'rb') as f0:
                    json_dict = json.load(f0)
                    params_ao = json_dict['address_objects'][0]
                    params_ao['fqdn']['name'] = des_name
                    params_ao['fqdn']['domain'] = des_name
                caseobj_ao.append(params_ao)
            data_ao = json.dumps(casebody_ao)
            data_rt = json.dumps(casebody_rt)
            print data_rt
            self.post_object(ipstr,url_ao,data_ao,i,loop-1)
            self.post_object(ipstr,url_rt,data_rt,i,loop-1)

    def post_BotnetFilter(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_bot = 'https://' + ipstr + '/api/sonicos/botnet/custom-list-addresses'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        json_path_bot = os.getcwd() + "\\JSON_FILE\\BotnetFilter\\BotnetFilter.json"
        json_path_ao = os.getcwd() + "\\JSON_FILE\\BotnetFilter\\AddressObject.json"
        ################################add bonet filter with variable parameter#####################################################
        a, b = self.run_start_params(sn)
        c = 2
        num = en + 1
        for i in range(sn, num, step):
            caseobj_ao = []
            caseobj_bot = []
            casebody_ao = {'address_objects': caseobj_ao}
            casebody_bot = {"botnet":{"custom_list":{"address":caseobj_bot}}}
            loop = self.dealwith_FOR_loop(i,num,step)
            for j in range(i, loop):
                a,b,c = self.dealwith_abc(a,b,c)
                ao_name = "botaddrobj-" + str(j)
                host_ip = "92." + str(c) + "." + str(b) + "." + str(a)
                # create json file for botnet filter
                with open(json_path_bot, 'r') as f:
                    json_dict = json.load(f)
                    params_bot = json_dict['botnet']['custom_list']['address'][0]
                    params_bot['name'] = ao_name
                caseobj_bot.append(params_bot)
                # create json file for address objects
                with open(json_path_ao, 'rb') as f0:
                    json_dict = json.load(f0)
                    params_ao = json_dict['address_objects'][0]
                    params_ao['ipv4']['name'] = ao_name
                    params_ao['ipv4']['host']['ip'] = host_ip
                caseobj_ao.append(params_ao)
                a += 1
            data_ao = json.dumps(casebody_ao)
            data_bot = json.dumps(casebody_bot)
            self.post_object(ipstr,url_ao,data_ao,i,loop-1)
            self.post_object(ipstr,url_bot,data_bot,i,loop-1)
    
    def post_GeoIPFilter(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_geo = 'https://' + ipstr + '/api/sonicos/geo-ip/addresses'
        url_ao = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4'
        json_path_geo = os.getcwd() + "\\JSON_FILE\\GeoIPFilter\\GeoIPFilter.json"
        json_path_ao = os.getcwd() + "\\JSON_FILE\\GeoIPFilter\\AddressObject.json"
        ################################add bonet filter with variable parameter#####################################################
        a, b = self.run_start_params(sn)
        c = 2
        num = en + 1
        for i in range(sn, num, step):
            caseobj_ao = []
            caseobj_geo = []
            casebody_ao = {'address_objects': caseobj_ao}
            casebody_geo = {"geo_ip":{"custom_list":{"address":caseobj_geo}}}
            loop = self.dealwith_FOR_loop(i,num,step)
            for j in range(i, loop):
                a,b,c = self.dealwith_abc(a,b,c)
                ao_name = "geoaddrobj-" + str(j)
                host_ip = "72." + str(c) + "." + str(b) + "." + str(a)
                # create json file for botnet filter
                with open(json_path_geo, 'rb') as f:
                    json_dict = json.load(f)
                    params_geo = json_dict['geo_ip']['custom_list']['address'][0]
                    params_geo['name'] = ao_name
                caseobj_geo.append(params_geo)
                # create json file for address objects
                with open(json_path_ao, 'rb') as f0:
                    json_dict = json.load(f0)
                    params_ao = json_dict['address_objects'][0]
                    params_ao['ipv4']['name'] = ao_name
                    params_ao['ipv4']['host']['ip'] = host_ip
                caseobj_ao.append(params_ao)
                a += 1
            data_ao = json.dumps(casebody_ao)
            data_geo = json.dumps(casebody_geo)
            self.post_object(ipstr,url_ao,data_ao,i,loop-1)
            self.post_object(ipstr,url_geo,data_geo,i,loop-1)

    def post_RestAPIAgents(self,ipstr,sn,en,step=1):
        sn,en=int(sn),int(en)
        url_agent = 'https://' + ipstr + '/api/sonicos/user/sso/third-party-api/clients'
        json_path_agent = os.getcwd() + "\\JSON_FILE\\RestAPIAgents\\RestAPIAgents.json"
        # ##############################Add API Agents#####################################
        a, b = self.run_start_params(sn)
        c = 2
        num = en + 1
        for i in range(sn, num, step):
            client = []
            agent_body = {"user":{"sso":{"third_party_api":{"client":client}}}}
            loop = self.dealwith_FOR_loop(i, num, step)
            for j in range(i, loop):
                a,b,c = self.dealwith_abc(a,b,c)
                host_ip = "172." + str(c) + "." + str(b) + "." + str(a)
                with open(json_path_agent, 'rb') as f_ag:
                    json_dict = json.load(f_ag)
                    agent_params = json_dict['user']['sso']['third_party_api']['client'][0]
                    agent_params['host'] = host_ip
                client.append(agent_params)
                a += 1
            data_agent = json.dumps(agent_body)
            self.post_object(ipstr, url_agent, data_agent,i,loop-1)

    def body(self,case, num, step=1):
        bodyname = "address_objects"
        if num >= step:
            if case == "addressObject":
                a = 1
                b = 1
                c = 1
                endnum = num + 1
                for i in range(1, endnum, step):
                    caseobj = []
                    casebody= {bodyname: caseobj}
                    print casebody
                    loop = i + step
                    for j in range(i, loop):
                        name = "src-" + str(j)
                        zone = "LAN"
                        a += 1
                        a, b, c = self.dealwith_abc(a, b, c)
                        host_ip = "12." + str(c) + "." + str(b) + "." + str(a)
                        addressObj = {
                            "ipv4": {
                                "name": name,
                                "zone": zone,
                                "host": {
                                    "ip": host_ip
                                }
                            }
                        }
                        caseobj.append(addressObj)
                        print "hello"
                        print caseobj
                    jsonname = casename + str(i) + '.json'
                    print jsonname
                    print type(jsonname)
                    t = os.path.join(os.path.dirname(__file__), jsonname)
                    print t
                    print "hello"
                    with open(jsonname, 'w') as f1:
                        json.dump(casebody, f1)

        else:
            print("enter num is wrong")


    # Commit configuration
    def commit(self,ipstr):
        url = 'https://' + ipstr + '/api/sonicos/config/pending'
        headers = {'Content-Type': 'application/json'}
        try:
            res = requests.post(url, headers=headers, verify=False)
            msg_commit_res = res.json()['status']['info'][0]['message']
            logging.info("Commit status code =={}!!commit respond message:{} ".format(res.status_code,msg_commit_res))
            if "Unauthorized" in msg_commit_res:
                print "For commit--Unauthorized. Try to login again."
                self.login(ipstr)
            elif "Not allowed in current mode" in msg_commit_res:
                print "commit error--{}. Try to set config mode.".format(msg_commit_res)
                self.set_configMode(ipstr)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            t = datetime.datetime.now()
            print "{}- CommitERROR - Web service exception, msg = {}".format(t,e)

    def delete(self,ipstr, num):
        for i in range(num):
            name = "test" + str(i)
            url = 'https://' + ipstr + '/api/sonicos/address-objects/ipv4/name/' + name
            headers = {'Content-Type': 'application/json'}
            try:
                r = requests.delete(url, headers=headers, verify=False)
                if (r.status_code == 200):
                    print ("Delete action successfully!")
                r.raise_for_status()
            except requests.exceptions.RequestException as e:
                print "- DeleteERROR - Web service exception, msg = {}".format(e)


    def logout(self,ipstr):
        url = 'https://' + ipstr + '/api/sonicos/auth'
        headers = {'Content-Type': 'application/json'}
        try:
            r = requests.delete(url, headers=headers, verify=False)
            if (r.status_code == 200):
                print ("Logout successfully!")
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print "- DeleteERROR - Web service exception, msg = {}".format(e)

    
