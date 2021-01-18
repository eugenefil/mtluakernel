# TODO handle AsyncHTTPClient client exceptions
# TODO handle json exceptions
# TODO search for specific response id on server

import sys
import json

from ipykernel.kernelbase import Kernel as BaseKernel
from tornado.httpclient import AsyncHTTPClient
from tornado import gen

from . import __version__
from . import server

def get_result(resp):
    if ('Content-Type' not in resp.headers
        or resp.headers['Content-Type'] != 'application/json'):
        return None, 'payload is not json'

    try:
        res = json.loads(resp.body)
    except json.JSONDecodeError:
        return None, 'json is invalid'

    if not isinstance(res, dict):
        return None, 'json is not an object'

    if 'result' not in res:
        return None, "missing 'result' key"

    if not isinstance(res['result'], str):
        return None, "'result' value is not a string"

    return res['result'], None

class MTLuaKernel(BaseKernel):
    implementation = 'Minetest Lua Kernel'
    implementation_version = __version__
    banner = '%s %s' % (implementation, implementation_version)
    language_info = {
        'name': 'lua',
        'mimetype': 'text/x-lua',
        'file_extension': '.lua',
    }

    def start(self):
        super().start()
        self.server = server.listen()

    @gen.coroutine
    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        if not code or code.isspace(): return

        client = AsyncHTTPClient()
        headers = {'content-type': 'application/json'}
        body = json.dumps({'code': code})
        resp = yield client.fetch('http://127.0.0.1:2468/exec_requests',
                                  method='POST', headers=headers,
                                  body=body)
        res, err = get_result(resp)
        if res is None:
            self.log.error('Got bad response from execution server: %s', err)
            return

        if not silent:
            content = {'execution_count': self.execution_count,
                       'data': {'text/plain': res},
                       'metadata': {}}
            self.send_response(self.iopub_socket, 'execute_result', content)

        return {
            'status': 'ok',
            # The base class increments the execution count
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }
