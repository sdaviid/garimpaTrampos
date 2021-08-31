Idéia
-----

A idéia deste projeto é reunir diversas plataformas de emprego e pradrozinar sua saída, tornando possível realizar a mesma pesquisa em diversas bases.

A base do projeto é o Web Scrapping, a maioria das plataformas possui uma API própria, mas muitas vezes ela é destinada para a área de recrutamento ou são destinadas a uso interno (dentro do próprio site/aplicativo)

Cada plataforma de emprego é usada como um plugin, seguindo um padrão do programa para padrozinar a pesquisa e saída de dados.

Plugins
-------

No momento o projeto possuí duas plataformas integradas:
* InfoJobs
* Catho

Demo
----


Uma versão demo está disponível em: http://garimpatrampos.co.vu:8000/docs

Requisitos
----------

FastAPI
uvicorn


Utilização
----------


Para utilização de qualquer dos plugins citados será necessário configurar uma conta seguindo o padrão abaixo:

./config.json

```json
[
	{
		"plugin_script": "infojobs",
		"title": "InfoJobs",
		"active": true,
		"url": "https://www.infojobs.com.br",
		"username": "email@exemplo.com",
		"password": "senha"
	},
]
```

O script ao ser inicializado tentará realizar o login, em caso de problemas o plugin ficará indisponível.



Para executar o servidor, em um terminal execute

```bash
uvicorn main:app
```

