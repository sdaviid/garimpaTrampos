from pydoc import locate

from pydantic import BaseModel

from fastapi import FastAPI, Path, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional, Union


from utils.logging_utils import create_default_logger
from utils import utils
from core.garimpaHandler import(
    garimpaPlugins,
    garimpaPlugin,
    garimpaJobs,
    garimpaCompany,
    garimpaVacancy,
    garimpaJobs,
    garimpaHandlerError,
    garimpaHandlerSuccess,
    garimpaHandlerResponse
)
from core.garimpaException import(
    NotExpectedStatusCode,
    WrongLengthCEP,
    FailedGetVacancyData
)




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


@app.exception_handler(IndexError)
async def value_error_exception_handler(request: Request, exc: IndexError):
    return JSONResponse(
        status_code=350,
        content={"message": str(exc)},
    )






responses = {
    404: {"description": "Plugin Not Found", "model": garimpaHandlerResponse},
    400: {"description": "Plugin Disabled", "model": garimpaHandlerResponse},
    501: {"description": "Not Implemented", "model": garimpaHandlerResponse},
}





@app.get(
    '/get-job-sources',
    response_model=Union[garimpaPlugins, garimpaHandlerResponse]
)
def get_job_sources():
    output = []
    for plugin in plugins:
        output.append(garimpaPlugin.parse_obj(
                                            {
                                                'key': plugins[plugin]['data']['plugin_script'],
                                                'title': plugins[plugin]['data']['title'],
                                                'active': plugins[plugin]['active'],
                                                'url': plugins[plugin]['data']['url']
                                            }
                                        )
        )
        #output_data = garimpaPlugin(key=plugins[plugin]['data']['plugin_script'], title=plugins[plugin]['data']['title'], active=plugins[plugin]['active'], url=plugins[plugin]['data']['url'])
        #output.append(output_data)
    return garimpaHandlerResponse(status=200, data=output).json_response()
    #return garimpaHandlerResponse.parse_obj({'status': 200, 'data': output})
    #data = garimpaHandlerSuccess(status=200, data=garimpaPlugins(data=output))
    #return data.json_response()



class Message(BaseModel):
    message: str




def validate_plugin(key_source):
    if key_source not in plugins:
        return garimpaHandlerResponse(status=404, message='Pluin nor found').json_response()
        #return garimpaHandlerResponse.parse_obj({'status': 404, 'data': [], 'message': 'Plugin n2ot found'})
        #return garimpaHandlerError(status=404, data=[], message="Plugin not found")
    if plugins[key_source]['active'] is not True:
        return garimpaHandlerResponse(status=400, message='Pluin nor activate').json_response()
        #return garimpaHandlerResponse.parse_obj({'status': 400, 'data': [], 'message': 'Plugin not activate'})
    return True
    #return garimpaHandlerResponse.parse_obj({'status': 200, 'data': []})
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
    if validate == True:
        try:
            jobs = plugins[key_source]['instance'].get_jobs(keyword, zipcode, page)
            if jobs:
                return jobs
            #return jobs.parse_obj({'status': 200})
            #return garimpaHandlerResponse.parse_obj({'status': 200, 'data': plugins[key_source]['instance'].get_jobs(keyword, zipcode, page)})
            #validate.data = plugins[key_source]['instance'].get_jobs(keyword, zipcode, page)
            #return validate.json_response()
        except IndexError as err:
            #return garimpaHandlerResponse.parse_obj({'status': 433, 'message': 'Somethi3333ng Went Wrong'})
            raise IndexError(err)
        except NotImplementedError:
            return garimpaHandlerResponse.parse_obj({'status': 501, 'message': 'Not Implemented'})
            #return JSONResponse(status_code=501, content={"message": "Not Implemented"})
        except NotExpectedStatusCode:
            return garimpaHandlerResponse.parse_obj({'status': 500, 'message': 'Something Went Wrong'})
        except WrongLengthCEP as err:
            return garimpaHandlerResponse(status=312, data=[], message=str(err)).json_response()
    else:
        return validate



@app.get(
    '/get-vacancy/{key_source}/{id_vacancy}',
    response_model=Union[garimpaVacancy, garimpaHandlerResponse],
    responses={
        **responses
    }
)
def get_vacancy(key_source: str, id_vacancy: int):
    validate = validate_plugin(key_source)
    if validate == True:
        try:
            return garimpaVacancy(status=200, data=plugins[key_source]['instance'].get_vacancy(id_vacancy)).json_response()
        except NotImplementedError:
            return JSONResponse(status_code=501, content={"message": "Not Implemented"})
        except FailedGetVacancyData as err:
            return garimpaHandlerResponse(status=500, message=str(err)).json_response()
        except Exception as err:
            return JSONResponse(status_code=501, content={"message": "Not Implemented"})
    else:
        return validate






@app.get(
   '/get-company/{key_source}/{id_company}',
   response_model=Union[garimpaCompany, garimpaHandlerResponse],
   responses= {
        **responses,
        502: {"model": Message, "description": "not faund"},
   }
)
def get_company(key_source: str, id_company: int):
    validate = validate_plugin(key_source)
    if validate == True:
        try:
            return garimpaCompany(status=200, data=plugins[key_source]['instance'].get_company(id_company)).json_response()
            #return plugins[key_source]['instance'].get_company(id_company)
        except NotImplementedError:
            return garimpaHandlerResponse(status=501, data=[], message="Not Implemented").json_response()
            #return JSONResponse(status_code=501, content={"message": "Not Implemented"})
    else:
        return validate



@app.get('/get-keywords-from/{key_source}/{keyword}')
def get_keywords_from(key_source: str, keyword: str):
    validate = validate_plugin(key_source)
    if validate == True:
        try:
            return plugins[key_source]['instance'].get_keyword_options(keyword)
        except NotImplementedError:
            return JSONResponse(status_code=501, content={"message": "Not Implemented"})
    else:
        return validate


