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
  def Request(url, request_type):
    response = {}
    if request_type == RequestTypes.GET:
      response = requests.get(url)
    return response.json()
