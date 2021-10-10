from pydantic import BaseModel, Field
from typing import Optional, Union, List, Dict
from fastapi import Query
from fastapi.responses import JSONResponse


from utils.logging_utils import create_default_logger


logger = create_default_logger("core.handler")


class garimpaHandlerSuccess(BaseModel):
    status: Union[bool, int]
    data: Union[list, dict, None]
    def json_response(self):
        return JSONResponse(status_code=self.status, content=self.dict())





class garimpaHandlerError(garimpaHandlerSuccess):
    message: str



class garimpaHandlerResponse(BaseModel):
    status: Union[bool, int, None]
    data: Optional[Union[list, dict, None]] = []
    message: Optional[Union[str, None]] = None
    def json_response(self):
        return JSONResponse(status_code=self.status, content=self.dict())



class garimpaPlugin(BaseModel):
    key: str
    title: str
    url: str
    active: bool



class garimpaPlugins(garimpaHandlerResponse):
    data: List[garimpaPlugin]
    #data: Union[list, dict, None]









class garimpaCompanyData(BaseModel):
    description: str
    number_employees: str
    area: str
    url: str
    id: int
    name: str
    location: str




class garimpaCompany(garimpaHandlerResponse):
    data: Union[garimpaCompanyData, None]



class garimpaVacancyData(BaseModel):
    title: str = Field(
        title='Categoria', 
        description='Categoria da vaga'
    )
    salary: Union[str, dict, list, None] = Field(
        title='Salário',
        description='Salário disponibilizado na vaga'
    )
    level: str = Field(
        title='Nível de Hierarquia'
    )
    contract: Union[str, dict, list, None] = Field(
        title='Tipo de contrato',
        description='Tipo de contrato (CLT,PJ,FREELANCE)'
    )
    period: Union[str, dict, list, None] = Field(
        title='Jornada de trabalho'
    )
    method: Union[str, dict, list, None] = Field(
        title='Tipo de jornada',
        description='Tipo de jornada(Home Office, Presencial)'
    )
    description: Union[str, dict, list] = Field(
        title='Descrição da vaga'
    )
    requirements: Union[str, dict, list] = Field(
        title='Requerimentos',
        description='Requerimentos para se candidatar'
    )
    vacancy: Union[str, dict, list, None] = Field(
        title='Título da vaga'
    )
    id_company: Union[str, dict, list, int, None] = Field(
        title='ID da empresa',
        description='ID da empresa dentro da plataforma'
    )
    name: Union[str, dict, list, None] = Field(
        title='Nome da empresa'
    )
    date_creation: str = Field(
        title='Data de criação',
        description='Data vaga foi postada'
    )
    state: str = Field(
        title='Estado da vaga'
    )
    city: str = Field(
        title='Cidade da vaga'
    )
    is_premium: Union[bool, None] = Field(
        title='É uma vaga premium?',
        description='Determina se a vaga é apenas para usuários Premium da plataforma'
    )
    is_confidential: Union[bool, None] = Field(
        title='É empresa confidencial?',
        description='Determina se a empresa contratante está como confidencial'
    )
    benefits: Union[str, list, dict, None] = Field(
        title='Beneficios'
    )
    company_data: Union[str, dict, list, garimpaCompanyData, None] = Field(
        title='Informações da empresa'
    )





class garimpaVacancy(garimpaHandlerResponse):
    data: Union[garimpaVacancyData, None]




class garimpaJob(BaseModel):
    id: Union[str, int]
    vacancy: Union[str, dict, list]
    id_company: Optional[Union[str, list, dict, None]] = None
    name: Union[str, dict, list]
    date_creation: str
    state: str
    city: str
    description: Union[str, list, dict]
    url: Optional[Union[str, None]] = None
    is_premium: Optional[Union[bool, None]] = None
    model: Optional[Union[str, list, dict, None]] = None
    period: Optional[Union[str, list, dict, None]] = None
    salary: Optional[Union[str, list, dict, None]] = None
    benefits: Optional[Union[str, list, dict, None]] = None






class garimpaJobs(garimpaHandlerResponse):
    data: List[garimpaJob]
    total: Optional[Union[int, None]]= Query(0)
    page: Optional[Union[int, None]]= Query(0)
    #response: List[garimpaJob]




class garimpaHandler(object):
    def __init__(self, title=None, logged=False):
        self.logged = logged
        self.title = title
    #     self.teste()
    # def teste(self):
    #     logger.info('{} - {}'.format(self.title, 'SIM' if self.logged is True else 'NAO'))
    # def __getattribute__(self, item):
    #     logger.info('__getattribute__ {}'.format(item))
    #     return super().__getattribute__(item)
    def make_login(self):
        # logger.info('CALLING MAKE LOGIN')
        # super().make_login()
        pass
    def get_key_state(self, *args, **kw):
        pass
    def get_key_city(self, *args, **kw):
        pass
    def get_keyword_options(self, *args, **kw):
        pass
    def get_vacancy(self, *args, **kw):
        pass
    def get_jobs(self, *args, **kw):
        pass
    def get_company(self, *args, **kw):
        pass


