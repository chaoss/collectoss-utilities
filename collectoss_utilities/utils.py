import importlib.metadata


class ToolMetadata:

    @property
    def version(self) -> str:
        return importlib.metadata.version("collectoss-utilities")

    @property
    def name(self) -> str:
        return "CollectOSS Utilities"