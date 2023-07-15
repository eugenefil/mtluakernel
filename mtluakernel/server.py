import json

from tornado.httputil import responses as std_http_responses
import tornado.web as web
from tornado.concurrent import Future


class BaseHandler(web.RequestHandler):
    def initialize(self, code):
        self.code = code

    def write_error(self, status_code, **kwargs):
        resp = std_http_responses.get(status_code, 'Unknown')
        msg = '%s %s' % (status_code, resp)
        self.write({'error': msg})


class CodeHandler(BaseHandler):
    def get(self):
        self.set_status(200)
        self.write(self.code.get('body', {'code': ''}))

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

        done = Future()
        self.code.update(body=self.request.body, done_future=done)
        res = await done

        self.set_status(200)
        self.write(res)


class ResultHandler(BaseHandler):
    def post(self):
        self.set_status(200)
        if not self.code: return # ignore unknown result

        # pass code execution result and wake CodeHandler.post()
        self.code['done_future'].set_result(self.request.body)
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
