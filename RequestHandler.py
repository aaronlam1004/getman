import json
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
    def GetJsonFromRequest(request):
        request_json = {}
        for k, v in vars(request).items():
            if k != "hooks":
                request_json[k] = v
        return json.dumps(request_json)

    @staticmethod
    def Request(url, request_type, params={}, headers={}, body={}, form={}):
        response = {}
        session = requests.Session()
        request = requests.Request(request_type.value, url, params=params, headers=headers, json=body, data=form)
        res = None
        try:
            res = session.send(request.prepare())
            response = res.json()
        except Exception as exception:
            if res is not None:
                response = { "status_code": res.status_code, "reason": res.reason }
            else:
                response = { "status_code": 504, "reason": "Gateway Timeout" }
            response = json.dumps(response)
            response = json.loads(response)
        return request, response


