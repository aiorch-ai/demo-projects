from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_setup_uses_requested_package_configuration():
    setup_text = (PROJECT_ROOT / "setup.py").read_text()

    assert "from setuptools import setup" in setup_text
    assert "packages=['todo']" in setup_text
    assert "install_requires=['pydantic>=2.5.0']" in setup_text
    assert "entry_points={'console_scripts': ['todo=todo.cli:main']}" in setup_text
    assert "python_requires='>=3.10'" in setup_text
    assert "find_packages" not in setup_text


def test_readme_matches_required_commands_and_examples():
    readme_text = (PROJECT_ROOT / "README.md").read_text()

    assert "pip install -e ." in readme_text
    assert "pip install -r requirements.txt" not in readme_text
    assert "pytest tests/" in readme_text
    assert "pytest tests/ -v" not in readme_text

    for command in ("add", "list", "done", "delete", "search", "stats"):
        assert f"| `{command}` |" in readme_text

    for forbidden in ("--title", "--description", "--priority", "--due-date", "--status"):
        assert forbidden not in readme_text
