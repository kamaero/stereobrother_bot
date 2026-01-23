#!/usr/bin/env python3
"""
Setup script for StereoBrother Bot project initialization.
This script helps set up the development environment and run initial checks.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version meets requirements."""
    required_version = (3, 11)
    current_version = sys.version_info[:2]

    if current_version < required_version:
        print(
            f"❌ Python {required_version[0]}.{required_version[1]} or higher is required."
        )
        print(f"   Current version: {sys.version_info[0]}.{sys.version_info[1]}")
        return False

    print(f"✓ Python {current_version[0]}.{current_version[1]} meets requirements")
    return True


def check_dependencies():
    """Check if required system dependencies are installed."""
    required_commands = ["ffmpeg", "git"]
    missing_commands = []

    for cmd in required_commands:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            print(f"✓ {cmd} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_commands.append(cmd)
            print(f"❌ {cmd} is not installed")

    if missing_commands:
        print("\nPlease install missing dependencies:")
        for cmd in missing_commands:
            if cmd == "ffmpeg":
                print("  - FFmpeg: sudo apt-get install ffmpeg (Ubuntu/Debian)")
                print("            brew install ffmpeg (macOS)")
                print("            Download from https://ffmpeg.org/ (Windows)")
            elif cmd == "git":
                print("  - Git: https://git-scm.com/downloads")
        return False

    return True


def create_virtualenv():
    """Create a Python virtual environment."""
    venv_path = Path(".venv")

    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return True

    print("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print("✓ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False


def install_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")

    # Check if we're in a virtual environment
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    pip_cmd = [sys.executable, "-m", "pip"]

    try:
        # Upgrade pip
        subprocess.run([*pip_cmd, "install", "--upgrade", "pip"], check=True)

        # Install requirements
        requirements_file = Path("requirements.txt")
        if requirements_file.exists():
            subprocess.run([*pip_cmd, "install", "-r", "requirements.txt"], check=True)
            print("✓ Dependencies installed from requirements.txt")
        else:
            print("⚠ requirements.txt not found, skipping dependency installation")

        # Install development dependencies
        try:
            subprocess.run(
                [
                    *pip_cmd,
                    "install",
                    "pytest",
                    "pytest-asyncio",
                    "pytest-cov",
                    "black",
                    "isort",
                    "flake8",
                    "mypy",
                    "pre-commit",
                ],
                check=True,
            )
            print("✓ Development dependencies installed")
        except subprocess.CalledProcessError:
            print("⚠ Could not install all development dependencies")

        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_pre_commit():
    """Set up pre-commit hooks."""
    print("Setting up pre-commit hooks...")

    try:
        # Install pre-commit hooks
        subprocess.run([sys.executable, "-m", "pre_commit", "install"], check=True)
        print("✓ Pre-commit hooks installed")

        # Run pre-commit on all files
        subprocess.run(
            [sys.executable, "-m", "pre_commit", "run", "--all-files"], check=False
        )
        print("✓ Pre-commit checks completed")

        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"⚠ Could not set up pre-commit hooks: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    directories = [
        "storage",
        "temp",
        "logs",
        "models",
        "tests/unit",
        "tests/integration",
        "config",
        "services",
        "utils",
    ]

    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")

    # Create __init__.py files
    init_files = [
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "config/__init__.py",
        "services/__init__.py",
        "utils/__init__.py",
    ]

    for init_file in init_files:
        path = Path(init_file)
        if not path.exists():
            path.write_text('"""Package initialization."""\n')
            print(f"✓ Created file: {init_file}")


def create_env_file():
    """Create .env file from example."""
    env_example = Path("env.example")
    env_file = Path(".env")

    if not env_example.exists():
        print("⚠ env.example not found, creating basic .env file")
        env_content = """# Environment configuration for StereoBrother Bot
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/stereobrother_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Storage
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./storage

# Security
SECRET_KEY=your-secret-key-change-in-production

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Application
HOST=0.0.0.0
PORT=8000
WORKERS=4
APP_VERSION=1.0.0

# AI Models
AI_MODELS_PATH=./models
MAX_AUDIO_SIZE_MB=100
SUPPORTED_FORMATS=mp3,wav,flac,ogg,m4a,aac

# Temporary files
TEMP_DIR=./temp
TEMP_FILE_RETENTION_HOURS=24
"""
    else:
        env_content = env_example.read_text()

    if not env_file.exists():
        env_file.write_text(env_content)
        print("✓ Created .env file from template")
        print("  ⚠ Please update the .env file with your actual configuration")
    else:
        print("✓ .env file already exists")


def run_tests():
    """Run basic tests to verify setup."""
    print("Running basic tests...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✓ All tests passed")
        else:
            print("⚠ Some tests failed")
            print(result.stdout)

        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"⚠ Could not run tests: {e}")
        return False


def display_next_steps():
    """Display next steps for the user."""
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review and update the .env file with your configuration")
    print("2. Start the database and Redis:")
    print("   docker-compose up -d db redis")
    print("3. Run the application:")
    print("   python run.py server")
    print("4. Or run with Docker Compose:")
    print("   docker-compose up -d")
    print("\nDevelopment commands:")
    print("  • Run tests: python -m pytest")
    print("  • Format code: python -m black .")
    print("  • Lint code: python -m flake8")
    print("  • Type check: python -m mypy .")
    print("\nAccess the application:")
    print("  • API: http://localhost:8000")
    print("  • Docs: http://localhost:8000/docs")
    print("  • Health: http://localhost:8000/health")
    print("\nFor more information, see README.md")


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup StereoBrother Bot project")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument(
        "--skip-pre-commit", action="store_true", help="Skip pre-commit setup"
    )
    parser.add_argument(
        "--skip-venv", action="store_true", help="Skip virtual environment creation"
    )
    args = parser.parse_args()

    print("Setting up StereoBrother Bot project...")
    print("=" * 60)

    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Run setup steps
    steps = [
        ("Checking Python version", check_python_version),
        ("Checking system dependencies", check_dependencies),
    ]

    if not args.skip_venv:
        steps.append(("Creating virtual environment", create_virtualenv))

    steps.extend(
        [
            ("Installing dependencies", install_dependencies),
            ("Creating directories", create_directories),
            ("Creating environment file", create_env_file),
        ]
    )

    if not args.skip_pre_commit:
        steps.append(("Setting up pre-commit", setup_pre_commit))

    if not args.skip_tests:
        steps.append(("Running tests", run_tests))

    # Execute all steps
    all_success = True
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            all_success = False
            print(f"⚠ {step_name} had issues")

    if all_success:
        display_next_steps()
        return 0
    else:
        print("\n" + "=" * 60)
        print("SETUP COMPLETED WITH ISSUES")
        print("=" * 60)
        print("\nSome setup steps had issues. Please check the output above.")
        print("You may need to manually complete some steps.")
        display_next_steps()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
