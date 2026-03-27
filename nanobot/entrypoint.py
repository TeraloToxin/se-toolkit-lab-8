#!/usr/bin/env python3
"""Resolve environment variables into nanobot config at runtime."""
import json
import os

def resolve_config():
    # Read the base config.json
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Resolve LLM provider settings from environment
    llm_api_key = os.environ.get("LLM_API_KEY", "")
    llm_api_base_url = os.environ.get("LLM_API_BASE_URL", "")
    llm_api_model = os.environ.get("LLM_API_MODEL", "coder-model")
    
    # Set up providers section
    if "providers" not in config:
        config["providers"] = {}
    config["providers"]["custom"] = {
        "apiKey": llm_api_key,
        "apiBase": llm_api_base_url
    }
    
    # Set up agents defaults
    if "agents" not in config:
        config["agents"] = {}
    if "defaults" not in config["agents"]:
        config["agents"]["defaults"] = {}
    config["agents"]["defaults"]["model"] = llm_api_model
    
    # Set up gateway (only port)
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT", "18790")
    if "gateway" not in config:
        config["gateway"] = {}
    config["gateway"]["port"] = int(gateway_port)
    
    # Set up channels with webchat
    if "channels" not in config:
        config["channels"] = {}
    
    access_key = os.environ.get("NANOBOT_ACCESS_KEY", "")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT", "8765")
    
    config["channels"]["webchat"] = {
        "enabled": True,
        "allow_from": ["*"],
        "port": int(webchat_port),
        "access_key": access_key
    }
    
    # Resolve MCP server environment variables
    # Preserve existing MCP servers and only update lms with env vars
    mcp_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL", "http://backend:8000")
    mcp_api_key = os.environ.get("NANOBOT_LMS_API_KEY", "")
    
    if "tools" not in config:
        config["tools"] = {}
    if "mcpServers" not in config["tools"]:
        config["tools"]["mcpServers"] = {}
    
    # Update lms server with container URLs (preserve other servers like observability)
    existing_servers = config["tools"]["mcpServers"]
    existing_servers["lms"] = {
        "command": "python",
        "args": [
            "-m",
            "mcp_lms",
            mcp_backend_url
        ],
        "env": {
            "NANOBOT_LMS_API_KEY": mcp_api_key
        }
    }
    config["tools"]["mcpServers"] = existing_servers
    
    # Write resolved config
    resolved_path = os.path.join(os.path.dirname(__file__), "config.resolved.json")
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)
    
    return resolved_path

if __name__ == "__main__":
    resolved_config = resolve_config()
    workspace = os.path.join(os.path.dirname(__file__), "workspace")
    
    # Launch nanobot gateway using python -m
    import subprocess
    subprocess.run([
        "python", "-m", "nanobot", 
        "gateway", 
        "--config", resolved_config, 
        "--workspace", workspace
    ])
