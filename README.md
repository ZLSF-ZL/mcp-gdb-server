# MCP GDB Server

基于 [FastMCP](https://github.com/anthropics/fastmcp) 的 Model Context Protocol (MCP) 服务器，用于通过 MCP 协议远程控制 GDB 调试会话。

主要用于 **CTF Pwn** 挑战的 AI 辅助调试，配合 Claude 等 AI Agent 实现自动化的二进制漏洞分析。

## 功能

- **启动调试会话** — 支持本地调试、附加进程 (gdb -p)、远程调试 (target remote)
- **发送 GDB 命令** — 交互式执行任意 GDB 命令（break, step, print 等）
	- **GDB 自动探测** — 自动选用 gdb-multiarch 或 gdb
- **断点管理** — 设置、删除、启用、禁用断点，支持条件断点
- **执行控制** — stepi、next、finish、continue
- **寄存器与内存** — 结构化读取寄存器、内存、反汇编
- **调用栈查看** — backtrace 支持显示局部变量
- **表达式求值** — 调试中动态求值

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 开发模式启动（单文件入口，推荐）
python3 mcp_gdb_server.py

# 指定端口
python3 mcp_gdb_server.py 9000

# 或通过环境变量指定地址
MCP_HOST=127.0.0.1 MCP_PORT=9000 python3 mcp_gdb_server.py
```

服务器默认在 `http://0.0.0.0:8000` 监听 SSE 传输。

> 也可以通过包模式启动（效果相同）：`python3 -m mcp_gdb_server`

## 客户端配置

在支持 MCP 的客户端（如 VS Code、Cursor、Claude Code 等）中，根据运行方式选择对应配置。

### 方式一：连接已运行的服务（SSE）

服务已通过 systemd 或手动启动，客户端直接连接：

```json
{
  "type": "sse",
  "url": "http://127.0.0.1:8000/sse",
  "timeout": 1800,
  "disabled": false
}
```

### 方式二：从源码自动启动（Stdio）

客户端自动从项目目录启动 `mcp_gdb_server.py`：

```json
{
  "type": "stdio",
  "command": "python3",
  "args": ["mcp_gdb_server.py", "--transport", "stdio"]
}
```


## 编译为独立可执行文件

编译后生成单个二进制文件，不依赖 Python 环境，可直接 `./mcp_gdb_server` 启动。

### 前置要求

```bash
pip install pyinstaller
```

### 编译

```bash
# 生产编译（单文件、strip）
python3 build.py

# Debug 编译（目录模式，保留调试信息）
python3 build.py --debug

# 清理缓存后编译
python3 build.py --clean
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

### 生命周期

| 工具 | 描述 |
|------|------|
| `start_debugging` | 启动 GDB 调试会话，留空自动选择最佳 GDB |
| `detect_gdb` | 探测系统上可用的 GDB 二进制 |
| `send_gdb_command` | 向 GDB 发送原始命令或向程序输入 |
| `interrupt` | 中断正在运行的程序 |
| `stop_debugging` | 终止程序并退出 GDB |
| `detach_debugging` | 仅退出 GDB，远程目标程序继续运行 |

### 断点管理

| 工具 | 描述 |
|------|------|
| `set_breakpoint` | 设置断点，支持条件断点和一次性断点（tbreak） |
| `delete_breakpoint` | 按编号删除断点/监视点 |
| `list_breakpoints` | 列出所有断点、监视点、捕获点 |
| `enable_breakpoint` | 启用断点 |
| `disable_breakpoint` | 禁用断点 |

### 执行控制

| 工具 | 描述 |
|------|------|
| `step_into` | 单步进入（stepi） |
| `step_over` | 单步跳过（next） |
| `step_out` | 执行到当前函数返回（finish） |
| `continue_execution` | 继续执行 |

### 状态查看

| 工具 | 描述 |
|------|------|
| `read_registers` | 读取寄存器值，返回结构化字典 |
| `backtrace` | 打印调用栈，支持显示局部变量 |
| `evaluate` | 求值 GDB 表达式（print） |

### 内存与反汇编

| 工具 | 描述 |
|------|------|
| `read_memory` | 按指定格式读取内存（hex、decimal、string、instr） |
| `search_memory` | 在内存范围中搜索值（find） |
| `disassemble` | 反汇编指定地址附近的指令 |

### 监视点

| 工具 | 描述 |
|------|------|
| `set_watchpoint` | 设置硬件监视点（write/read/access） |

## 典型用法

```
 1. detect_gdb()                          # 查看系统上可用的 GDB
 2. start_debugging()                     # 自动选用最佳 GDB
 3. set_breakpoint(location="main")
 4. send_gdb_command(command="run")
 5. send_gdb_command(command="r < input.txt")
 6. read_registers()                      # 结构化寄存器字典
 7. read_memory(address="$rsp", count=32) # 结构化内存
 8. backtrace()                           # 结构化调用栈
 9. disassemble(address="$rip")           # 结构化反汇编
10. evaluate(expression="'A'*8")          # 结构化表达式求值
11. set_watchpoint(expression="rbp-8", kind="write")
```

## 项目结构

```
mcp-gdb-server/
├── mcp_gdb_server.py          # 单文件 CLI 入口（推荐）
├── mcp_gdb_server/            # Python 包
│   ├── __init__.py            # FastMCP 应用创建与组件装配
│   ├── manager.py             # GDBManager — GDB 进程管理
│   ├── tools.py               # MCP 工具注册
│   └── __main__.py            # 入口点 (python3 -m mcp_gdb_server)
├── mcp_gdb_server.py          # CLI 入口 / PyInstaller 编译入口
├── build.py                   # PyInstaller 编译脚本
├── mcp-gdb-server.service     # systemd 服务单元
├── install_service.sh         # 服务一键安装
├── uninstall_service.sh       # 服务一键卸载
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
