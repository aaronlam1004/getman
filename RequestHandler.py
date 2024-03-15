from enum import Enum

import requests

class RequestTypes(Enum):
  GET = "GET"
  POST = "POST"
  PUT = "PUT"
  PATCH = "PATCH"
  DELETE = "DELETE"
  HEAD = "HEAD"
  OPTIONS = "OPTIONS"

class RequestHandler:
  @staticmethod
  def GetRequestJson(request):
    request_json = {}
    for k, v in vars(request).items():
      if k != "hooks":
        request_json[k] = v
    return request_json
  
  @staticmethod
  def Request(url, request_type, body={}, form={}):
    response = {}
    session = requests.Session()
    request = requests.Request(request_type.value, url, json=body, data=form)
    res = session.send(request.prepare())
    response = res.json()
    return request, response
