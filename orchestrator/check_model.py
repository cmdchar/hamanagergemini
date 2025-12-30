import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    from app.models.server import Server
    print("Server model imported successfully")
    print(f"Attributes: {dir(Server)}")
    
    if hasattr(Server, 'deployments'):
        print("Server has 'deployments' attribute")
        print(Server.deployments)
    else:
        print("Server does NOT have 'deployments' attribute")
        
except Exception as e:
    print(f"Error: {e}")
