"""Local static preview of site/dist, served like GitHub Pages: no special headers.

The in-browser OpenModelica compiler needs no cross-origin isolation for compiling and
simulating, so a plain static host is enough.
"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse
import errno
import os

os.chdir(Path(__file__).resolve().parents[1] / 'site/dist')
class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.wasm': 'application/wasm', '.mjs': 'text/javascript'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535')
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError as error:
        hint = ' Try npm start -- --port 8001' if error.errno == errno.EADDRINUSE else ''
        parser.exit(1, f'Cannot start server: {error}.{hint}\n')
    with server:
        print(f'Local: http://127.0.0.1:{server.server_port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
