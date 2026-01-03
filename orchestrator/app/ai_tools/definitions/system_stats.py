from app.ai_tools import AITool, ai_tool
import psutil
import shutil
from typing import Dict, Any

@ai_tool
class SystemStatsTool(AITool):
    @property
    def name(self) -> str:
        return "get_system_stats"

    @property
    def description(self) -> str:
        return "Get current system statistics (CPU, Memory, Disk) of the Orchestrator container."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = shutil.disk_usage("/")
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2)
        }
