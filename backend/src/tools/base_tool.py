# Arquivo: src/tools/base_tool.py
from pydantic.v1 import BaseModel, Field
from typing import Type, Any

class BaseTool(BaseModel):
    name: str = Field(...)
    description: str = Field(...)
    args_schema: Type[BaseModel] = None

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if self.args_schema:
            args_model = self.args_schema.parse_obj(kwargs if kwargs else args[0])
            return self._run(**dict(args_model))
        else:
            return self._run(*args, **kwargs)

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("A subclasse da ferramenta deve implementar este método.")