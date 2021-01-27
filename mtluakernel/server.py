# TODO need code id for code/result match in case of server/game restarts?
# TODO client breaks conn while server is awaiting result
# TODO unknown endpoints (e.g. /foo) end up sending html error

import json

from tornado.httputil import responses as std_http_responses
import tornado.web as web
from tornado.concurrent import Future


class BaseHandler(web.RequestHandler):
    def initialize(self, code):
        self.code = code

    def write_error(self, errcode, msg=None, **kwargs):
        if msg is None:
            resp = std_http_responses.get(errcode, 'Unknown')
            msg = '%s %s' % (errcode, resp)
        self.write({'error': msg})


def parse_code(s):
    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        return None, 'json is invalid'

    if not isinstance(obj, dict):
        return None, 'json is not an object'

    if 'code' not in obj:
        return None, "missing 'code' key"

    if not isinstance(obj['code'], str):
        return None, "'code' value is not a string"

    return obj['code'], None

class CodeHandler(BaseHandler):
    def get(self):
        self.set_status(200)
        self.write({'code': self.code.get('text', '')})

    async def post(self):
        # Reject new code requests, if one is already processing. We
        # don't do multiple requests, since it bears w/ it issues
        # concerning sequential execution or what to do w/ later
        # requests when the first one failed, i.e. queue
        # management. This management must be done in clients, closer
        # to where those requests originate. For example jupyter
        # kernel does it and sends here one request at a time.
        if self.code:
            self.send_error(429) # too many requests
            return

        code, err = parse_code(self.request.body)
        if code is None:
            self.send_error(400, msg=err)
            return

        done = Future()
        self.code.update(text=code, done_future=done)
        res = await done

        self.set_status(200)
        self.write({'result': res})


def parse_result(s):
    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        return None, 'json is invalid'

    if not isinstance(obj, dict):
        return None, 'json is not an object'

    if 'result' not in obj:
        return None, "missing 'result' key"

    if not isinstance(obj['result'], str):
        return None, "'result' value is not a string"

    return obj['result'], None

class ResultHandler(BaseHandler):
    def post(self):
        res, err = parse_result(self.request.body)
        if res is None:
            self.send_error(400, msg=err)
            return

        self.set_status(200)
        if not self.code: return # ignore unknown result

        # pass code execution result and wake CodeHandler.post()
        self.code['done_future'].set_result(res)
        # result is processed, clear the code object immediately
        # (before the next GET /code could possibly access it)
        self.code.clear()


def listen():
    kws = dict(code={}) # shared object for storing code request attrs
    app = web.Application([
        ('/code', CodeHandler, kws),
        ('/result', ResultHandler, kws),
    ])
    return app.listen(2468)


if __name__ == '__main__':
    server = listen()
    from tornado.ioloop import IOLoop; IOLoop.current().start()
