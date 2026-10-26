#!/usr/bin/env python3
"""Run the browser client and its two local WebSocket services together."""
import asyncio
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen
import webbrowser

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / '.local'
CHECKOUT = STATE / 'browser-client'
ASSETS = STATE / 'browser-assets'
PID_FILE = STATE / 'browser.pid'
TAILNET_FILE = STATE / 'tailnet.json'
URL = 'http://127.0.0.1:8000'


def running():
    try:
        with urlopen(URL + '/health', timeout=1) as response:
            return json.load(response).get('project') == str(ROOT)
    except (OSError, ValueError):
        return False


def open_browser():
    if os.environ.get('COSMIC_NO_BROWSER') != '1':
        webbrowser.open(URL)


def stop():
    if not PID_FILE.exists():
        print('The browser services are not running.')
        return
    pid = int(PID_FILE.read_text())
    command = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True).stdout
    if pid <= 1 or str(Path(__file__).resolve()) not in command:
        PID_FILE.unlink(missing_ok=True)
        print('Removed a stale browser PID file.')
        return
    os.kill(pid, signal.SIGTERM)
    print('Stopping the browser services. You can close the game tab.')


async def serve():
    import websockets
    sys.path.insert(0, str(CHECKOUT / 'web'))
    from server import Handler
    from assets_server import AssetServer
    from ws_proxy import MapleStoryProxy

    class LocalHandler(Handler):
        def translate_path(self, path):
            request = unquote(urlsplit(path).path)
            files = {'/': CHECKOUT / 'web/index.html',
                     '/web/index.html': CHECKOUT / 'web/index.html',
                     '/web/config.json': CHECKOUT / 'web/config.json'}
            for name in ('mobile-controls.js', 'mobile-controls.css'):
                files['/web/' + name] = CHECKOUT / 'web' / name
            for name in ('JourneyClient.js', 'JourneyClient.wasm', 'JourneyClient.wasm.map'):
                files['/build/' + name] = CHECKOUT / 'build' / name
            for asset in ASSETS.glob('*.nx'):
                files['/assets/' + asset.name] = asset
            return str(files.get(request, CHECKOUT / '__not_found__'))

        def do_GET(self):
            if self.path == '/health':
                payload = json.dumps({'project': str(ROOT), 'pid': os.getpid(),
                                      'origins': origins}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            elif self.path == '/favicon.ico':
                self.send_response(204)
                self.end_headers()
            else:
                super().do_GET()

    httpd = ThreadingHTTPServer(('127.0.0.1', 8000), LocalHandler)
    assets = AssetServer(str(ASSETS))
    proxy = MapleStoryProxy(allowed_targets={('127.0.0.1', port) for port in (8484, 7575, 7576, 7577)})
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)
    origins = ['http://127.0.0.1:8000', 'http://localhost:8000']
    if TAILNET_FILE.exists():
        origin = json.loads(TAILNET_FILE.read_text()).get('origin', '')
        parsed = urlsplit(origin)
        if parsed.scheme == 'https' and parsed.hostname and parsed.hostname.endswith('.ts.net') and parsed.port == 8443:
            origins.append(origin)
    http_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    try:
        async with websockets.serve(assets.handler, '127.0.0.1', 8765,
                                    origins=origins, max_size=50 * 1024 * 1024, compression=None), \
                   websockets.serve(proxy.handle_client, '127.0.0.1', 8080, origins=origins):
            http_thread.start()
            PID_FILE.write_text(str(os.getpid()))
            print(f'Cosmic is ready in your browser: {URL}', flush=True)
            print('Press Control-C or use stop-macos.command to stop these services.', flush=True)
            open_browser()
            await stop_event.wait()
    finally:
        if http_thread.is_alive():
            httpd.shutdown()
            http_thread.join()
        httpd.server_close()
        if PID_FILE.exists() and PID_FILE.read_text() == str(os.getpid()):
            PID_FILE.unlink()


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'start'
    if action == 'stop':
        stop()
    elif action == 'status':
        if not running():
            sys.exit('The browser services are not running.')
        print(URL)
    elif action == 'start':
        if running():
            print(f'Browser services are already running: {URL}')
            open_browser()
            return
        try:
            asyncio.run(serve())
        except OSError as error:
            sys.exit(f'Could not start browser services: {error}. Ports 8000, 8080 and 8765 must be free.')
    else:
        sys.exit('Usage: browser_services.py [start|stop|status]')


if __name__ == '__main__':
    main()
