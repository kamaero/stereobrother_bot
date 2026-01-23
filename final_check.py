#!/usr/bin/env python3
"""
Final check script for StereoBrother Bot project.
This script verifies that the project is ready for GitHub push.
"""

import os
import subprocess
import sys
from pathlib import Path

import yaml


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def run_command(cmd, cwd=None):
    """Run command and return success status."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def check_file_structure():
    """Check if all required files exist."""
    print_header("Checking File Structure")

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

    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path}")
            all_exist = False

    return all_exist


def check_python_imports():
    """Check if Python imports work."""
    print_header("Checking Python Imports")

    # Create a temporary Python file to test imports
    test_file = "test_imports_temp.py"
    with open(test_file, "w") as f:
        f.write("""
import sys
sys.path.insert(0, '.')

try:
    from src.main import app
    print("OK - src.main imported")

    from config.settings import settings
    print("OK - config.settings imported")

    from services.audio_processor import AudioProcessor
    print("OK - services.audio_processor imported")

    from services.user_manager import UserManager
    print("OK - services.user_manager imported")

    from services.payment_service import PaymentService
    print("OK - services.payment_service imported")

    from utils.audio_utils import AudioUtils
    print("OK - utils.audio_utils imported")

    from utils.storage import StorageManager
    print("OK - utils.storage imported")

    from utils.validators import validate_audio_file
    print("OK - utils.validators imported")

    from models.schemas import AudioUploadRequest
    print("OK - models.schemas imported")

    from src.tasks import celery_app
    print("OK - src.tasks imported")

    print("\\nAll imports successful!")
    sys.exit(0)
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)
""")

    success, stdout, stderr = run_command(f"python3 {test_file}")

    # Clean up temporary file
    try:
        os.remove(test_file)
    except:
        pass

    if success:
        print("✅ All Python imports work correctly")
        return True
    else:
        print(f"❌ Python import check failed")
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")
        return False


def check_workflow_file():
    """Check if GitHub workflow file is valid."""
    print_header("Checking GitHub Workflow")

    try:
        with open(".github/workflows/ci.yml", "r") as f:
            workflow = yaml.safe_load(f)

        # Check required sections
        required_sections = ["name", "on", "jobs"]
        for section in required_sections:
            if section not in workflow:
                print(f"✗ Missing section: {section}")
                return False
            print(f"✓ Section present: {section}")

        # Check required jobs
        required_jobs = ["lint", "test", "build"]
        jobs = workflow.get("jobs", {})
        for job in required_jobs:
            if job not in jobs:
                print(f"✗ Missing job: {job}")
                return False
            print(f"✓ Job present: {job}")

        print("✅ Workflow file is valid")
        return True

    except yaml.YAMLError as e:
        print(f"❌ YAML parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking workflow: {e}")
        return False


def check_tests():
    """Run basic tests."""
    print_header("Running Tests")

    success, stdout, stderr = run_command("python3 -m pytest tests/ -v")

    if success:
        print("✅ All tests passed")
        # Show test summary
        lines = stdout.strip().split("\n")
        for line in lines[-10:]:  # Show last 10 lines
            print(line)
        return True
    else:
        print("❌ Tests failed")
        print(f"Stdout: {stdout[-500:] if stdout else 'No output'}")
        print(f"Stderr: {stderr[-500:] if stderr else 'No error output'}")
        return False


def check_dockerfile():
    """Check Dockerfile syntax."""
    print_header("Checking Dockerfile")

    try:
        with open("Dockerfile", "r") as f:
            content = f.read()

        # Basic checks
        checks = [
            ("FROM python:3.11-slim", "Uses Python 3.11 slim image"),
            ("COPY requirements.txt", "Copies requirements.txt"),
            ("RUN pip install", "Installs Python dependencies"),
            ("EXPOSE 8000", "Exposes port 8000"),
            ("CMD", "Has CMD instruction"),
        ]

        all_good = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✓ {description}")
            else:
                print(f"✗ Missing: {description}")
                all_good = False

        if all_good:
            print("✅ Dockerfile looks good")
            return True
        else:
            print("❌ Dockerfile has issues")
            return False

    except Exception as e:
        print(f"❌ Error checking Dockerfile: {e}")
        return False


def check_requirements():
    """Check requirements.txt."""
    print_header("Checking Requirements")

    try:
        with open("requirements.txt", "r") as f:
            content = f.read()

        # Check for critical dependencies
        critical_deps = [
            "fastapi",
            "uvicorn",
            "pydantic",
            "pydantic-settings",
            "celery",
            "email-validator",
        ]

        missing_deps = []
        for dep in critical_deps:
            if dep not in content.lower():
                missing_deps.append(dep)

        if not missing_deps:
            print("✅ All critical dependencies are listed")
            return True
        else:
            print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
            return False

    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False


def check_pyproject():
    """Check pyproject.toml."""
    print_header("Checking pyproject.toml")

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

        if all_good:
            print("✅ pyproject.toml is properly configured")
            return True
        else:
            print("❌ pyproject.toml has issues")
            return False

    except ImportError:
        print("⚠ tomli not installed, skipping detailed check")
        # Basic file existence check
        if Path("pyproject.toml").exists():
            print("✓ pyproject.toml exists")
            return True
        else:
            print("✗ pyproject.toml missing")
            return False
    except Exception as e:
        print(f"❌ Error checking pyproject.toml: {e}")
        return False


def main():
    """Main function."""
    print("=" * 60)
    print("FINAL CHECK: StereoBrother Bot Project")
    print("=" * 60)

    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Run all checks
    checks = [
        ("File Structure", check_file_structure),
        ("Python Imports", check_python_imports),
        ("GitHub Workflow", check_workflow_file),
        ("Tests", check_tests),
        ("Dockerfile", check_dockerfile),
        ("Requirements", check_requirements),
        ("PyProject", check_pyproject),
    ]

    results = []
    for check_name, check_func in checks:
        try:
            success = check_func()
            results.append((check_name, success))
        except Exception as e:
            print(f"❌ Error during {check_name}: {e}")
            results.append((check_name, False))

    # Print summary
    print_header("CHECK SUMMARY")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for check_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {check_name}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n" + "=" * 60)
        print("🎉 PROJECT IS READY FOR GITHUB PUSH!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. git add .")
        print("2. git commit -m 'Fix GitHub Actions workflow'")
        print("3. git push")
        print("\nThe workflow should now run successfully on GitHub!")
        return 0
    else:
        print("\n" + "=" * 60)
        print("⚠ PROJECT NEEDS FIXES BEFORE PUSH")
        print("=" * 60)
        print(f"\n{total - passed} check(s) failed. Please fix them before pushing.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCheck interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
