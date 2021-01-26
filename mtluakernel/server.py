import json
from uuid import uuid4

from tornado.httputil import responses as std_http_responses
import tornado.web as web
from tornado.locks import Event


class BaseHandler(web.RequestHandler):
    def initialize(self, requests):
        self.requests = requests

    def write_error(self, code, msg=None, **kwargs):
        if msg is None:
            resp = std_http_responses.get(code, 'Unknown')
            msg = '%s %s' % (code, resp)
        self.write({'error': msg})


def parse_code(req):
    if ('Content-Type' not in req.headers
        or req.headers['Content-Type'] != 'application/json'):
        return None, 'payload is not json'

    try:
        req = json.loads(req.body)
    except json.JSONDecodeError:
        return None, 'json is invalid'

    if not isinstance(req, dict):
        return None, 'json is not an object'

    if 'code' not in req:
        return None, "missing 'code' key"

    if not isinstance(req['code'], str):
        return None, "'code' value is not a string"

    return req['code'], None

class ExecRequestsHandler(BaseHandler):
    def get(self):
        self.set_status(200)
        self.set_header('content-type', 'application/json')
        self.write(json.dumps([{'id': id, 'code': req['code']}
                               for id, req in self.requests.items()]))

    async def post(self):
        code, err = parse_code(self.request)
        if code is None:
            self.send_error(400, msg=err)
            return

        id = str(uuid4())
        req = {'code': code, 'done_event': Event()}
        self.requests[id] = req
        await req['done_event'].wait()

        self.set_status(200)
        self.write({'result': req['result']})
        del self.requests[id]


def parse_result(req):
    if ('Content-Type' not in req.headers
        or req.headers['Content-Type'] != 'application/json'):
        return None, 'payload is not json'

    try:
        res = json.loads(req.body)
    except json.JSONDecodeError:
        return None, 'json is invalid'

    if not isinstance(res, dict):
        return None, 'json is not an object'

    if 'id' not in res:
        return None, "missing 'id' key"

    if not isinstance(res['id'], str):
        return None, "'id' value is not a string"

    if 'result' not in res:
        return None, "missing 'result' key"

    if not isinstance(res['result'], str):
        return None, "'result' value is not a string"

    return {'id': res['id'], 'result': res['result']}, None

class ExecResultsHandler(BaseHandler):
    def post(self):
        res, err = parse_result(self.request)
        if res is None:
            self.send_error(400, msg=err)
            return

        self.set_status(200)
        req = self.requests.get(res['id'], None)
        if req is None: return # ignore unknown ids

        req['result'] = res['result']
        req['done_event'].set() # wake synchronous request handler


def listen():
    requests = {}
    app = web.Application([
        ('/exec_requests', ExecRequestsHandler, dict(requests=requests)),
        ('/exec_results', ExecResultsHandler, dict(requests=requests)),
    ])
    return app.listen(2468)


if __name__ == '__main__':
    server = listen()
    from tornado.ioloop import IOLoop; IOLoop.current().start()
