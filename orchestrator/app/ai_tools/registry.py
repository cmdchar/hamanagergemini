from typing import Dict, List
from app.ai_tools.base import AITool
import importlib
import pkgutil
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    _tools: Dict[str, AITool] = {}

    @classmethod
    def register(cls, tool: AITool):
        logger.info(f"Registering AI Tool: {tool.name}")
        cls._tools[tool.name] = tool

    @classmethod
    def get_tool(cls, name: str) -> AITool:
        return cls._tools.get(name)

    @classmethod
    def get_all_tools(cls) -> List[AITool]:
        return list(cls._tools.values())

    @classmethod
    def load_tools(cls):
        # Import all modules in definitions
        from app.ai_tools import definitions
        package = definitions
        
        # Handle both file system path and package path
        if hasattr(package, "__path__"):
            path = package.__path__
            prefix = package.__name__ + "."
            
            for _, name, _ in pkgutil.iter_modules(path, prefix):
                try:
                    importlib.import_module(name)
                    logger.info(f"Loaded tool module: {name}")
                except Exception as e:
                    logger.error(f"Failed to load tool module {name}: {e}")

# Decorator for auto-registration
def ai_tool(cls):
    ToolRegistry.register(cls())
    return cls
