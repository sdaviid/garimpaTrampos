from pydantic import BaseModel
import requests
import lxml.html
import json
import pkce
import jwt

from core import utils
from core.garimpaHandler import garimpaHandler, garimpaCompany, garimpaJob, garimpaJobs, garimpaVacancy

class infojobs(garimpaHandler):
    auth_data = None
    login = None
    senha = None
    logged = False
    def __init__(self, login, senha):
        self.login = login
        self.senha = senha
        self.make_login()
    def make_login(self):
        retorno = False
        cv = pkce.generate_code_verifier(length=43)
        cc = pkce.get_code_challenge(cv)
        url = 'https://login.infojobs.com.br/connect/authorize'
        query = {
            'redirect_uri': 'com.infojobs.app:/oauth2callback',
            'client_id': 'Android.Mobile',
            'response_type': 'code',
            'prompt': 'login',
            'state': 'NAntN1iGcg6BBu9MFObmwg',
            'scope': 'openid profile offline_access email InfoJobs api',
            'code_challenge': cc,
            'code_challenge_method': 'S256',
            'OrigenVisita': '496'
        }
        req = requests.Session()
        r1 = req.get(url, params=query, verify=False, allow_redirects=False)
        url2 = r1.headers['Location']
        r2 = req.get(url2, verify=False)
        h2 = lxml.html.fromstring(r2.text)
        token = h2.xpath('//input[@name="__RequestVerificationToken"]')[0].value
        payload2 = {
            'Username': self.login,
            'Password': self.senha,
            'RememberLogin': 'true',
            'button': 'login',
            '__RequestVerificationToken': token,
            'RememberLogin': 'false'
        }
        r3 = req.post(url2, data=payload2, verify=False, allow_redirects=False)
        url4 = 'https://login.infojobs.com.br/connect/authorize/callback'
        query4 = {
            'redirect_uri': 'com.infojobs.app:/oauth2callback',
            'client_id': 'Android.Mobile',
            'response_type': 'code',
            'state': 'NAntN1iGcg6BBu9MFObmwg',
            'scope': 'openid profile offline_access email InfoJobs api',
            'code_challenge': cc,
            'code_challenge_method': 'S256',
            'OrigenVisita': '496'
        }
        r4 = req.get(url4, params=query4, verify=False, allow_redirects=False)
        if r4.status_code == 302:
            try:
                codigo = r4.headers['Location'].split('=')[1][0:r4.headers['Location'].split('=')[1].index('&')]
                url5 = 'https://login.infojobs.com.br/connect/token'
                payload5 = {
                    'client_secret': 'secret',
                    'client_id': 'Android.Mobile',
                    'code_verifier': cv,
                    'redirect_uri': 'com.infojobs.app:/oauth2callback',
                    'code': codigo,
                    'grant_type': 'authorization_code'
                }
                r5 = requests.post(url5, data=payload5, verify=False)
                if r5.status_code == 200:
                    j5 = json.loads(r5.text)
                    token_decrypt = jwt.decode(j5['access_token'], verify=False)
                    keys = {'TOKEN': j5['access_token'], 'CANDIDATO': token_decrypt['IdCandidate']}
                    self.auth_data = keys
                    self.logged = True
                    retorno = True
            except Exception as e:
                print('ext r4 ... %s' % (str(e)))
        return retorno
    def get_key_state(self, cep=None, lat=None, lon=None):
        retorno = False
        if self.logged:
            if cep is not None:
                dados_cep = utils.get_cep_data(cep)
                if dados_cep:
                    lat = dados_cep['Latitude']
                    lon = dados_cep['Longitude']
            if lat is not None and lon is not None:
                url = 'https://android.infojobs.com.br/mobile/app_webservices/Candidates.asmx/GetLocation2?OrigenVisita=496'
                headers = {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Device-Info': '10#2#4#Oneplus A5010#API 25#496#3.6.12#%s#4#0' % (self.auth_data['CANDIDATO']),
                    'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
                    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2; A5010 Build/N2G48H)',
                    'Host': 'android.infojobs.com.br',
                    'Accept-Encoding': 'gzip'
                }
                payload = {
                    "pLocation": {
                        "CEP": "",
                        "IdLocation2": 0,
                        "IdLocation3": 0,
                        "IdLocation5": -1,
                        "Latitude": float(lat),
                        "Location2": "",
                        "Location3": "",
                        "Location5": "",
                        "Longitude": float(lon),
                        "Street": "",
                        "Parent": 0,
                        "Text": "",
                        "Value": 0
                    }
                }
                r = requests.post(url, json=payload, headers=headers, verify=False)
                if r.status_code == 200:
                    j = json.loads(r.text)
                    if 'd' in j:
                        if 'IdLocation2' in j['d']:
                            retorno = j['d']['IdLocation2']
        return retorno
    def get_key_city(self, key_uf, cep=None, cidade=None):
        retorno = False
        if cep is not None:
            dados_cep = utils.get_cep_data(cep)
            if dados_cep:
                cidade = dados_cep['Cidade']
        if cidade:
            url = 'https://android.infojobs.com.br/mobile/app_webservices/Dictionaries.asmx/Read?OrigenVisita=496'
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Device-Info': '10#2#4#Oneplus A5010#API 25#496#3.6.12#%s#4#0' % (self.auth_data['CANDIDATO']),
                'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
                'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2; A5010 Build/N2G48H)',
                'Host': 'android.infojobs.com.br',
                'Accept-Encoding': 'gzip'
            }
            payload = {
                "IdParent": int(key_uf),
                "IdType": 23
            }
            r = requests.post(url, json=payload, headers=headers, verify=False)
            if r.status_code == 200:
                j = json.loads(r.text)
                if 'd' in j:
                    for i in j['d']:
                        if cidade.lower() in i['Text'].lower():
                            retorno = i['Value']
                            break
        return retorno
    def get_keyword_options(self, chave):
        retorno = False
        url = 'https://android.infojobs.com.br/mobile/app_webservices/Dictionaries.asmx/AutoComplete?OrigenVisita=496'
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Device-Info': '10#2#4#Oneplus A5010#API 25#496#3.6.12#%s#4#0' % (self.auth_data['CANDIDATO']),
            'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2; A5010 Build/N2G48H)',
            'Host': 'android.infojobs.com.br',
            'Accept-Encoding': 'gzip'
        }
        payload = {
            "IdType": 92,
            "Term": chave
        }
        r = requests.post(url, json=payload, headers=headers, verify=False)
        if r.status_code == 200:
            j = json.loads(r.text)
            if 'd' in j:
                retorno = []
                for i in j['d']:
                    retorno.append(i['Text'])
        return retorno
    def get_jobs(self, chave, cep, pagina=1):
        retorno = False
        dados_cep = utils.get_cep_data(cep)
        if dados_cep:
            key_uf = self.get_key_state(lat=dados_cep['Latitude'], lon=dados_cep['Longitude'])
            if key_uf:
                key_cidade = self.get_key_city(key_uf, cidade=dados_cep['Cidade'])
                if key_cidade:
                    url = 'https://android.infojobs.com.br/mobile/app_webservices/Vacancy.asmx/List?OrigenVisita=496'
                    headers = {
                        'Content-Type': 'application/json; charset=utf-8',
                        'Device-Info': '10#2#4#Oneplus A5010#API 25#496#3.6.12#%s#4#0' % (self.auth_data['CANDIDATO']),
                        'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
                        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2; A5010 Build/N2G48H)',
                        'Host': 'android.infojobs.com.br',
                        'Accept-Encoding': 'gzip'
                    }
                    payload = {
                        "Find": {
                            "Category1": "",
                            "Category2": "",
                            "IdLocation1": 12,
                            "IdLocation2": [int(key_uf)],
                            "IdLocation3": [int(key_cidade)],
                            "Job": "",
                            "KeyWords": chave,
                            "Latitude": float(dados_cep['Latitude']),
                            "Location2": "",
                            "Location3": "",
                            "Longitude": float(dados_cep['Longitude']),
                            "Order": "",
                            "PageNumber": int(pagina),
                            "PageSize": 10,
                            "Radius": -1
                        }
                    }
                    r = requests.post(url, json=payload, headers=headers, verify=False)
                    if r.status_code == 200:
                        j = json.loads(r.text)
                        if 'd' in j:
                            retorno = {}
                            if 'genericList' in j['d']:
                                data_emp = []
                                for i in j['d']['genericList']:
                                    emp_id = i['IdVacancy']
                                    emp_vaga = i['Title']
                                    emp_idempresa = i['IdCompany']
                                    emp_nome = i['Company']
                                    emp_data = i['GridDate']
                                    emp_estado = i['Location2']
                                    emp_cidade = i['Location3']
                                    emp_descr = i['Description']
                                    emp_premium = True if i['IsLimited'] == 1 else False
                                    temp_emp = garimpaJob(id=emp_id, vacancy=emp_vaga, id_company=emp_idempresa, name=emp_nome, date_creation=emp_data, state=emp_estado, city=emp_cidade, description=emp_descr, is_premium=emp_premium)
                                    data_emp.append(temp_emp)
                                retorno = garimpaJobs(data=data_emp, total=int(j['d']['total']), page=int(pagina))
        return retorno
    def get_company(self, key_empresa):
        retorno = False
        url = 'https://android.infojobs.com.br/mobile/app_webservices/Companies.asmx/Read?OrigenVisita=496'
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Device-Info': '10#2#4#Oneplus A5010#API 25#496#3.6.12#%s#4#0' % (self.auth_data['CANDIDATO']),
            'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2; A5010 Build/N2G48H)',
            'Host': 'android.infojobs.com.br',
            'Accept-Encoding': 'gzip'
        }
        payload = {
            "IdCandidate": 51022506,
            "IdCompany": int(key_empresa),
            "Name": ""
        }
        r = requests.post(url, json=payload, headers=headers, verify=False)
        if r.status_code == 200:
            j = json.loads(r.text)
            if 'd' in j:
                dados = j['d']
                emp_descr = str(dados['Descriptions'])
                emp_funcionarios = str(dados['Employees'])
                emp_setor = str(dados['Sector'])
                emp_url = str(dados['Url'])
                emp_id = str(dados['IdCompany'])
                emp_nome = str(dados['Name'])
                emp_localizacao = str(dados['Location3'])
                retorno = garimpaCompany(description=emp_descr, number_employees=emp_funcionarios, area=emp_setor, url=emp_url, id=emp_id, name=emp_nome, location=emp_localizacao)
        return retorno
    def get_vacancy(self, key_vaga):
        retorno = False
        url = 'https://android.infojobs.com.br/mobile/app_webservices/Vacancy.asmx/Read2?OrigenVisita=496'
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Device-Info': '10#2#4#Oneplus A5010#API 25#496#3.6.12#%s#4#0' % (self.auth_data['CANDIDATO']),
            'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2; A5010 Build/N2G48H)',
            'Host': 'android.infojobs.com.br',
            'Accept-Encoding': 'gzip'
        }
        payload = {
            "IdCandidate": 51022506,
            "IdContractTypeProduct": 16,
            "IdVacancy": int(key_vaga)
        }
        r = requests.post(url, json=payload, headers=headers, verify=False)
        if r.status_code == 200:
            j = json.loads(r.text)
            if 'd' in j:
                dados = j['d']
                emp_cargo = dados['Category2']
                emp_salario = dados['SalaryRange']
                emp_tipo = dados['ManagerialLevel']
                emp_contrato = dados['ContractWorkType']
                emp_periodo = dados['WorkingHour']
                emp_metodo = dados['WorkMethod']
                emp_descr = dados['Descriptions']['Content'] if dados['Descriptions'] is not None else []
                emp_exigencias = dados['Requirements']['Content'] if dados['Requirements'] is not None else []
                emp_vaga = dados['Title']
                emp_titulo = dados['Job']
                emp_id = dados['IdCompany']
                emp_empresa = dados['Company']
                emp_data = dados['GridDate']
                emp_estado = dados['Location2']
                emp_cidade = dados['Location3']
                emp_categoria = dados['Category1']
                emp_premium = dados['Limited']
                emp_confidencial = dados['CompanyHidden']
                emp_beneficios = dados['Benefits']['Content'] if dados['Benefits'] is not None else []
                retorno = garimpaVacancy(title=emp_cargo, salary=emp_salario, level=emp_tipo, contract=emp_contrato, period=emp_periodo, method=emp_metodo, description=emp_descr, requiriments=emp_exigencias, vacancy=emp_vaga, id_company=emp_id, name=emp_empresa, date_creation=emp_data, state=emp_estado, city=emp_cidade, is_premium=emp_premium, is_confidential=emp_confidencial, benefitis=emp_beneficios, company_data=self.get_company(emp_id))
        return retorno









