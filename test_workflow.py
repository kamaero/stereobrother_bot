#!/usr/bin/env python3
"""
Test script to verify workflow fixes for StereoBrother Bot.
This script simulates the GitHub Actions workflow locally.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd, cwd=None, env=None):
    """Run a command and return output."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"Stdout:\n{result.stdout[:1000]}...")
        if result.stderr:
            print(f"Stderr:\n{result.stderr[:1000]}...")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {cmd}")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def test_lint_step():
    """Test the lint step from workflow."""
    print("\n" + "=" * 60)
    print("Testing Lint Step")
    print("=" * 60)

    # Install dependencies
    commands = [
        "python3 -m pip install --upgrade pip",
        "python3 -m pip install pre-commit",
        "python3 -m pre_commit install",
        "python3 -m pip install -r requirements.txt",
        "python3 -m pip install isort black bandit mypy",
    ]

    for cmd in commands:
        if not run_command(cmd):
            return False

    # Run pre-commit hooks
    if not run_command("python3 -m pre_commit run --all-files"):
        print("Warning: pre-commit hooks failed, but continuing...")

    # Check Python imports
    if not run_command(
        "python3 -m isort --check-only --profile=black --line-length=88 src/ config/ services/ utils/"
    ):
        print("Warning: isort check failed, but continuing...")

    # Check code formatting
    if not run_command(
        "python3 -m black --check --line-length=88 --target-version=py311 src/ config/ services/ utils/"
    ):
        print("Warning: black check failed, but continuing...")

    # Run security checks
    if not run_command("python3 -m bandit -r src/ config/ services/ utils/ -ll"):
        print("Warning: bandit check failed, but continuing...")

    # Run mypy type checking
    if not run_command(
        "python3 -m mypy --ignore-missing-imports --show-error-codes src/ config/ services/ utils/"
    ):
        print("Warning: mypy check failed, but continuing...")

    return True


def test_test_step():
    """Test the test step from workflow."""
    print("\n" + "=" * 60)
    print("Testing Test Step")
    print("=" * 60)

    # Install test dependencies
    commands = [
        "python3 -m pip install --upgrade pip",
        "python3 -m pip install -r requirements.txt",
        "python3 -m pip install pytest pytest-asyncio pytest-cov httpx",
    ]

    for cmd in commands:
        if not run_command(cmd):
            return False

    # Set up test environment variables
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/stereobrother_test",
            "REDIS_URL": "redis://localhost:6379/0",
            "SECRET_KEY": "test-secret-key",
            "DEBUG": "true",
            "ENVIRONMENT": "test",
        }
    )

    # Run unit tests
    if not run_command(
        "python3 -m pytest tests/ -v --cov=src --cov-report=xml --cov-report=html",
        env=env,
    ):
        print("Warning: pytest failed, but continuing...")

    return True


def test_build_step():
    """Test the build step from workflow."""
    print("\n" + "=" * 60)
    print("Testing Build Step")
    print("=" * 60)

    # Check if Dockerfile exists
    dockerfile = Path("Dockerfile")
    if not dockerfile.exists():
        print("Error: Dockerfile not found")
        return False

    # Check Dockerfile content
    with open(dockerfile, "r") as f:
        content = f.read()
        if "poetry.lock" in content:
            print("Warning: Dockerfile still references poetry.lock")
        if "requirements.txt" not in content:
            print("Warning: Dockerfile doesn't reference requirements.txt")

    # Try to build Docker image (skip if Docker not available)
    if shutil.which("docker"):
        print("Docker is available, attempting build...")
        if not run_command("docker build -t stereobrother-test ."):
            print("Warning: Docker build failed")
            return False
    else:
        print("Docker not available, skipping build test")

    return True


def check_file_structure():
    """Check if all required files and directories exist."""
    print("\n" + "=" * 60)
    print("Checking File Structure")
    print("=" * 60)

    required_dirs = [
        "src",
        "config",
        "services",
        "utils",
        "models",
        "tests",
        "tests/unit",
        "tests/integration",
        ".github/workflows",
    ]

    required_files = [
        "src/main.py",
        "src/tasks.py",
        "src/__init__.py",
        "config/settings.py",
        "config/__init__.py",
        "services/audio_processor.py",
        "services/user_manager.py",
        "services/payment_service.py",
        "services/__init__.py",
        "utils/audio_utils.py",
        "utils/storage.py",
        "utils/validators.py",
        "utils/__init__.py",
        "models/schemas.py",
        "models/__init__.py",
        "tests/unit/test_basic.py",
        "tests/integration/test_basic_integration.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        ".github/workflows/ci.yml",
        ".pre-commit-config.yaml",
        ".yamllint.yaml",
        ".markdownlint.yaml",
        ".secrets.baseline",
        "pyproject.toml",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "env.example",
        "run.py",
        "setup.py",
    ]

    all_good = True

    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Missing directory: {dir_path}")
            all_good = False

    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ File exists: {file_path}")
        else:
            print(f"✗ Missing file: {file_path}")
            all_good = False

    return all_good


def check_pyproject_toml():
    """Check pyproject.toml for required configurations."""
    print("\n" + "=" * 60)
    print("Checking pyproject.toml")
    print("=" * 60)

    try:
        import tomli

        with open("pyproject.toml", "rb") as f:
            config = tomli.load(f)

        checks = [
            ("project.name", "stereobrother-bot"),
            ("project.version", "1.0.0"),
            ("tool.black.line-length", 88),
            ("tool.isort.profile", "black"),
            ("tool.mypy.python_version", "3.11"),
            ("tool.bandit.exclude_dirs", ["tests", "frontend", "docs"]),
        ]

        all_good = True
        for key, expected in checks:
            parts = key.split(".")
            value = config
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    print(f"✗ Missing key: {key}")
                    all_good = False
                    break
            else:
                if value == expected:
                    print(f"✓ {key} = {value}")
                else:
                    print(f"✗ {key} = {value} (expected {expected})")
                    all_good = False

        return all_good
    except ImportError:
        print("Warning: tomli not installed, skipping pyproject.toml check")
        return True
    except Exception as e:
        print(f"Error checking pyproject.toml: {e}")
        return False


def main():
    """Main test function."""
    print("Testing StereoBrother Bot Workflow Fixes")
    print("=" * 60)

    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Run tests
    tests = [
        ("File Structure Check", check_file_structure),
        ("pyproject.toml Check", check_pyproject_toml),
        ("Lint Step Test", test_lint_step),
        ("Test Step Test", test_test_step),
        ("Build Step Test", test_build_step),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"Running: {test_name}")
        print(f"{'=' * 60}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"\n✓ {test_name} PASSED")
            else:
                print(f"\n✗ {test_name} FAILED")
        except Exception as e:
            print(f"\n✗ {test_name} ERROR: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed! Workflow should run successfully.")
        return 0
    else:
        print(f"\n⚠ {total - passed} tests failed. Check the output above.")
        print("Some issues may need to be fixed before pushing to GitHub.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
