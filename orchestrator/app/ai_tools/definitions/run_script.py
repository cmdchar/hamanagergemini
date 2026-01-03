from app.ai_tools import AITool, ai_tool
import asyncio
import os
from typing import Dict, Any

@ai_tool
class RunScriptTool(AITool):
    @property
    def name(self) -> str:
        return "run_custom_script"

    @property
    def description(self) -> str:
        return "Run a custom script from the scripts directory. Returns stdout/stderr."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "script_name": {
                    "type": "string",
                    "description": "Name of the script file (e.g., check_disk.py)"
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of arguments"
                }
            },
            "required": ["script_name"]
        }

    async def execute(self, script_name: str, args: list = None, **kwargs) -> Dict[str, Any]:
        scripts_dir = "/app/app/ai_tools/scripts"
        script_path = os.path.join(scripts_dir, script_name)
        
        if not os.path.exists(script_path):
            return {"error": f"Script {script_name} not found"}
        
        # Ensure script is within scripts dir (security)
        # Note: In container /app/app/ai_tools/scripts is the path
        if not os.path.abspath(script_path).startswith(os.path.abspath(scripts_dir)):
            return {"error": "Access denied"}

        args = args or []
        
        if script_name.endswith(".py"):
            cmd = ["python3", script_path] + args
        elif script_name.endswith(".sh"):
            cmd = ["bash", script_path] + args
        else:
            return {"error": "Unsupported script type"}

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode()
            }
        except Exception as e:
            return {"error": str(e)}
