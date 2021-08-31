import requests
import lxml.html
import json
import codecs


def read_config_file():
    retorno = False
    data = False
    with codecs.open("config.json", encoding='UTF-8', mode='r') as f:
        data = f.read()
    if data:
    	retorno = json.loads(data)
    return retorno



def get_cep_data(cep):
    retorno = False
    url = 'https://www.mapacep.com.br/index.php'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'PHPSESSID=qn3amf7dn55gv1v58vk865gr97',
        'Host': 'www.mapacep.com.br',
        'Origin': 'https://www.mapacep.com.br',
        'Referer': 'https://www.mapacep.com.br/index.php',
        'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
        'sec-ch-ua-mobile': '?0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }
    payload = {
        'keywords': cep.replace('.', '').replace('-', ''),
        'sid': 'Busca por CEP, Cidade, Endereço, CNPJ ou Cód. IBGE',
        'submit': 'Pesquisar'
    }
    r = requests.post(url, data=payload, headers=headers, verify=False)
    h = lxml.html.fromstring(r.text)
    dados_cep = h.xpath('//div[@class="row resultado-buscacep alinhaesquerda"]/div[@class="col-md-6"]/p/b/following-sibling::text()')
    lat = dados_cep[3].strip()
    lon = dados_cep[4].strip()
    cidade = dados_cep[6].strip()
    uf = dados_cep[9].strip()
    if lat and lon:
        retorno = {'Latitude': lat, 'Longitude': lon, 'Cidade': cidade, 'UF': uf}
    return retorno
