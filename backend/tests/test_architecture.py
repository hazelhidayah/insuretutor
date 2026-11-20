import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest


APP = Path(__file__).resolve().parents[1] / "app"
FORBIDDEN_IMPORTS = {
    "app.providers": ("app.main", "app.chat", "app.evaluation", "app.retrieval"),
    "app.retrieval": ("app.main", "app.chat", "app.evaluation", "app.providers"),
}


def imports(source: str, package: str):
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            yield from ((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = resolve_name("." * node.level + module, package)
            yield module, node.lineno
            for alias in node.names:
                yield f"{module}.{alias.name}", node.lineno


def violations(source: str, package: str, forbidden: tuple[str, ...]):
    for imported, line in imports(source, package):
        module = imported.removeprefix("backend.")
        if any(module == target or module.startswith(f"{target}.") for target in forbidden):
            yield line, imported


@pytest.mark.parametrize("layer", FORBIDDEN_IMPORTS)
def test_infrastructure_imports_stay_below_orchestration(layer: str) -> None:
    failures = []
    for path in (APP / layer.rsplit(".", 1)[1]).rglob("*.py"):
        package = ".".join(("app", *path.relative_to(APP).parent.parts))
        for line, module in violations(path.read_text(encoding="utf-8"), package, FORBIDDEN_IMPORTS[layer]):
            failures.append(f"{path.relative_to(APP)}:{line} imports {module}")
    assert not failures, (
        "Keep adapter dependencies one-way. Compose retrieval and providers in chat.py "
        "or wire them in main.py.\n" + "\n".join(failures)
    )


@pytest.mark.parametrize("statement", [
    "from .. import chat",
    "from ..chat import ChatService",
    "import backend.app.main as api",
    "from app import retrieval",
])
def test_boundary_check_detects_forbidden_import_forms(statement: str) -> None:
    assert list(violations(statement, "app.providers", FORBIDDEN_IMPORTS["app.providers"]))
