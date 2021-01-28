# TODO handle AsyncHTTPClient client exceptions
# TODO handle json exceptions
# TODO search for specific response id on server
# TODO if not code or code.isspace(): return

import sys
import json

from ipykernel.kernelbase import Kernel as BaseKernel
from tornado.httpclient import AsyncHTTPClient
from tornado import gen

from . import __version__
from . import server

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
        resp = yield AsyncHTTPClient().fetch(
            'http://127.0.0.1:2468/code',
            method='POST',
            # w/ request_timeout=0 it seems to just hang w/out request
            # being sent, so we use arbitrarily long timeout instead
            # (since code may be executed arbitrarily long)
            request_timeout=1e9,
            body=json.dumps({'code': code}))

        res, err = parse_result(resp.body)
        if res is None:
            self.log.error('Got bad response from execution server: %s', err)
            return

        if not silent and res != 'nil':
            content = {'execution_count': self.execution_count,
                       'data': {'text/plain': res},
                       'metadata': {}}
            self.send_response(self.iopub_socket, 'execute_result',
                               content)

        return {
            'status': 'ok',
            # The base class increments the execution count
            'execution_count': self.execution_count,
            'payload': [],
            'user_expressions': {},
        }
