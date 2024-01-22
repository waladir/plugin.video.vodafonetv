# -*- coding: utf-8 -*-
import sys
import xbmcaddon
import xbmcgui

import json
import time 

from libs.api import API
from libs.utils import apiVersion

class Session:
    def __init__(self):
        self.load_session()

    def create_session(self):
        self.get_token()
        self.save_session()

    def get_token(self):
        addon = xbmcaddon.Addon()
        api = API()

        
        headers = api.headers
# hodnota vtv-authentication a zasifrovane heslo lze vzit z volani endpointu https://apigw.cz.vtv.vodafone.com/vtv/authentication/v1/credentials pri prihlaseni na webu. S heslem primo z nastaveni (nesifrovanym) prihlaseni nefunguje
        headers.update({'vtv-authentication' : 'web:xxxx'})
        post = {"password":"xxxx","username":addon.getSetting('username'),"deviceBrandId":"22"}
        data = api.call_api(url = 'https://apigw.cz.vtv.vodafone.com/vtv/authentication/v1/credentials', data = post, headers = headers)
        print(data)
        if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaLoginResponse':
            xbmcgui.Dialog().notification('Vodafone TV','Problém při přihlášení', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        ks = data['result']['loginSession']['ks']



        post = {'ks' : ks, 'apiVersion' : apiVersion}
        data = api.call_api(url = 'https://3062.vfp2.ott.kaltura.com/api_v3/service/household/action/get', data = post, headers = api.headers)
        if 'err' in data or not 'result' in data or not 'masterUsers' in data['result'] or len(data['result']['masterUsers']) == 0:
            xbmcgui.Dialog().notification('Vodafone TV','Problém při přihlášení1', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        master_userid = data['result']['masterUsers'][0]['id']
        userid = None
        for user in data['result']['users']:
            if user['id'] != master_userid:
                userid = user['id']
        if userid is None:
            xbmcgui.Dialog().notification('Vodafone TV','Problém při přihlášení2', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 

        post = {'ks' : ks, 'apiVersion' : apiVersion, 'userIdToSwitch' : userid}
        data = api.call_api(url = 'https://3062.vfp2.ott.kaltura.com/api_v3/service/session/action/switchUser', data = post, headers = api.headers)
        print(data)
        if 'err' in data or not 'result' in data or not 'objectType' in data['result'] or data['result']['objectType'] != 'KalturaLoginSession':
            xbmcgui.Dialog().notification('Vodafone TV','Problém při přihlášení3', xbmcgui.NOTIFICATION_ERROR, 5000)
            sys.exit() 
        self.ks = data['result']['ks']
        self.ks_expiry = data['result']['expiry']

    def load_session(self):
        from libs.settings import Settings
        settings = Settings()
        data = settings.load_json_data({'filename' : 'session.txt', 'description' : 'session'})
        if data is not None :
            data = json.loads(data)
            if 'ks_expiry' not in data or int(data['ks_expiry']) < int(time.time()):
                self.create_session()
            else:
                self.ks = data['ks']
                self.ks_expirt = data['ks_expiry']                
        else:
            self.create_session()
        self.save_session                            

    def save_session(self):
        from libs.settings import Settings
        settings = Settings()
        data = json.dumps({'ks' : self.ks, 'ks_expiry' : self.ks_expiry})        
        settings.save_json_data({'filename' : 'session.txt', 'description' : 'session'}, data)

    def remove_session(self):
        from libs.settings import Settings
        settings = Settings()
        settings.reset_json_data({'filename' : 'session.txt', 'description' : 'session'})
        self.create_session()
        xbmcgui.Dialog().notification('Vodafone TV', 'Byla vytvořená nová session', xbmcgui.NOTIFICATION_INFO, 5000)
