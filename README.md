# remote_access_trojan

语言：[中文](README.md) [English](README_en.md)

这个仓库用于生成木马病毒，目前暂未做好

注：用户使用该软件造成的任何损失和赔偿，全由用户承担

## 特点：
- 木马病毒可打包成exe,elf,apk,app可执行文件 ❌
- 木马病毒支持中文和英文 ✅
- 木马病毒基于wss(websocket+ssl)协议，原计划基于tcp协议 ✅
- 木马病毒可以通过命令行，网页，图形化这些方式控制目标主机 ❌
- 木马病毒可以同时控制多台设备 ✅
- 木马病毒可以对目标主机输入命令，获取系统信息，上传/下载文件，截图，录音，实时观看对方屏幕，截取键盘输入等操作 ❌

## 准备环境：
- [Python 3.10+](https://www.python.org/downloads/)
- websockets, rich第三方库。
  ```bash
  pip3 install websockets rich
  ```
- 要有证书，分别是key.pem和cert.pem两个文件。如果你对安全性没那么重视且想简单的生成证书，可以考虑自签名证书
```bash
openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -out cert.pem -days 99999 -subj "/CN=localhost"
```

## 如何使用：
### 下载
方法1：克隆这个仓库并进入该目录
```bash
git clone https://github.com/zhaobokai341/remote_access_trojan.git
cd remote_access_trojan
```
方法2：直接通过浏览器下载然后解压
方法3：进入[Releases](https://github.com/zhaobokai341/remote_access_trojan/releases),选择合适的版本，下载名为code.zip的文件

2.运行

进入code目录，有两个文件，分别是zh和en,zh是中文版本，en是英文版本，根据语言偏好选择合适的文件夹即可，这里以zh为例
进入zh文件夹，输入
```bash
python server.py
```
这个命令可启动服务端，用于控制受害者机器，不出意外，会遇到类似的输出
```
[01:44:49] 版权所有：Copyright © 赵博凯, All Rights Reserved.                                                                                                    server.py:65
[01:44:49] [*] 正在启动程序...                                                                                                                                   server.py:43
[01:44:49] [*] 正在配置证书文件, 证书位置: ../cert.pem, 密钥位置: ../key.pem                                                                                     server.py:43
[01:44:49] [*] 正在启动服务器, 监听地址: 0.0.0.0, 端口: 8765                                                                                                     server.py:43
(server)> 
```
这代表就成功了
