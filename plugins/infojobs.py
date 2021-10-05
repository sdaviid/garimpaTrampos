from pydantic import BaseModel
import requests
import lxml.html
import json
import pkce
import jwt

from utils.logging_utils import create_default_logger
from utils import utils
from core.garimpaHandler import (
    garimpaHandler, 
    garimpaCompany, 
    garimpaJob, 
    garimpaJobs, 
    garimpaVacancy
)
from core.garimpaException import(
    NotExpectedStatusCode,
    AccessTokenNotFound
)


logger = create_default_logger("plugins/infojobs")

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
        def generate_cv_cc(length=43):
            cv = pkce.generate_code_verifier(length=length)
            cc = pkce.get_code_challenge(cv)
            return (cv, cc)
        code_verifier, code_challenge = generate_cv_cc()
        req_session = requests.Session()
        def generate_headers():
            return {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; A5010 Build/N2G48H; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/66.0.3359.158 Safari/537.36',
                'X-Requested-With': 'com.android.browser'
            }
        def initialize_login_process():
            url = 'https://login.infojobs.com.br/connect/authorize'
            query_params = {
                'redirect_uri': 'com.infojobs.app:/oauth2callback',
                'client_id': 'Android.Mobile',
                'response_type': 'code',
                'prompt': 'login',
                'state': 'NAntN1iGcg6BBu9MFObmwg',
                'scope': 'openid profile offline_access email InfoJobs api',
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256',
                'OrigenVisita': '496'
            }
            try:
                res = req_session.get(url, params=query_params, headers=generate_headers(), verify=True, allow_redirects=False, timeout=10)
                if res.status_code != 302:
                    raise NotExpectedStatusCode
            except NotExpectedStatusCode:
                logger.critical(f'Initialize login process expecting status code 302, got {res.status_code} instead')
            except Exception as err:
                logger.error('Exception initialize login process', exc_info=True)
            else:
                logger.info('Initialization login process ok')
                return res.headers['Location']
        def obtain_verification_token():
            url = initialize_login_process()
            if url:
                try:
                    res = req_session.get(url, headers=generate_headers(), verify=True, timeout=10)
                    if res.status_code != 200:
                        raise NotExpectedStatusCode
                    html_xml = lxml.html.fromstring(res.text)
                    token = html_xml.xpath('//input[@name="__RequestVerificationToken"]')[0].value
                except NotExpectedStatusCode:
                    logger.critical(f'Obtain verification token expecting status code 200, got {res.status_code} instead')
                except Exception as err:
                    logger.error('Exception obtain verification token', exc_info=True)
                else:
                    logger.info('Obtain verification token ok')
                    return (url, token)
        def first_step_login():
            url, token = obtain_verification_token()
            if url and token:
                payload = {
                    'Username': self.login,
                    'Password': self.senha,
                    'RememberLogin': 'true',
                    'button': 'login',
                    '__RequestVerificationToken': token,
                    'RememberLogin': 'false'
                }
                try:
                    headers = generate_headers()
                    headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
                    res = req_session.post(url, data=payload, headers=headers, verify=True, allow_redirects=False, timeout=10)
                    if res.status_code != 302:
                        raise NotExpectedStatusCode
                except NotExpectedStatusCode:
                    logger.critical(f'First step login expecting status code 302, got {res.status_code} instead')
                except Exception as err:
                    logger.error('Exception First step login', exc_info=True)
                else:
                    logger.info('First step login ok')
                    return True
        def second_step_login():
            if first_step_login():
                url = 'https://login.infojobs.com.br/connect/authorize/callback'
                query_params = {
                    'redirect_uri': 'com.infojobs.app:/oauth2callback',
                    'client_id': 'Android.Mobile',
                    'response_type': 'code',
                    'state': 'NAntN1iGcg6BBu9MFObmwg',
                    'scope': 'openid profile offline_access email InfoJobs api',
                    'code_challenge': code_challenge,
                    'code_challenge_method': 'S256',
                    'OrigenVisita': '496'
                }
                try:
                    res = req_session.get(url, params=query_params, headers=generate_headers(), verify=True, allow_redirects=False, timeout=10)
                    if res.status_code != 302:
                        raise NotExpectedStatusCode
                    code_access = res.headers['Location'].split('=')[1][0:res.headers['Location'].split('=')[1].index('&')]
                except NotExpectedStatusCode:
                    logger.critical(f'Second step login expecting status code 302, got {res.status_code} instead')
                except Exception as err:
                    logger.error('Exception Second step login', exc_info=True)
                else:
                    logger.info('Second step login ok')
                    return code_access
        def third_step_login():
            code_access = second_step_login()
            if code_access:
                url = 'https://login.infojobs.com.br/connect/token'
                payload = {
                    'client_secret': 'secret',
                    'client_id': 'Android.Mobile',
                    'code_verifier': code_verifier,
                    'redirect_uri': 'com.infojobs.app:/oauth2callback',
                    'code': code_access,
                    'grant_type': 'authorization_code'
                }
                try:
                    headers = generate_headers()
                    headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
                    res = req_session.post(url, data=payload, headers=headers, verify=True, timeout=10)
                    if res.status_code != 200:
                        raise NotExpectedStatusCode
                    if 'access_token' not in res.json():
                        raise AccessTokenNotFound
                    token_decrypt = jwt.decode(res.json()['access_token'], verify=False)
                    auth_data = {
                        'TOKEN': res.json()['access_token'],
                        'CANDIDATO': token_decrypt['IdCandidate']
                    }
                except NotExpectedStatusCode:
                    logger.critical(f'Third step login expecting status code 200, got {res.status_code} instead')
                except AccessTokenNotFound:
                    logger.critical('Access token JWT not found on connect/token response')
                except Exception as err:
                    logger.error('Exception Third step login', exc_info=True)
                else:
                    logger.info('Third step login ok')
                    return auth_data
        login_details = third_step_login()
        if login_details:
            logger.info('Infojobs login has been logged')
            self.auth_data = login_details
            self.logged = True
            return True
        logger.critical('Infojobs failed log-in')
        return False
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
                try:
                    r = requests.post(url, json=payload, headers=headers, verify=True)
                    if r.status_code != 200:
                        raise NotExpectedStatusCode
                except NotExpectedStatusCode:
                    logger.critical(f'Get key state expecting status code 200, got {r.status_code} instead')
                except Exception as err:
                    logger.error('Exception Get key state', exc_info=True)
                else:
                    j = json.loads(r.text)
                    if 'd' in j:
                        if 'IdLocation2' in j['d']:
                            retorno = j['d']['IdLocation2']
                    logger.info('Get key state ok')
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
                'Accept-Encoding': 'gzip'
            }
            payload = {
                "IdParent": int(key_uf),
                "IdType": 23
            }
            try:
                r = requests.post(url, json=payload, headers=headers, verify=True)
                if r.status_code != 200:
                    raise NotExpectedStatusCode
            except NotExpectedStatusCode:
                logger.critical(f'Get key city expecting status code 200, got {r.status_code} instead')
            except Exception as err:
                logger.error('Exception Get key city', exc_info=True)
            else:
                j = json.loads(r.text)
                if 'd' in j:
                    for i in j['d']:
                        if cidade.lower() in i['Text'].lower():
                            retorno = i['Value']
                            break
                logger.info('Get key city ok')
        return retorno
    def get_keyword_options(self, chave):
        retorno = False
        url = 'https://android.infojobs.com.br/mobile/app_webservices/Dictionaries.asmx/AutoComplete?OrigenVisita=496'
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Device-Info': '10#2#4#Oneplus A5010#API 25#496#3.6.12#%s#4#0' % (self.auth_data['CANDIDATO']),
            'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.2; A5010 Build/N2G48H)',
            'Accept-Encoding': 'gzip'
        }
        payload = {
            "IdType": 92,
            "Term": chave
        }
        try:
            r = requests.post(url, json=payload, headers=headers, verify=True)
            if r.status_code != 200:
                raise NotExpectedStatusCode
        except NotExpectedStatusCode:
            logger.critical(f'Get keywords options expecting status code 200, got {r.status_code} instead')
        except Exception as err:
            logger.error('Exception Get keywords options', exc_info=True)
        else:
            j = json.loads(r.text)
            if 'd' in j:
                retorno = []
                for i in j['d']:
                    retorno.append(i['Text'])
            logger.info('Get keywords options ok')
        return retorno
    def get_jobs(self, chave, cep, pagina=1):
        retorno = False
        try:
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
                        try:
                            r = requests.post(url, json=payload, headers=headers, verify=True)
                            if r.status_code != 200:
                                raise NotExpectedStatusCode
                        except NotExpectedStatusCode:
                            logger.critical(f'Get Jobs expecting status code 200, got {r.status_code} instead')
                        except Exception as err:
                            logger.error('Exception Get Jobs', exc_info=True)
                        else:
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
                                        emp_url = i['Url']
                                        emp_premium = True if i['IsLimited'] == 1 else False
                                        temp_emp = garimpaJob(id=emp_id, vacancy=emp_vaga, id_company=emp_idempresa, name=emp_nome, date_creation=emp_data, state=emp_estado, city=emp_cidade, description=emp_descr, is_premium=emp_premium, url=emp_url)
                                        data_emp.append(temp_emp)
                                    retorno = garimpaJobs.parse_obj({'status': 200, 'data': data_emp, 'total': int(j['d']['total']), 'page': int(pagina)})
                                    logger.info('Get Jobs ok')
                                    #retorno = garimpaJobs(statusresponse=data_emp, total=int(j['d']['total']), page=int(pagina))
        except IndexError as err:
            retorno = garimpaJobs.parse_obj({'status': 402, 'data': [], 'message': str(err)})
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
        r = requests.post(url, json=payload, headers=headers, verify=True)
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
        r = requests.post(url, json=payload, headers=headers, verify=True)
        if r.status_code == 200:
            j = json.loads(r.text)
            print(r.text)
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
















