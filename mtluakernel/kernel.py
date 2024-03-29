import sys
import json

from ipykernel.kernelbase import Kernel as BaseKernel
from tornado.httpclient import AsyncHTTPClient
from tornado import gen

from . import __version__
from . import server

def parse_result(s):
    try:
        res = json.loads(s)
    except json.JSONDecodeError:
        return None, 'json is invalid'

    if not isinstance(res, dict):
        return None, 'json is not an object'

    if 'status' not in res:
        return None, "missing 'status' key"

    if not isinstance(res['status'], bool):
        return None, "'status' value is not a boolean"

    if 'value' in res and not isinstance(res['value'], str):
        return None, "'value' value is not a string"

    if 'stdout' in res and not isinstance(res['stdout'], str):
        return None, "'stdout' value is not a string"

    return res, None

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
        value, stdout = res.get('value'), res.get('stdout')

        if not silent:
            if stdout is not None:
                content = {'name': 'stdout', 'text': stdout}
                self.send_response(self.iopub_socket, 'stream', content)

            if value is not None:
                content = {'execution_count': self.execution_count,
                           'data': {'text/plain': value},
                           'metadata': {}}
                self.send_response(self.iopub_socket, 'execute_result',
                                   content)

        if res['status']:
            reply_content = {
                'status': 'ok',
                'payload': [],
                'user_expressions': {},
            }
        else:
            reply_content = {'status': 'error'}
        reply_content['execution_count'] = self.execution_count
        return reply_content
