from pydantic import BaseModel
from typing import Optional, Union
from fastapi import Query
from fastapi.responses import JSONResponse



class garimpaHandlerSuccess(BaseModel):
    status: Union[bool, int]
    data: Union[list, dict, None]
    def json_response(self):
        return JSONResponse(status_code=self.status, content=self.dict())





class garimpaHandlerError(garimpaHandlerSuccess):
    message: str





class garimpaPlugins(BaseModel):
    data: list





class garimpaPlugin(BaseModel):
    key: str
    title: str
    url: str
    active: bool





class garimpaCompany(BaseModel):
    description: str
    number_employees: str
    area: str
    url: str
    id: int
    name: str
    location: str



class garimpaVacancy(BaseModel):
    title: str
    salary: str
    level: str
    contract: str
    period: str
    method: str
    description: Union[str, dict, list]
    requiriments: Union[str, dict, list]
    vacancy: str
    id_company: Union[str, int]
    name: str
    date_creation: str
    state: str
    city: str
    is_premium: Union[bool, None]
    is_confidential: Union[bool, None]
    benefits: Union[str, list, dict, None]
    company_data: garimpaCompany



class garimpaJob(BaseModel):
    id: Union[str, int]
    vacancy: Union[str, dict, list]
    id_company: Optional[Union[str, list, dict, None]] = None
    name: Union[str, dict, list]
    date_creation: str
    state: str
    city: str
    description: Union[str, list, dict]
    is_premium: Optional[Union[bool, None]] = None
    model: Optional[Union[str, list, dict, None]] = None
    period: Optional[Union[str, list, dict, None]] = None
    salary: Optional[Union[str, list, dict, None]] = None
    benefits: Optional[Union[str, list, dict, None]] = None






class garimpaJobs(BaseModel):
    data: list
    total: Optional[Union[int, None]]= Query(1)
    page: Optional[Union[int, None]]= Query(1)




class garimpaHandler(object):
    def make_login(self):
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


