import builtins
from types import ModuleType
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from graphviz import Digraph


ModulePath = Tuple[str, ...]

class ImportAction:
    def __init__(self,
        name: str,
        the_globals: Dict[str, Any],
        the_locals: Dict[str, Any],
        fromlist: Optional[List[str]],
        level: int,
        imported_module: ModuleType,
    ) -> None:
        self._name = name
        self._globals = the_globals
        self._locals = the_locals
        self._fromlist = fromlist
        self._level = level
        self._imported_module = imported_module
    
    def from_name(self) -> str:
        return self._globals.get('__name__')
    
    def _build_imported_paths(self) -> Iterable[ModulePath]:
        """Fully qualified names for `from ... import ...` imports

        This resolves relative imports and returns one path for every imported item in the fromlist
        """
        from_module_path = self.from_name().split('.')
        root_module = from_module_path[:-self._level]
        if self._name:
            root_module += self._name.split('.')
        return [tuple(root_module + [from_item]) for from_item in self._fromlist]
    
    def _last_module_in_path(self, path: ModulePath) -> ModulePath:
        """Given a path, find the last item that refers to a module object"""
        module_path = self._imported_module.__name__.split('.')
        relative_path = self._name.split('.')[len(module_path):]
        obj = self._imported_module
        for name in relative_path:
            obj = getattr(obj, name)
            if not isinstance(obj, ModuleType):
                break
            module_path.append(name)
        return tuple(module_path)

    def imported_names(self) -> Iterable[str]:
        if self._fromlist is None:
            return [self._name]
        imported_paths = self._build_imported_paths()
        imported_module_paths = {self._last_module_in_path(imported_path) for imported_path in imported_paths}
        return ['.'.join(module_path) for module_path in imported_module_paths]


class ImportGraph(Digraph):
    def add_import(self, import_action: ImportAction) -> None:
        for name in import_action.imported_names():
            self.edge(import_action.from_name(), name)


import_graph = ImportGraph()
def import_wrapper(old_import):
    def new_import(name, the_globals, the_locals, fromlist, level):
        module = old_import(name, the_globals, the_locals, fromlist, level)
        import_action = ImportAction(name, the_globals, the_locals, fromlist, level, module)
        import_graph.add_import(import_action)
        return module
    return new_import

def main():
    old_init = builtins.__import__
    builtins.__import__ = import_wrapper(old_init)
    import a_package.a_module
    import_graph.save(filename='graph.dot')

if __name__ == '__main__':
    main()
