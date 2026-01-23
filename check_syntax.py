#!/usr/bin/env python3
"""
Syntax check script for StereoBrother Bot.
This script checks Python files for syntax errors and common issues.
"""

import ast
import os
import sys
from pathlib import Path


def check_python_file(file_path: Path) -> tuple[bool, list[str]]:
    """Check a Python file for syntax errors."""
    errors = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for syntax errors
        try:
            ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            errors.append(
                f"Syntax error: {e.msg} at line {e.lineno}, column {e.offset}"
            )
            return False, errors

        # Check for common issues
        lines = content.split("\n")

        # Check for mixed tabs and spaces
        for i, line in enumerate(lines, 1):
            if "\t" in line and " " in line:
                # Check if it's actually mixed or just spaces after tabs
                if line.replace("\t", "").startswith(" "):
                    errors.append(f"Line {i}: Mixed tabs and spaces")

        # Check for trailing whitespace
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:
                errors.append(f"Line {i}: Trailing whitespace")

        # Check for missing newline at end of file
        if content and not content.endswith("\n"):
            errors.append("Missing newline at end of file")

        # Check file encoding (basic check)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                f.read()
        except UnicodeDecodeError:
            errors.append("File is not valid UTF-8")

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Error reading file: {e}"]


def check_imports(file_path: Path) -> tuple[bool, list[str]]:
    """Check if imports can be resolved."""
    errors = []

    try:
        # Add project root to Python path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse imports from AST
        tree = ast.parse(content, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        __import__(alias.name)
                    except ImportError as e:
                        # Check if it's a local module
                        module_path = alias.name.replace(".", "/")
                        possible_paths = [
                            project_root / f"{module_path}.py",
                            project_root / module_path / "__init__.py",
                            project_root / "src" / f"{module_path}.py",
                            project_root / "src" / module_path / "__init__.py",
                            project_root / "config" / f"{module_path}.py",
                            project_root / "config" / module_path / "__init__.py",
                            project_root / "services" / f"{module_path}.py",
                            project_root / "services" / module_path / "__init__.py",
                            project_root / "utils" / f"{module_path}.py",
                            project_root / "utils" / module_path / "__init__.py",
                            project_root / "models" / f"{module_path}.py",
                            project_root / "models" / module_path / "__init__.py",
                        ]

                        if not any(p.exists() for p in possible_paths):
                            errors.append(f"Import not found: {alias.name} ({e})")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    try:
                        __import__(node.module)
                    except ImportError as e:
                        # Check if it's a local module
                        module_path = node.module.replace(".", "/")
                        possible_paths = [
                            project_root / f"{module_path}.py",
                            project_root / module_path / "__init__.py",
                            project_root / "src" / f"{module_path}.py",
                            project_root / "src" / module_path / "__init__.py",
                            project_root / "config" / f"{module_path}.py",
                            project_root / "config" / module_path / "__init__.py",
                            project_root / "services" / f"{module_path}.py",
                            project_root / "services" / module_path / "__init__.py",
                            project_root / "utils" / f"{module_path}.py",
                            project_root / "utils" / module_path / "__init__.py",
                            project_root / "models" / f"{module_path}.py",
                            project_root / "models" / module_path / "__init__.py",
                        ]

                        if not any(p.exists() for p in possible_paths):
                            errors.append(
                                f"Import not found: from {node.module} import ... ({e})"
                            )

        return len(errors) == 0, errors

    except Exception as e:
        return False, [f"Error checking imports: {e}"]


def find_python_files(directory: Path) -> list[Path]:
    """Find all Python files in directory."""
    python_files = []

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and virtual environments
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and d not in ["__pycache__", "venv", ".venv"]
        ]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return sorted(python_files)


def main() -> int:
    """Main function."""
    project_root = Path(__file__).parent

    # Directories to check
    directories = [
        project_root / "src",
        project_root / "config",
        project_root / "services",
        project_root / "utils",
        project_root / "models",
        project_root / "tests",
    ]

    all_python_files = []
    for directory in directories:
        if directory.exists():
            all_python_files.extend(find_python_files(directory))

    # Also check root Python files
    for file in project_root.glob("*.py"):
        if file.name != __file__:
            all_python_files.append(file)

    print(f"Checking {len(all_python_files)} Python files...")
    print("=" * 80)

    total_errors = 0
    files_with_errors = 0

    for file_path in all_python_files:
        relative_path = file_path.relative_to(project_root)

        # Check syntax
        syntax_ok, syntax_errors = check_python_file(file_path)

        # Check imports (only for non-test files)
        imports_ok = True
        import_errors = []

        if "tests" not in str(file_path):
            imports_ok, import_errors = check_imports(file_path)

        if syntax_ok and imports_ok:
            print(f"✓ {relative_path}")
        else:
            files_with_errors += 1
            print(f"✗ {relative_path}")

            for error in syntax_errors:
                print(f"  Syntax: {error}")
                total_errors += 1

            for error in import_errors:
                print(f"  Import: {error}")
                total_errors += 1

    print("=" * 80)

    if total_errors == 0:
        print(f"✅ All {len(all_python_files)} files passed syntax and import checks!")
        return 0
    else:
        print(f"❌ Found {total_errors} errors in {files_with_errors} files")
        print("\nCommon issues to fix:")
        print("1. Check that all imported modules exist")
        print(
            "2. Run 'python3 -m pip install -r requirements.txt' to install dependencies"
        )
        print("3. Make sure __init__.py files exist in package directories")
        print("4. Check for syntax errors in the files listed above")
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
