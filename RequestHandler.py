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
  def Request(url, request_type, body={}, form={}):
    response = {}
    if request_type == RequestTypes.GET:
      response = requests.get(url, json=body, data=form)
    elif request_type == RequestTypes.POST:
      response = requests.post(url, json=body, data=form)
    return response.json()
