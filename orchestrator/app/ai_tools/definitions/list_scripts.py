from app.ai_tools import AITool, ai_tool
import os
from typing import Dict, Any

@ai_tool
class ListScriptsTool(AITool):
    @property
    def name(self) -> str:
        return "list_available_scripts"

    @property
    def description(self) -> str:
        return "List all custom scripts available in the scripts directory."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {}

    async def execute(self, **kwargs) -> Dict[str, Any]:
        scripts_dir = "/app/app/ai_tools/scripts"
        if not os.path.exists(scripts_dir):
            return {"scripts": []}
        
        scripts = [f for f in os.listdir(scripts_dir) if f.endswith('.py') or f.endswith('.sh')]
        return {"scripts": scripts}
