from fastapi import FastAPI, Path, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional


from core import utils  
from core.garimpaHandler import garimpaPlugins, garimpaPlugin, garimpaJobs, garimpaCompany, garimpaVacancy, garimpaJobs, garimpaHandlerError, garimpaHandlerSuccess
import importlib
from pydoc import locate

from pydantic import BaseModel




def load_plugins():
    plugins_loaded = {}
    plugins = utils.read_config_file()
    if plugins:
        for plugin in plugins:
            if plugin['active'] is True:
                try:
                    plugin_mod = locate(f'core.{plugin["plugin_script"]}.{plugin["plugin_script"]}')
                except Exception as e:
                    print(f'plugin {plugin["plugin_script"]} failed to load exp {e}')
                    plugin_mod = False
                if plugin_mod:
                    plugins_loaded.update({plugin["plugin_script"]: {"data": plugin, "module": plugin_mod, "active": False, "plugin_instance": None}})
    return plugins_loaded




plugins = load_plugins()


for plugin_key in list(plugins.keys()):
    username = plugins[plugin_key]['data']['username']
    password = plugins[plugin_key]['data']['password']
    plugin_instance = plugins[plugin_key]['module'](username, password)
    if plugin_instance:
        if plugin_instance.logged is True:
            plugins[plugin_key].update({'active': True, 'instance': plugin_instance})
        else:
            plugins[plugin_key].update({'active': False})


origins = ["*"]

app = FastAPI(
    servers=[
        {"url": "http://api.garimpatrampos.co.vu", "description": "Staging environment"}
    ]
)

#app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 404:
        return garimpaHandlerError(status=404, data=[], message="Route not found").json_response()
    return garimpaHandlerError(status=exc.status_code, data=[], message=str(exc.detail)).json_response()



@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)




@app.get('/get-job-sources')
def get_job_sources():
    output = []
    for plugin in plugins:
        output_data = garimpaPlugin(key=plugins[plugin]['data']['plugin_script'], title=plugins[plugin]['data']['title'], active=plugins[plugin]['active'], url=plugins[plugin]['data']['url'])
        output.append(output_data)
    data = garimpaHandlerSuccess(status=200, data=garimpaPlugins(data=output))
    return data.json_response()



class Message(BaseModel):
    message: str



responses = {
    404: {"description": "Plugin Not Found", "model": Message},
    400: {"description": "Plugin Disabled", "model": Message},
    501: {"description": "Not Implemented", "model": Message},
}



def validate_plugin(key_source):
    if key_source not in plugins:
        return garimpaHandlerError(status=404, data=[], message="Plugin not found")
    if plugins[key_source]['active'] is not True:
        return garimpaHandlerError(status=400, data=[], message="Plugin not activate")
    return garimpaHandlerSuccess(status=200, data=[])




@app.get(
    '/search-vacancies/{key_source}/{keyword}/{zipcode}',
    response_model=garimpaJobs,
    responses={
        **responses
    }
)
def search_vacancies(key_source: str, keyword: str, zipcode: str, page: Optional[int] = Query(1, alias="page")):
    validate = validate_plugin(key_source)
    if validate.status == 200:
        try:
            validate.data = plugins[key_source]['instance'].get_jobs(keyword, zipcode, page)
            return validate.json_response()
        except NotImplementedError:
            return JSONResponse(status_code=501, content={"message": "Not Implemented"})
    else:
        return validate.json_response()



@app.get(
    '/get-vacancy/{key_source}/{id_vacancy}',
    response_model=garimpaVacancy,
    responses={
        **responses
    }
)
def get_vacancy(key_source: str, id_vacancy: int):
    validate = validate_plugin(key_source)
    if validate.status == 200:
        try:
            return plugins[key_source]['instance'].get_vacancy(id_vacancy)
        except NotImplementedError:
            return JSONResponse(status_code=501, content={"message": "Not Implemented"})
    else:
        return JSONResponse(status_code=validate.status, content=validate.dict())






@app.get(
   '/get-company/{key_source}/{id_company}',
   response_model=garimpaCompany,
   responses= {
        **responses,
        502: {"model": Message, "description": "not faund"},
   }
)
def get_company(key_source: str, id_company: int):
    validate = validate_plugin(key_source)
    if validate.status == 200:
        try:
            return plugins[key_source]['instance'].get_company(id_company)
        except NotImplementedError:
            return JSONResponse(status_code=501, content={"message": "Not Implemented"})
    else:
        return JSONResponse(status_code=validate.status, content=validate.dict())



@app.get('/get-keywords-from/{key_source}/{keyword}')
def get_keywords_from(key_source: str, keyword: str):
    validate = validate_plugin(key_source)
    if validate.status == 200:
        try:
            return plugins[key_source]['instance'].get_keyword_options(keyword)
        except NotImplementedError:
            return JSONResponse(status_code=501, content={"message": "Not Implemented"})
    else:
        return JSONResponse(status_code=validate.status, content=validate.dict())


