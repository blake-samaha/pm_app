"""
Architecture tests to enforce layered architecture boundaries.

These tests scan the backend codebase imports and verify that:
1. routers/ never imports from repositories/
2. repositories/ never imports from routers/ or services/
3. models/ never imports from routers/, services/, or repositories/
4. No circular dependencies exist at the package level

These guardrails help maintain a clean layered architecture:
    routers -> services -> repositories -> models
                       |-> integrations
"""

import ast
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

BACKEND_ROOT = Path(__file__).parent.parent.parent

# Define the layers and their allowed dependencies
# Each layer can only import from layers listed in its "allowed" set
LAYER_RULES: Dict[str, Set[str]] = {
    "routers": {
        "services",
        "schemas",
        "models",
        "exceptions",
        "dependencies",
        "permissions",
        "config",
        "database",
        "integrations",
        "middleware",
    },
    "services": {
        "repositories",
        "models",
        "schemas",
        "exceptions",
        "integrations",
        "config",
        "database",
        "permissions",
    },
    "repositories": {"models", "database", "exceptions"},
    "models": {"exceptions"},
    "integrations": {"models", "schemas", "exceptions", "config"},
    "schemas": {"models", "exceptions"},
}

# Layers that must NOT be imported by certain other layers (explicit denials)
FORBIDDEN_IMPORTS: Dict[str, Set[str]] = {
    "routers": {"repositories"},  # routers must not import repositories
    "repositories": {
        "routers",
        "services",
    },  # repos must not import routers or services
    "models": {
        "routers",
        "services",
        "repositories",
    },  # models must not import business layers
}


def get_imports_from_file(file_path: Path) -> List[str]:
    """Extract all import module names from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return imports


def get_package_files(package_name: str) -> List[Path]:
    """Get all Python files in a package directory."""
    package_dir = BACKEND_ROOT / package_name
    if not package_dir.exists():
        return []
    return list(package_dir.glob("**/*.py"))


def build_import_graph() -> Dict[str, Set[str]]:
    """
    Build a graph of package-level imports.

    Returns a dict mapping package names to sets of packages they import from.
    """
    packages = [
        "routers",
        "services",
        "repositories",
        "models",
        "integrations",
        "schemas",
    ]
    graph: Dict[str, Set[str]] = defaultdict(set)

    for package in packages:
        for file_path in get_package_files(package):
            imports = get_imports_from_file(file_path)
            for imp in imports:
                # Only track imports of our internal packages
                if imp in packages:
                    graph[package].add(imp)

    return graph


def find_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Find all cycles in the import graph using DFS."""
    cycles = []
    visited = set()
    rec_stack = []

    def dfs(node: str, path: List[str]) -> None:
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return

        if node in visited:
            return

        visited.add(node)
        rec_stack.append(node)

        for neighbor in graph.get(node, []):
            dfs(neighbor, path + [node])

        rec_stack.pop()

    for node in graph:
        dfs(node, [])

    return cycles


class TestArchitectureBoundaries:
    """Test that architecture layer boundaries are respected."""

    def test_routers_do_not_import_repositories(self):
        """Routers should go through services, not directly to repositories."""
        violations = []

        for file_path in get_package_files("routers"):
            imports = get_imports_from_file(file_path)
            for imp in imports:
                if imp == "repositories":
                    violations.append(
                        f"{file_path.relative_to(BACKEND_ROOT)}: imports 'repositories'"
                    )

        assert not violations, (
            "Routers must not import repositories directly. "
            "Use services instead.\n\nViolations:\n" + "\n".join(violations)
        )

    def test_repositories_do_not_import_services_or_routers(self):
        """Repositories should only know about models and database."""
        violations = []
        forbidden = {"services", "routers"}

        for file_path in get_package_files("repositories"):
            imports = get_imports_from_file(file_path)
            for imp in imports:
                if imp in forbidden:
                    violations.append(
                        f"{file_path.relative_to(BACKEND_ROOT)}: imports '{imp}'"
                    )

        assert not violations, (
            "Repositories must not import services or routers. "
            "They should only depend on models and database.\n\nViolations:\n"
            + "\n".join(violations)
        )

    def test_models_do_not_import_business_layers(self):
        """Models should be pure data structures with no business logic dependencies."""
        violations = []
        forbidden = {"services", "routers", "repositories"}

        for file_path in get_package_files("models"):
            imports = get_imports_from_file(file_path)
            for imp in imports:
                if imp in forbidden:
                    violations.append(
                        f"{file_path.relative_to(BACKEND_ROOT)}: imports '{imp}'"
                    )

        assert not violations, (
            "Models must not import services, routers, or repositories. "
            "They should be pure data structures.\n\nViolations:\n"
            + "\n".join(violations)
        )

    def test_no_circular_dependencies(self):
        """There should be no circular dependencies between packages."""
        graph = build_import_graph()
        cycles = find_cycles(graph)

        # Filter out self-references and duplicates
        unique_cycles = []
        seen = set()
        for cycle in cycles:
            if len(cycle) > 2:  # More than just A -> A
                cycle_key = tuple(sorted(cycle[:-1]))  # Remove duplicate end node
                if cycle_key not in seen:
                    seen.add(cycle_key)
                    unique_cycles.append(" -> ".join(cycle))

        assert not unique_cycles, (
            "Circular dependencies detected between packages:\n"
            + "\n".join(f"  {c}" for c in unique_cycles)
        )

    def test_layer_boundaries_summary(self):
        """
        Summary test that checks all forbidden imports.

        This provides a single comprehensive check of all architecture rules.
        """
        graph = build_import_graph()
        violations = []

        for package, forbidden in FORBIDDEN_IMPORTS.items():
            actual_imports = graph.get(package, set())
            for forbidden_pkg in forbidden:
                if forbidden_pkg in actual_imports:
                    violations.append(
                        f"{package}/ imports {forbidden_pkg}/ (forbidden)"
                    )

        assert not violations, (
            "Architecture layer violations detected:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nExpected layer order: routers -> services -> repositories -> models"
        )
