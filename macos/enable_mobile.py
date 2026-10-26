#!/usr/bin/env python3
"""Keep the local game services reachable privately from the user's tailnet."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / '.local'
PYTHON = STATE / 'browser-venv/bin/python'
SERVICES = ROOT / 'macos/browser_services.py'


def port_open(port):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=1):
            return True
    except OSError:
        return False


def health():
    try:
        with urlopen('http://127.0.0.1:8000/health', timeout=1) as response:
            result = json.load(response)
            return result if result.get('project') == str(ROOT) else {}
    except (OSError, ValueError):
        return {}


def background(command, log_name):
    with (STATE / log_name).open('ab') as log:
        subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                         stdout=log, stderr=log, start_new_session=True,
                         env={**os.environ, 'COSMIC_NO_BROWSER': '1'})


def keep_awake(service_pid):
    command = ['/usr/bin/caffeinate', '-i', '-w', str(service_pid)]
    pid_file = STATE / 'mobile-awake.pid'
    if pid_file.exists():
        previous = pid_file.read_text().strip()
        if previous.isdigit():
            result = subprocess.run(['ps', '-p', previous, '-o', 'command='],
                                    capture_output=True, text=True)
            if result.stdout.strip() == ' '.join(command):
                return
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    pid_file.write_text(str(process.pid))


def main():
    tailscale = shutil.which('tailscale')
    if not tailscale:
        sys.exit('Install and connect Tailscale on this Mac and your phone first.')
    if not PYTHON.exists() or not (STATE / 'browser-client/build/JourneyClient.wasm').exists():
        sys.exit('Run ./setup-macos.sh first.')
    status = json.loads(subprocess.check_output([tailscale, 'status', '--json']))
    if status.get('BackendState') != 'Running':
        sys.exit('Connect Tailscale on this Mac first.')
    hostname = status['Self']['DNSName'].rstrip('.')
    origin = f'https://{hostname}:8443'
    configuration = json.loads(subprocess.check_output([tailscale, 'serve', 'status', '--json']))
    targets = {8443: 8000, 8444: 8080, 8445: 8765}
    # These are separate from any existing HTTPS/Funnel service on port 443.
    for port, local_port in targets.items():
        host = f'{hostname}:{port}'
        existing = configuration.get('Web', {}).get(host)
        expected = {'Handlers': {'/': {'Proxy': f'http://127.0.0.1:{local_port}'}}}
        if existing and existing != expected:
            sys.exit(f'Tailscale port {port} already serves another app; its configuration was left intact.')
        if str(port) in configuration.get('TCP', {}) and not existing:
            sys.exit(f'Tailscale port {port} is already in use.')
        if configuration.get('AllowFunnel', {}).get(host):
            sys.exit(f'Port {port} is configured for public Funnel access; use a private Serve port.')
    for port, local_port in targets.items():
        subprocess.run([tailscale, 'serve', '--bg', f'--https={port}',
                        f'http://127.0.0.1:{local_port}'], check=True)
    (STATE / 'tailnet.json').write_text(json.dumps({'origin': origin}) + '\n')
    current = health()
    if current and origin not in current.get('origins', []):
        subprocess.run([str(PYTHON), str(SERVICES), 'stop'], check=True)
        deadline = time.monotonic() + 10
        while port_open(8000) and time.monotonic() < deadline:
            time.sleep(0.1)
    if not health():
        if port_open(8000):
            sys.exit('Port 8000 is in use by another app; it was left running.')
        background([str(PYTHON), '-u', str(SERVICES), 'start'], 'browser.log')
    if not port_open(8484):
        launcher = ROOT.parent / 'Cosmic/launch-macos.command'
        if not launcher.exists():
            sys.exit('Start the Cosmic server, then run this launcher again.')
        background([str(launcher)], 'mobile-server.log')
    deadline = time.monotonic() + 55
    while time.monotonic() < deadline:
        current = health()
        if current and port_open(8484):
            keep_awake(current['pid'])
            print(f'\nOpen on your phone with Tailscale connected:\n{origin}/?mobile=1')
            print('Use landscape orientation. Idle sleep is paused while the browser service runs; keep the Mac lid open.')
            return
        time.sleep(0.25)
    sys.exit('Startup is taking longer than expected; check .local/browser.log and .local/mobile-server.log.')


if __name__ == '__main__':
    main()
