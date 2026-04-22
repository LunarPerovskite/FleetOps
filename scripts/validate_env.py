#!/usr/bin/env python3
"""FleetOps Environment Validator

Check if your environment is ready to run FleetOps
"""

import sys
import os
import subprocess
import socket

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def check(name: str, condition: bool, message: str = "") -> bool:
    """Print check result"""
    if condition:
        print(f"{Colors.GREEN}✅{Colors.RESET} {name}")
        if message:
            print(f"   {Colors.BLUE}ℹ️{Colors.RESET}  {message}")
        return True
    else:
        print(f"{Colors.RED}❌{Colors.RESET} {name}")
        if message:
            print(f"   {Colors.YELLOW}⚠️{Colors.RESET}  {message}")
        return False

def run_command(cmd: str) -> tuple[bool, str]:
    """Run shell command and return success + output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def check_port(host: str, port: int) -> bool:
    """Check if port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def main():
    print(f"{Colors.BLUE}🔍 FleetOps Environment Validator{Colors.RESET}")
    print("=" * 50)
    
    all_checks = []
    
    # Python version
    python_version = sys.version_info
    python_ok = python_version >= (3, 11)
    all_checks.append(check(
        f"Python {python_version.major}.{python_version.minor}.{python_version.micro}",
        python_ok,
        "Required: Python 3.11+" if not python_ok else None
    ))
    
    # Node.js
    success, output = run_command("node --version")
    if success:
        version = output.lstrip('v')
        major = int(version.split('.')[0])
        node_ok = major >= 18
        all_checks.append(check(
            f"Node.js {version}",
            node_ok,
            "Required: Node.js 18+" if not node_ok else None
        ))
    else:
        all_checks.append(check("Node.js", False, "Not found. Install from https://nodejs.org"))
    
    # npm
    success, output = run_command("npm --version")
    all_checks.append(check(
        f"npm {output}" if success else "npm",
        success,
        "Not found" if not success else None
    ))
    
    # Docker
    success, _ = run_command("docker --version")
    all_checks.append(check("Docker", success, "Install from https://docker.com" if not success else None))
    
    # Docker Compose
    success, _ = run_command("docker-compose --version")
    if not success:
        success, _ = run_command("docker compose version")
    all_checks.append(check("Docker Compose", success, "Install docker-compose" if not success else None))
    
    # PostgreSQL
    pg_running = check_port("localhost", 5432)
    all_checks.append(check(
        "PostgreSQL (port 5432)",
        pg_running,
        "Start PostgreSQL or use Docker" if not pg_running else None
    ))
    
    # Redis
    redis_running = check_port("localhost", 6379)
    all_checks.append(check(
        "Redis (port 6379)",
        redis_running,
        "Start Redis or use Docker" if not redis_running else None
    ))
    
    # Environment file
    env_exists = os.path.exists('.env')
    all_checks.append(check(
        ".env file",
        env_exists,
        "Run: cp .env.example .env" if not env_exists else None
    ))
    
    # Backend dependencies
    req_exists = os.path.exists('backend/requirements.txt')
    all_checks.append(check("Backend requirements.txt", req_exists))
    
    # Frontend dependencies
    pkg_exists = os.path.exists('frontend/package.json')
    all_checks.append(check("Frontend package.json", pkg_exists))
    
    # Git
    success, _ = run_command("git --version")
    all_checks.append(check("Git", success))
    
    # Print summary
    print("\n" + "=" * 50)
    passed = sum(all_checks)
    total = len(all_checks)
    
    if passed == total:
        print(f"{Colors.GREEN}🎉 All checks passed! You're ready to run FleetOps.{Colors.RESET}")
        print(f"\n{Colors.BLUE}Next steps:{Colors.RESET}")
        print("   docker-compose up -d")
        print("   # or")
        print("   make dev")
    elif passed >= total - 2:
        print(f"{Colors.YELLOW}⚠️  {passed}/{total} checks passed.{Colors.RESET}")
        print(f"{Colors.YELLOW}You can still run FleetOps with Docker (it handles Postgres/Redis).{Colors.RESET}")
        print(f"\n{Colors.BLUE}Quick start:{Colors.RESET}")
        print("   docker-compose up -d")
    else:
        print(f"{Colors.RED}❌ {passed}/{total} checks passed.{Colors.RESET}")
        print(f"{Colors.RED}Please fix the issues above before running FleetOps.{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Easiest option: Use Docker{Colors.RESET}")
        print("   docker-compose up -d")
        sys.exit(1)
    
    print(f"\n{Colors.BLUE}📖 Documentation:{Colors.RESET} https://github.com/LunarPerovskite/FleetOps/blob/main/docs/GETTING_STARTED.md")

if __name__ == "__main__":
    main()
