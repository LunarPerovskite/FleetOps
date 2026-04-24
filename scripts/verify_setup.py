#!/usr/bin/env python3
"""Verify FleetOps setup

Run this to check if everything is configured correctly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def check_env(name, required=False):
    """Check if environment variable is set"""
    value = os.getenv(name)
    if value:
        print(f"  ✓ {name}: {'***' if 'KEY' in name or 'SECRET' in name else 'set'}")
        return True
    else:
        icon = "✗" if required else "○"
        print(f"  {icon} {name}: not set {'(REQUIRED)' if required else '(optional)'}")
        return not required

def check_file(path, required=False):
    """Check if file exists"""
    if os.path.exists(path):
        print(f"  ✓ {path}: exists")
        return True
    else:
        icon = "✗" if required else "○"
        print(f"  {icon} {path}: not found {'(REQUIRED)' if required else '(optional)'}")
        return not required

def check_python_module(module):
    """Check if Python module is installed"""
    try:
        __import__(module)
        print(f"  ✓ {module}: installed")
        return True
    except ImportError:
        print(f"  ✗ {module}: NOT installed")
        return False

def main():
    print("=" * 60)
    print("FleetOps Setup Verification")
    print("=" * 60)
    
    all_ok = True
    
    # Environment variables
    print("\n1. Environment Variables")
    all_ok &= check_env("SECRET_KEY", required=True)
    all_ok &= check_env("DATABASE_URL", required=True)
    all_ok &= check_env("REDIS_URL", required=False)
    
    # Optional API keys
    print("\n2. LLM Provider API Keys (optional)")
    check_env("OPENAI_API_KEY")
    check_env("ANTHROPIC_API_KEY")
    check_env("OPENROUTER_API_KEY")
    check_env("GROQ_API_KEY")
    check_env("OLLAMA_URL")
    
    # Required Python modules
    print("\n3. Python Dependencies")
    deps = ["fastapi", "uvicorn", "sqlalchemy", "httpx", "pydantic"]
    for dep in deps:
        all_ok &= check_python_module(dep)
    
    # Optional dependencies
    print("\n4. Optional Dependencies")
    check_python_module("redis")
    check_python_module("prometheus_client")
    
    # Files
    print("\n5. Project Files")
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    check_file(os.path.join(base, "docker-compose.yml"))
    check_file(os.path.join(base, "backend", "Dockerfile"))
    check_file(os.path.join(base, "backend", "alembic.ini"))
    
    # Database connection
    print("\n6. Database Connection")
    try:
        from app.core.database import sync_engine
        from sqlalchemy import text
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("  ✓ Database: connected")
    except Exception as e:
        print(f"  ✗ Database: {e}")
        all_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_ok:
        print("✓ All required checks passed!")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
    print("=" * 60)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
