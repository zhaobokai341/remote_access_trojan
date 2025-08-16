__author__ = "赵博凯"
__license__ = "GPL v3.0"

import asyncio
import websockets
import ssl

HOST = '0.0.0.0' # your ip
PORT = 1234 # your port
SSL_CERTFILE = 'cert.pem' # your ssl cert file
SSL_KEYFILE = 'key.pem' # your ssl key file

async def handler(websocket):
    try:
        print(f"连接成功，ID：{websocket.id}，IP：{websocket.remote_address}")
        while True:
            command = await asyncio.to_thread(input, f"{websocket.id}> ")
            if command == "exit":
                await websocket.send("exit")
                print("关闭连接...")
                break
            await websocket.send(command)
            recv = await websocket.recv()
            if recv.startswith("ERROR:"):
                print(f"命令执行失败: {recv[5:]}")
            else:
                print(recv)
    except websockets.exceptions.ConnectionClosedOK:
        print("客户端已正常关闭连接。")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"连接因错误中断: {e}")
    except Exception as e:
        print(f"发生未知错误：{e}")

async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(SSL_CERTFILE, SSL_KEYFILE)
    async with websockets.serve(handler, HOST, PORT, ssl=ssl_context):
        print(f"服务器已启动，监听端口：{PORT}")
        await asyncio.Future()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("服务器已关闭。")
