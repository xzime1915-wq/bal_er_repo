import asyncio
import json
from typing import Any, Callable, Awaitable

from agent.tools import pc_tools, web_tools
from agent import memory

ToolFn = Callable[..., Awaitable[str] | str]


async def _wrap(fn: Callable[..., Any], **kwargs: Any) -> str:
    result = fn(**kwargs)
    if asyncio.iscoroutine(result):
        return await result
    return str(result)


TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "open_app",
        "description": "Open a Windows application (chrome, notepad, vscode, etc.)",
        "parameters": {"name": "string — app name"},
    },
    {
        "name": "close_app",
        "description": "Close/kill an application by name",
        "parameters": {"name": "string"},
    },
    {
        "name": "run_command",
        "description": "Run a PowerShell command on the PC",
        "parameters": {"command": "string"},
    },
    {
        "name": "set_volume",
        "description": "Set system volume 0-100",
        "parameters": {"level": "integer 0-100"},
    },
    {
        "name": "screenshot",
        "description": "Take a screenshot, returns file path",
        "parameters": {"save_dir": "optional string path"},
    },
    {
        "name": "list_dir",
        "description": "List files in a directory",
        "parameters": {"path": "string"},
    },
    {
        "name": "create_folder",
        "description": "Create a folder",
        "parameters": {"path": "string"},
    },
    {
        "name": "move_file",
        "description": "Move file or folder",
        "parameters": {"src": "string", "dest": "string"},
    },
    {
        "name": "search_files",
        "description": "Search files by glob under a root path",
        "parameters": {"root": "string", "pattern": "string e.g. *.pdf"},
    },
    {
        "name": "web_search",
        "description": "Search the web",
        "parameters": {"query": "string"},
    },
    {
        "name": "print_news",
        "description": "Fetch today headlines for the dashboard",
        "parameters": {},
    },
    {
        "name": "query_memory",
        "description": "Read a stored memory key",
        "parameters": {"key": "string"},
    },
    {
        "name": "save_memory",
        "description": "Save user preference or fact",
        "parameters": {"key": "string", "value": "string"},
    },
    {
        "name": "query_user_profile",
        "description": "Get user profile summary",
        "parameters": {},
    },
    {
        "name": "add_note",
        "description": "Save a note",
        "parameters": {"title": "string", "body": "string"},
    },
    {
        "name": "parent_delegate_task",
        "description": "Spawn a background sub-agent for a long task (browse, research)",
        "parameters": {"task": "string", "label": "optional short label"},
    },
    {
        "name": "generate_diagram",
        "description": "Generate a Mermaid flowchart for Visual Hub",
        "parameters": {"mermaid": "string — valid mermaid syntax"},
    },
]


async def execute_tool(name: str, args: dict) -> str:
    if name == "open_app":
        return await _wrap(pc_tools.open_application, name=args.get("name", ""))
    if name == "close_app":
        return await _wrap(pc_tools.close_application, name=args.get("name", ""))
    if name == "run_command":
        return await _wrap(pc_tools.run_shell_command, command=args.get("command", ""))
    if name == "set_volume":
        return await _wrap(pc_tools.set_volume, level=int(args.get("level", 50)))
    if name == "screenshot":
        return await _wrap(pc_tools.take_screenshot, save_dir=args.get("save_dir"))
    if name == "list_dir":
        return await _wrap(pc_tools.list_directory, path=args.get("path", "."))
    if name == "create_folder":
        return await _wrap(pc_tools.create_folder, path=args.get("path", ""))
    if name == "move_file":
        return await _wrap(pc_tools.move_path, src=args.get("src", ""), dest=args.get("dest", ""))
    if name == "search_files":
        return await _wrap(
            pc_tools.search_files,
            root=args.get("root", str(__import__("pathlib").Path.home())),
            pattern=args.get("pattern", "*"),
        )
    if name == "web_search":
        return await web_tools.web_search(args.get("query", ""))
    if name == "print_news":
        headlines = await web_tools.fetch_headlines()
        return json.dumps(headlines, ensure_ascii=False)
    if name == "query_memory":
        return memory.memory_get(args.get("key", "")) or "(empty)"
    if name == "save_memory":
        return memory.memory_set(args.get("key", ""), args.get("value", ""))
    if name == "query_user_profile":
        return memory.profile_summary()
    if name == "add_note":
        nid = memory.note_add(args.get("title", ""), args.get("body", ""))
        return f"Note saved id={nid}"
    if name == "generate_diagram":
        return json.dumps({"mermaid": args.get("mermaid", "flowchart LR\n  A[SENZ] --> B[Task]")})
    if name == "parent_delegate_task":
        from agent.sub_agents import delegate_task

        return await delegate_task(args.get("task", ""), args.get("label", "Sub-agent"))
    return f"Unknown tool: {name}"


def tools_prompt_block() -> str:
    lines = ["Available tools (respond with JSON tool calls when needed):"]
    for t in TOOL_DEFINITIONS:
        lines.append(f"- {t['name']}: {t['description']} | params: {t['parameters']}")
    return "\n".join(lines)
