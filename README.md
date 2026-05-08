# MCP GDB Server

基于 [FastMCP](https://github.com/anthropics/fastmcp) 的 Model Context Protocol (MCP) 服务器，用于通过 MCP 协议远程控制 GDB 调试会话。

主要用于 **CTF Pwn** 挑战的 AI 辅助调试，配合 Claude 等 AI Agent 实现自动化的二进制漏洞分析。

## 功能

- **启动调试会话** — 支持本地调试、附加进程 (gdb -p)、远程调试 (target remote)
- **发送 GDB 命令** — 交互式执行任意 GDB 命令（break, step, print 等）
- **中断运行** — 向正在运行的程序发送 SIGINT/Ctrl+C

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 开发模式启动（单文件入口，推荐）
python mcp_gdb_server.py

# 指定端口
python mcp_gdb_server.py 9000

# 或通过环境变量指定地址
MCP_HOST=127.0.0.1 MCP_PORT=9000 python mcp_gdb_server.py
```

服务器默认在 `http://0.0.0.0:8000` 监听 SSE 传输。

> 也可以通过包模式启动（效果相同）：`python -m mcp_gdb_server`

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
  "command": "python",
  "args": ["mcp_gdb_server.py", "--transport", "stdio"]
}
```

> **提示**：Claude Code 可将方式二配置在项目 `.claude/settings.json` 中（仅本项目生效），方式一配置在全局设置（其余项目生效），两者共存互不干扰。

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

### 生命周期

| 工具 | 描述 |
|------|------|
| `start_debugging` | 启动 GDB 调试会话 |
| `send_gdb_command` | 向 GDB 发送原始命令或向程序输入 |
| `interrupt` | 中断正在运行的程序 |
| `stop_debugging` | 终止 GDB 会话 |

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
1. start_debugging(command="gdb ./challenge")
2. set_breakpoint(location="main")
3. send_gdb_command(command="run")
4. send_gdb_command(command="r < input.txt")
5. read_registers()                    # 结构化寄存器字典
6. read_memory(address="$rsp", count=32)  # 结构化内存
7. backtrace()                         # 结构化调用栈
8. disassemble(address="$rip")         # 结构化反汇编
9. evaluate(expression="'A'*8")        # 结构化表达式求值
10. set_watchpoint(expression="rbp-8", kind="write")
```

## 项目结构

```
mcp-gdb-server/
├── mcp_gdb_server.py          # 单文件 CLI 入口（推荐）
├── mcp_gdb_server/            # Python 包
│   ├── __init__.py            # FastMCP 应用创建与组件装配
│   ├── manager.py             # GDBManager — GDB 进程管理
│   ├── tools.py               # MCP 工具注册
│   └── __main__.py            # 入口点 (python -m mcp_gdb_server)
├── run.py                     # PyInstaller 编译入口
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
