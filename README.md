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

## 如何使用

### 准备环境：
- [Python 3.10+](https://www.python.org/downloads/)
- websockets, rich第三方库。
  ```bash
  pip3 install websockets rich
  ```
