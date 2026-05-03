# MCP GDB Server

基于 [FastMCP](https://github.com/anthropics/fastmcp) 的 Model Context Protocol (MCP) 服务器，用于通过 MCP 协议远程控制 GDB 调试会话。

主要用于 **CTF Pwn** 挑战的 AI 辅助调试，配合 Claude 等 AI Agent 实现自动化的二进制漏洞分析。

## 功能

- **启动调试会话** — 支持本地调试、附加进程 (gdb -p)、远程调试 (target remote)
- **发送 GDB 命令** — 交互式执行任意 GDB 命令（break, step, print 等）
- **中断运行** — 向正在运行的程序发送 SIGINT/Ctrl+C
- **Shell 命令** — 在宿主机上执行系统命令辅助调试

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 开发模式启动
python -m mcp_gdb_server

# 或通过环境变量指定地址
MCP_HOST=127.0.0.1 MCP_PORT=9000 python -m mcp_gdb_server
```

服务器默认在 `http://0.0.0.0:8000` 监听 SSE 传输。

## 编译为独立可执行文件

编译后生成单个二进制文件，不依赖 Python 环境，可直接 `./mcp_gdb_server` 启动。

### 前置要求

```bash
pip install pyinstaller
```

### 编译

```bash
# 生产编译（单文件、strip）
python build.py

# Debug 编译（目录模式，保留调试信息）
python build.py --debug

# 清理缓存后编译
python build.py --clean
```

编译产物为 `dist/mcp_gdb_server`。

```bash
# 启动编译后的服务
./dist/mcp_gdb_server

# 可复制到任意位置独立运行
cp dist/mcp_gdb_server /usr/local/bin/
./mcp_gdb_server
```

## 安装为系统服务

```bash
# 一键编译 + 安装服务
chmod +x install_service.sh
sudo ./install_service.sh

# 或手动操作
sudo cp dist/mcp_gdb_server /usr/local/bin/
sudo cp mcp-gdb-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mcp-gdb-server.service

# 管理服务
systemctl status mcp-gdb-server.service
systemctl restart mcp-gdb-server.service
sudo journalctl -u mcp-gdb-server.service -f

# 卸载
sudo ./uninstall_service.sh
```

## MCP 工具

| 工具 | 描述 |
|------|------|
| `start_debugging` | 启动 GDB 调试会话 |
| `send_gdb_command` | 向 GDB 发送命令或向程序输入 |
| `interrupt` | 中断正在运行的程序 |
| `stop_debugging` | 终止 GDB 会话 |
| `run_shell_command` | 执行宿主机 Shell 命令 |

## 典型用法

```
1. start_debugging(command="gdb ./challenge")
2. send_gdb_command(command="break main")
3. send_gdb_command(command="run")
4. send_gdb_command(command="info registers")
5. send_gdb_command(command="x/32gx $rsp")
```

## 项目结构

```
mcp-gdb-server/
├── mcp_gdb_server/          # Python 包
│   ├── __init__.py          # FastMCP 应用创建与组件装配
│   ├── manager.py           # GDBManager — GDB 进程管理
│   ├── tools.py             # MCP 工具注册
│   └── __main__.py          # 入口点 (python -m mcp_gdb_server)
├── run.py                   # PyInstaller 编译入口
├── build.py                 # PyInstaller 编译脚本
├── mcp-gdb-server.service   # systemd 服务单元
├── install_service.sh       # 服务一键安装
├── uninstall_service.sh     # 服务一键卸载
├── requirements.txt
└── README.md
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MCP_HOST` | `0.0.0.0` | 监听地址 |
| `MCP_PORT` | `8000` | 监听端口 |

## 依赖

- Python 3.8+
- fastmcp
- pexpect
- PyInstaller（仅编译时需要）
