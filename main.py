from fastapi import FastAPI, Path, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional, Union


from utils.logging_utils import create_default_logger
from utils import utils
from core.garimpaHandler import garimpaPlugins, garimpaPlugin, garimpaJobs, garimpaCompany, garimpaVacancy, garimpaJobs, garimpaHandlerError, garimpaHandlerSuccess, garimpaHandlerResponse
from core.garimpaException import NotExpectedStatusCode
import importlib
from pydoc import locate

from pydantic import BaseModel


logger = create_default_logger("main")



def load_plugins():
    plugins_loaded = {}
    plugins = utils.read_config_file()
    if plugins:
        for plugin in plugins:
            if plugin['active'] is True:
                try:
                    plugin_mod = locate(f'plugins.{plugin["plugin_script"]}.{plugin["plugin_script"]}')
                except Exception as err:
                    logger.error(f'plugin {plugin["plugin_script"]} failed to load module', exc_info=True)
                    plugin_mod = False
                if plugin_mod:
                    plugins_loaded.update({plugin["plugin_script"]: {"data": plugin, "module": plugin_mod, "active": False, "plugin_instance": None}})
                    logger.info(f'plugin {plugin["plugin_script"]} was loaded')
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

# app = FastAPI(
#     servers=[
#         {"url": "http://api.garimpatrampos.co.vu", "description": "Staging environment"}
#     ]
# )

app = FastAPI()

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
        output.append(garimpaPlugin.parse_obj({'key': plugins[plugin]['data']['plugin_script'], 'title': plugins[plugin]['data']['title'], 'active': plugins[plugin]['active'], 'url': plugins[plugin]['data']['url']}))
        #output_data = garimpaPlugin(key=plugins[plugin]['data']['plugin_script'], title=plugins[plugin]['data']['title'], active=plugins[plugin]['active'], url=plugins[plugin]['data']['url'])
        #output.append(output_data)
    return garimpaHandlerResponse.parse_obj({'status': 200, 'data': output})
    #data = garimpaHandlerSuccess(status=200, data=garimpaPlugins(data=output))
    #return data.json_response()



class Message(BaseModel):
    message: str



responses = {
    404: {"description": "Plugin Not Found", "model": garimpaHandlerResponse},
    400: {"description": "Plugin Disabled", "model": garimpaHandlerResponse},
    501: {"description": "Not Implemented", "model": garimpaHandlerResponse},
}



def validate_plugin(key_source):
    if key_source not in plugins:
        return garimpaHandlerResponse.parse_obj({'status': 404, 'data': [], 'message': 'Plugin n2ot found'})
        #return garimpaHandlerError(status=404, data=[], message="Plugin not found")
    if plugins[key_source]['active'] is not True:
        return garimpaHandlerResponse.parse_obj({'status': 400, 'data': [], 'message': 'Plugin not activate'})
    return garimpaJobs.parse_obj({'status': 200, 'data': []})
    #return garimpaHandlerSuccess(status=200, data=[])




@app.get(
    '/search-vacancies/{key_source}/{keyword}/{zipcode}',
    response_model=Union[garimpaJobs, garimpaHandlerResponse],
    responses={
        **responses
    }
)
def search_vacancies(key_source: str, keyword: str, zipcode: str, page: Optional[int] = Query(1, alias="page")):
    validate = validate_plugin(key_source)
    if validate.status == 200:
        try:
            jobs = plugins[key_source]['instance'].get_jobs(keyword, zipcode, page)
            if jobs:
                return jobs
            #return jobs.parse_obj({'status': 200})
            #return garimpaHandlerResponse.parse_obj({'status': 200, 'data': plugins[key_source]['instance'].get_jobs(keyword, zipcode, page)})
            #validate.data = plugins[key_source]['instance'].get_jobs(keyword, zipcode, page)
            #return validate.json_response()
        except IndexError:
            return garimpaHandlerResponse.parse_obj({'status': 433, 'message': 'Somethi3333ng Went Wrong'})
        except NotImplementedError:
            return garimpaHandlerResponse.parse_obj({'status': 501, 'message': 'Not Implemented'})
            #return JSONResponse(status_code=501, content={"message": "Not Implemented"})
        except NotExpectedStatusCode:
            return garimpaHandlerResponse.parse_obj({'status': 500, 'message': 'Something Went Wrong'})
    else:
        return validate



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


