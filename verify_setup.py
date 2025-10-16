#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open Educational Resourcer - Setup Verification Script
Checks that all necessary files and configurations are in place
"""

import os
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Check marks (cross-platform)
CHECK = '[OK]' if sys.platform == 'win32' else '✓'
CROSS = '[X]' if sys.platform == 'win32' else '✗'

def check_file(filepath, required=True):
    """Check if a file exists"""
    exists = Path(filepath).exists()
    status = f"{GREEN}{CHECK}{RESET}" if exists else f"{RED}{CROSS}{RESET}"
    req_text = "(required)" if required else "(optional)"
    
    if exists:
        print(f"{status} {filepath} {GREEN}{req_text}{RESET}")
        return True
    else:
        color = RED if required else YELLOW
        print(f"{status} {filepath} {color}{req_text}{RESET}")
        return not required

def check_directory(dirpath, required=True):
    """Check if a directory exists"""
    exists = Path(dirpath).exists() and Path(dirpath).is_dir()
    status = f"{GREEN}{CHECK}{RESET}" if exists else f"{RED}{CROSS}{RESET}"
    req_text = "(required)" if required else "(optional)"
    
    if exists:
        print(f"{status} {dirpath}/ {GREEN}{req_text}{RESET}")
        return True
    else:
        color = RED if required else YELLOW
        print(f"{status} {dirpath}/ {color}{req_text}{RESET}")
        return not required

def check_env_file():
    """Check .env file and its contents"""
    print(f"\n{BOLD}Checking Environment Configuration:{RESET}")
    
    if not Path('.env').exists():
        print(f"{RED}{CROSS} .env file not found{RESET}")
        print(f"{YELLOW}  Run: cp .env.example .env{RESET}")
        return False
    
    print(f"{GREEN}{CHECK} .env file exists{RESET}")
    
    # Check for critical variables
    required_vars = [
        'DJANGO_SECRET_KEY',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'DB_HOST'
    ]
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in env_content:
            missing_vars.append(var)
            print(f"{RED}{CROSS} {var} not found in .env{RESET}")
        else:
            print(f"{GREEN}{CHECK} {var} found in .env{RESET}")
    
    if missing_vars:
        print(f"{YELLOW}  Missing variables: {', '.join(missing_vars)}{RESET}")
        return False
    
    return True

def main():
    """Main verification function"""
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Open Educational Resourcer - Setup Verification{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")
    
    all_good = True
    
    # Check root files
    print(f"{BOLD}Checking Root Files:{RESET}")
    all_good &= check_file('docker-compose.yml')
    all_good &= check_file('Dockerfile')
    all_good &= check_file('requirements.txt')
    all_good &= check_file('manage.py')
    all_good &= check_file('.env.example')
    all_good &= check_file('.gitignore')
    all_good &= check_file('README.md')
    
    # Check documentation files
    print(f"\n{BOLD}Checking Documentation:{RESET}")
    check_file('QUICKSTART.md', required=False)
    check_file('PROJECT_STRUCTURE.md', required=False)
    check_file('PROJECT_SUMMARY.md', required=False)
    check_file('DEPLOYMENT_CHECKLIST.md', required=False)
    
    # Check Django project structure
    print(f"\n{BOLD}Checking Django Project Structure:{RESET}")
    
    # Check if old name exists and warn
    if Path('oer_prototype').exists():
        print(f"{YELLOW}⚠ Found 'oer_prototype' folder - should be renamed to 'oer_rebirth'{RESET}")
        print(f"{YELLOW}  See RENAME_INSTRUCTIONS.md for details{RESET}")
    
    # Check for correct name
    if check_directory('oer_rebirth'):
        all_good &= check_file('oer_rebirth/__init__.py')
        all_good &= check_file('oer_rebirth/settings.py')
        all_good &= check_file('oer_rebirth/urls.py')
        all_good &= check_file('oer_rebirth/celery.py')
        all_good &= check_file('oer_rebirth/wsgi.py')
        all_good &= check_file('oer_rebirth/asgi.py')
    elif check_directory('oer_prototype', required=False):
        # Fallback to old name for backwards compatibility
        print(f"{YELLOW}  Using legacy 'oer_prototype' folder name{RESET}")
        all_good &= check_file('oer_prototype/__init__.py')
        all_good &= check_file('oer_prototype/settings.py')
        all_good &= check_file('oer_prototype/urls.py')
        all_good &= check_file('oer_prototype/celery.py')
        all_good &= check_file('oer_prototype/wsgi.py')
        all_good &= check_file('oer_prototype/asgi.py')
    else:
        print(f"{RED}{CROSS} Django project folder not found (neither oer_rebirth nor oer_prototype){RESET}")
        all_good = False
    
    # Check resources app
    print(f"\n{BOLD}Checking Resources App:{RESET}")
    all_good &= check_directory('resources')
    all_good &= check_file('resources/__init__.py')
    all_good &= check_file('resources/models.py')
    all_good &= check_file('resources/views.py')
    all_good &= check_file('resources/urls.py')
    all_good &= check_file('resources/admin.py')
    all_good &= check_file('resources/forms.py')
    all_good &= check_file('resources/apps.py')
    all_good &= check_file('resources/tasks.py')
    all_good &= check_file('resources/ai_processing.py')
    
    # Check services
    print(f"\n{BOLD}Checking Services:{RESET}")
    all_good &= check_directory('resources/services')
    all_good &= check_file('resources/services/__init__.py')
    all_good &= check_file('resources/services/ai_utils.py')
    all_good &= check_file('resources/services/oer_api.py')
    all_good &= check_file('resources/services/talis.py')
    
    # Check management commands
    print(f"\n{BOLD}Checking Management Commands:{RESET}")
    all_good &= check_directory('resources/management')
    all_good &= check_directory('resources/management/commands')
    all_good &= check_file('resources/management/__init__.py')
    all_good &= check_file('resources/management/commands/__init__.py')
    all_good &= check_file('resources/management/commands/fetch_oer.py')
    all_good &= check_file('resources/management/commands/export_talis.py')
    
    # Check templates
    print(f"\n{BOLD}Checking Templates:{RESET}")
    all_good &= check_directory('templates')
    all_good &= check_file('templates/base.html')
    all_good &= check_directory('templates/resources')
    all_good &= check_file('templates/resources/search.html')
    all_good &= check_file('templates/resources/taliscsv_upload.html')
    all_good &= check_file('templates/resources/compare.html')
    all_good &= check_file('templates/resources/talis_preview.html')
    all_good &= check_file('templates/resources/export.html')
    all_good &= check_file('templates/resources/export_success.html')
    
    # Check admin templates
    print(f"\n{BOLD}Checking Admin Templates:{RESET}")
    all_good &= check_directory('templates/admin/resources')
    all_good &= check_file('templates/admin/resources/csv_upload.html')
    all_good &= check_file('templates/admin/resources/oerresource_changelist.html')
    
    # Check static directory
    print(f"\n{BOLD}Checking Static Files:{RESET}")
    all_good &= check_directory('static')
    
    # Check Docker files
    print(f"\n{BOLD}Checking Docker Configuration:{RESET}")
    all_good &= check_directory('docker-entrypoint-initdb.d')
    all_good &= check_file('docker-entrypoint-initdb.d/init-vector.sql')
    all_good &= check_file('docker-entrypoint.sh')
    
    # Check environment configuration
    env_ok = check_env_file()
    all_good &= env_ok
    
    # Summary
    print(f"\n{BOLD}{'='*60}{RESET}")
    if all_good:
        print(f"{GREEN}{BOLD}{CHECK} All required files are present!{RESET}")
        print(f"\n{BOLD}Next steps:{RESET}")
        print("1. Review and update .env file")
        print("2. Run: docker-compose up --build")
        print("3. Access http://localhost:8000")
    else:
        print(f"{RED}{BOLD}{CROSS} Some required files are missing!{RESET}")
        print(f"{YELLOW}Please ensure all required files are in place before proceeding.{RESET}")
        sys.exit(1)
    print(f"{BOLD}{'='*60}{RESET}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Verification interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error during verification: {str(e)}{RESET}")
        sys.exit(1)
