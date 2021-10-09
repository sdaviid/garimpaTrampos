import requests
import lxml.html
import json


from utils.logging_utils import create_default_logger
from utils import utils
from core.garimpaHandler import garimpaHandler, garimpaCompany, garimpaJob, garimpaJobs, garimpaVacancy

logger = create_default_logger("plugins/catho")



class catho(garimpaHandler):
    auth_data = None
    login = None
    senha = None
    logged = False
    def __init__(self, login, senha):
        self.login = login
        self.senha = senha
        self.make_login()
    def get_api_key(self):
        retorno = {}
        url = 'https://api-services.catho.com.br/config/v1/auth-keys/android'
        headers = {
            'User-Agent': 'App Android 2.15.6-20210623_1048; API 25; ONEPLUS A5010',
            'X-Origin': 'app-android',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Api-Key': 'ia2IqjIFaLsq62jOMAnbF4NL7sbUW4fqkIhPVto8',
            'Host': 'api-services.catho.com.br',
            'Accept-Encoding': 'gzip'
        }
        r = requests.get(url, headers=headers, verify=True)
        if r.status_code == 200:
            j = json.loads(r.text)
            if 'services' in j:
                if 'bff-job-ad-search' in j['services']:
                    retorno.update({'SERVICE': j['services']['bff-job-ad-search']['api-key']})
                if 'auth' in j['services']:
                    retorno.update({'AUTH': j['services']['auth']['api-key']})
                if 'locations' in j['services']:
                    retorno.update({'LOCATION': j['services']['locations']['api-key']})
                if 'job-ads-api' in j['services']:
                    retorno.update({'VAGAS': j['services']['job-ads-api']['api-key']})
                if 'resume' in j['services']:
                    retorno.update({'OPCOES': j['services']['resume']['api-key']})
        return retorno
    def make_login(self):
        retorno = False
        keys = self.get_api_key()
        if keys:
            url = 'https://api-services.catho.com.br/auth/v1/signin'
            headers = {
                'User-Agent': 'App Android 2.15.6-20210623_1048; API 25; ONEPLUS A5010',
                'X-Origin': 'app-android',
                'Accept': 'application/json',
                'X-Api-Key': keys['AUTH'],
                'Content-Type': 'application/json; charset=UTF-8',
                'Host': 'api-services.catho.com.br',
                'Accept-Encoding': 'gzip'
            }
            payload = {
                "client_id": "281",
                "code_challenge": "kHkeoUPbb7RAlRQAR+nDrE9FAPwFjqiNRQBTnwU8J+A",
                "code_challenge_method": "S256",
                "password": self.senha,
                "provider": "password",
                "redirect_uri": "com.catho.app://authorize-callback",
                "response_type": "code",
                "state": "ab9567e2690548ad88b48d2b56f799e6",
                "token": None,
                "username": self.login
            }
            r = requests.post(url, json=payload, headers=headers, verify=True)
            if r.status_code == 200:
                j = json.loads(r.text)
                if 'code' in j:
                    url = 'https://api-services.catho.com.br/auth/v1/token'
                    payload = {
                        "client_id": "281",
                        "code": j['code'],
                        "code_verifier": "cIE--yqN.~nF7pv/MJ9rsmEAAv6A1XMVBJ8ZiCSg_2qm3--/mwP2GB",
                        "grant_type": "authorization_code",
                        "redirect_uri": "com.catho.app://authorize-callback",
                        "refresh_token": None
                    }
                    r = requests.post(url, json=payload, headers=headers, verify=True)
                    if r.status_code == 200:
                        j = json.loads(r.text)
                        if 'access_token' in j:
                            keys.update({'TOKEN': j['access_token']})
                            self.auth_data = keys
                            retorno = True
                            self.logged = True
        return retorno
    def get_key_state(self, cep=None, inicial=None):
        retorno = False
        if self.logged == True:
            if cep is not None:
                dados_cep = utils.get_cep_data(cep)
                if dados_cep:
                    inicial = dados_cep['UF']
            if inicial:
                url = 'https://api-services.catho.com.br/locations/v1/locations/countries/31/states'
                headers = {
                    'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
                    'User-Agent': 'App Android 2.15.6-20210623_1048; API 25; ONEPLUS A5010',
                    'X-Origin': 'app-android',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-Api-Key': self.auth_data['LOCATION'],
                    'Host': 'api-services.catho.com.br',
                    'Accept-Encoding': 'gzip'
                }
                r = requests.get(url, headers=headers, verify=True)
                if r.status_code == 200:
                    j = json.loads(r.text)
                    for i in j:
                        if inicial.lower() == i['initials'].lower():
                            retorno = i['id']
                            break
        return retorno
    def get_keyword_options(self, chave):
        retorno = False
        if self.logged == True:
            url = 'https://api-services.catho.com.br/resume/v1/job-position/list?q=%s' % (str(chave))
            headers = {
                'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
                'User-Agent': 'App Android 2.15.6-20210623_1048; API 25; ONEPLUS A5010',
                'X-Origin': 'app-android',
                'api-client-id': '2',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Api-Key': self.auth_data['OPCOES'],
                'Host': 'api-services.catho.com.br',
                'Accept-Encoding': 'gzip'
            }
            r = requests.get(url, headers=headers, verify=True)
            if r.status_code == 200:
                j = json.loads(r.text)
                if 'data' in j:
                    retorno = []
                    for i in j['data']:
                        retorno.append(i['title'])
            else:
                pass
        return retorno
    def get_key_city(self, key_uf, cep=None, cidade=None):
        if self.logged == True:
            if cep is not None:
                dados_cep = utils.get_cep_data(cep)
                if dados_cep:
                    cidade = dados_cep['Cidade']
            if cidade:
                url = 'https://api-services.catho.com.br/locations/v1/locations/countries/31/states/%s/cities' % (str(key_uf))
                headers = {
                    'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
                    'User-Agent': 'App Android 2.15.6-20210623_1048; API 25; ONEPLUS A5010',
                    'X-Origin': 'app-android',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-Api-Key': self.auth_data['LOCATION'],
                    'Host': 'api-services.catho.com.br',
                    'Accept-Encoding': 'gzip'
                }
                r = requests.get(url, headers=headers, verify=True)
                if r.status_code == 200:
                    j = json.loads(r.text)
                    for i in j:
                        if cidade.lower() == i['name'].lower():
                            retorno = i['id']
                            break
        return retorno
    def get_company(self, *kwg):
        raise NotImplementedError
    def get_vacancy(self, key_vaga):
        retorno = False
        if self.logged == True:
            url = 'https://api-services.catho.com.br/job-ads/jobs/%s/?format=json' % (str(key_vaga))
            headers = {
                'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
                'User-Agent': 'App Android 2.15.6-20210623_1048; API 25; ONEPLUS A5010',
                'X-Origin': 'app-android',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Api-Key': self.auth_data['VAGAS'],
                'Host': 'api-services.catho.com.br',
                'Accept-Encoding': 'gzip',
                'Content-Type': 'application/json; charset=UTF-8'
            }
            r = requests.get(url, headers=headers, verify=True)
            if r.status_code == 200:
                j = json.loads(r.text)
                emp_cargo = j['title']
                emp_descr = j['activities']
                emp_obs = j['observation']
                emp_periodo = j['period']
                emp_data = j['entry_date']
                emp_modelo = j['contracting_models']
                emp_perfil = j['profiles']
                emp_recruta = j['main_recruiter']
                emp_salario = j['salary']
                emp_beneficios = j['benefits']
                emp_estado = j['positions'][0]['state'] if j['positions'] else ''
                emp_cidade = j['positions'][0]['city'] if j['positions'] else ''
                emp_requerimentos = j['requirements']
                emp_empresa = j['hirer']
                emp_vaga = j['role']
                dd = {
                    'CARGO': emp_cargo,
                    'DESCR': emp_descr,
                    'OBSERVACAO': emp_obs,
                    'PERIODO': emp_periodo,
                    'DATA': emp_data,
                    'MODELO': emp_modelo,
                    'PERFIL': emp_perfil,
                    'RECRUTA': emp_recruta,
                    'SALARIO': emp_salario,
                    'BENEFICIOS': emp_beneficios,
                    'UF': emp_estado,
                    'CIDADE': emp_cidade,
                    'REQUERIMENTOS': emp_requerimentos,
                    'DADOS_EMPRESA': emp_empresa
                }
                retorno = garimpaVacancy(title=emp_cargo, salary=emp_salario, level='', contract=emp_modelo, period=emp_periodo, method=emp_periodo, description=emp_descr, requiriments=emp_requerimentos, vacancy=emp_vaga, id_company=[], name=emp_empresa, date_creation=emp_data, state=emp_estado, city=emp_cidade, is_premium=False, is_confidential=False, benefitis=emp_beneficios, company_data=None)
        return retorno
    def get_jobs(self, chave, cep, pagina=1):
        retorno = False
        if self.logged == True:
            dados_cep = utils.get_cep_data(cep)
            if dados_cep:
                key_uf = self.get_key_state(inicial=dados_cep['UF'])
                if key_uf:
                    key_cidade = self.get_key_city(key_uf, cidade=dados_cep['Cidade'])
                    if key_cidade:
                        url = 'https://api-services.catho.com.br/job-ad-search/?sort_by=relevance&page=' + str(pagina) + '&results_per_page=10&location_form=disjunctive'
                        headers = {
                            'Authorization': 'Bearer %s' % (self.auth_data['TOKEN']),
                            'User-Agent': 'App Android 2.15.6-20210623_1048; API 25; ONEPLUS A5010',
                            'X-Origin': 'app-android',
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'X-Api-Key': self.auth_data['SERVICE'],
                            'Host': 'api-services.catho.com.br',
                            'Accept-Encoding': 'gzip',
                            'Content-Type': 'application/json; charset=UTF-8'
                        }
                        payload = {
                            "api": {
                                "origin": "catho_search",
                                "service": "search"
                            },
                            "browser": {
                                "device": "mobile",
                                "referrer": "com.catho.app"
                            },
                            "facets": [],
                            "fields": ["job_id", "job_customized_data", "score"],
                            "query": {
                                "filters": {
                                    "jobs": {
                                        "city_id": [int(key_cidade)],
                                        "hierarchical_level_id": [],
                                        "ppd_profile_id": [],
                                        "professional_area_id": [],
                                        "profile_id": 1,
                                        "region_id": [],
                                        "salary_range_id": [0, 2, 3],
                                        "segment_id": [],
                                        "state_id": []
                                    }
                                },
                                "keywords": chave
                            },
                            "user": {
                                "candidate_id": 64355631,
                                "ip": "177.194.38.181",
                                "subscriber": True
                            }
                        }
                        r = requests.post(url, json=payload, headers=headers, verify=True)
                        if r.status_code == 200:
                            j = json.loads(r.text)
                            data_emp = []
                            retorno = {}
                            keys_jobs = ['jobs', 'jobsExpanded']
                            for i in keys_jobs:
                                if i in j:
                                    for y in j[i]:
                                        if 'job' in y:
                                            dados = y['job']
                                            emp_id = dados['id']
                                            emp_vaga = dados['title']
                                            emp_nome = dados['hirer']['name']
                                            emp_data = dados['entry_date']
                                            emp_descr = dados['activities']
                                            emp_periodo = dados['period']
                                            emp_modelo = dados['contracting_models'] if dados['contracting_models'] else []
                                            emp_salario = dados['salary']['range_description'] if dados['salary'] else ''
                                            emp_beneficios = dados['benefits'] if dados['benefits'] else []
                                            emp_estado = dados['positions'][0]['state'] if dados['positions'] else ''
                                            emp_cidade = dados['positions'][0]['city'] if dados['positions'] else ''
                                            temp_emp = garimpaJob(id=emp_id, vacancy=emp_vaga, name=emp_nome, date_creation=emp_data, description=emp_descr, period=emp_periodo, model=emp_modelo, salary=emp_salario, benefits=emp_beneficios, state=emp_estado, city=emp_cidade)
                                            data_emp.append(temp_emp)
                            retorno = garimpaJobs.parse_obj({'status': 200, 'data': data_emp, 'total': int(j['meta']['total']['jobAds']), 'page': int(pagina)})
                            #retorno = garimpaJobs(response=data_emp, total=int(j['meta']['total']['jobAds']), page=int(pagina))
        return retorno