import click
import importlib
import pkgutil

@click.group()
def repair():
    """Run repair scripts for specific issues."""
    pass

# Auto-discover and register all issue_*.py modules in this package
package_path = __path__
for importer, modname, ispkg in pkgutil.iter_modules(package_path):
    if modname.startswith("issue_"):
        mod = importlib.import_module(f".{modname}", __package__)
        # Each module exposes a Click command named `command`
        if hasattr(mod, "command"):
            repair.add_command(mod.command)