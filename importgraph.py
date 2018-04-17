import abc
import argparse
import builtins
import os
import re
import sys
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Mapping
from collections import defaultdict, deque

from graphviz import Digraph


ModulePath = Tuple[str, ...]
ImportFunctionType = Callable[[str, Dict[str, Any], Dict[str, Any], List[str], int], Any]


class ImportAction:

    UNKNOWN_MODULE_NAME = '<unknown>'
    
    def __init__(self,
        name: str,
        the_globals: Dict[str, Any],
        fromlist: Optional[List[str]],
        level: int,
        imported_module: ModuleType,
    ) -> None:
        self._name = name
        self._globals = the_globals
        self._fromlist = fromlist
        self._level = level
        self._imported_module = imported_module

    def from_name(self) -> str:
        if self._globals is None:
            return self.UNKNOWN_MODULE_NAME
        try:
            return self._globals['__name__']
        except KeyError:
            return self.UNKNOWN_MODULE_NAME

    def _build_imported_paths(self) -> Iterable[ModulePath]:
        """Fully qualified names for `from ... import ...` imports

        This resolves relative imports and returns one path for every imported item in the fromlist
        """
        from_module_path = self.from_name().split('.')
        root_module = from_module_path[:-self._level]
        if self._name:
            root_module += self._name.split('.')
        return [tuple(root_module + [from_item]) for from_item in self._fromlist]

    @staticmethod
    def _get_module(name: str):
        try:
            return sys.modules[name]
        except KeyError:
            return None

    @classmethod
    def module_file_path(cls, name: str):
        module = cls._get_module(name)
        if module is None:
            return ''
        try:
            return module.__file__
        except AttributeError:
            return ''

    def _last_module_in_path(self, path: ModulePath) -> ModulePath:
        """Given a path, find the last item that refers to a module object"""
        for sub_path in (path[:i] for i in reversed(range(len(path) + 1))):
            if self._get_module('.'.join(sub_path)) is not None:
                return sub_path
        return tuple()

    def imported_names(self) -> Iterable[str]:
        if self._fromlist is None:
            return [self._name]
        imported_paths = self._build_imported_paths()
        imported_module_paths = {self._last_module_in_path(imported_path) for imported_path in imported_paths}
        return ['.'.join(module_path) for module_path in imported_module_paths]


class AbstractImportGraph(metaclass=abc.ABCMeta):
    def __init__(self, filename_regex=None, exclude_files=None) -> None:
        if filename_regex is not None:
            self._filename_regex = re.compile(filename_regex)
        else:
            self._filename_regex = None
        exclude_files = exclude_files or []
        self.nodes = set()  # type: Set[str]
        self._exclude_regexes = [re.compile(exclude_re) for exclude_re in exclude_files]
        self._edges = set()  # type: Set[Tuple[str, str]]
        self._adjacency_list = defaultdict(set)  # type: Mapping[str, Set[str]]
        self._reverse_adjacency_list = defaultdict(set)  # type: Mapping[str, Set[str]]
        self._node_hierarchy = {}  # type: Mapping[str, int]
        super().__init__()
    
    def imported_modules(self, node: str) -> Optional[Set[str]]:
        return self._adjacency_list.get(node)
    
    def importing_modules(self, node: str) -> Optional[Set[str]]:
        return self._reverse_adjacency_list.get(node)

    def _files_match_regex(self, from_name: str, to_name: str) -> bool:
        if self._filename_regex is None:
            return True
        from_match = self._filename_regex.fullmatch(ImportAction.module_file_path(from_name))
        to_match = self._filename_regex.fullmatch(ImportAction.module_file_path(to_name))
        return bool(from_match and to_match)

    def _files_are_excluded(self, from_name: str, to_name: str) -> bool:
        for regex in self._exclude_regexes:
            if (
                regex.fullmatch(ImportAction.module_file_path(from_name)) or
                regex.fullmatch(ImportAction.module_file_path(to_name))
            ):
                return True
        return False

    def _should_keep_edge(self, from_name: str, to_name: str) -> bool:
        return self._files_match_regex(from_name, to_name) and not self._files_are_excluded(from_name, to_name)

    def _add_node(self, node: str) -> None:
        if node not in self.nodes:
            self.nodes.add(node)

    def _add_edge(self, edge: Tuple[str, str]) -> None:
        for node in edge:
            if node not in self.nodes:
                self._add_node(node)
        if edge not in self._edges:
            tail, head = edge
            self._edges.add(edge)
            self._adjacency_list[tail].add(head)
            self._reverse_adjacency_list[head].add(tail)

    def _build_hierarchy(self):
        self._node_hierarchy = defaultdict(int)
        root_queue = deque(node for node in self.nodes if not self.importing_modules(node))
        sub_hierarchies = {node: {node} for node in root_queue}
        while root_queue:
            root_node = root_queue.popleft()
            work_queue = deque([(root_node, 0)])
            while work_queue:
                node, level = work_queue.popleft()
                for other_root, children in sub_hierarchies.items():
                    if other_root == root_node:
                        continue
                    if node in children:
                        current_node_level = self._node_hierarchy[node]
                        offset = current_node_level - level
                        for node in children:
                            self._node_hierarchy[node] -= offset
                        del sub_hierarchies[other_root]
                        break
                else: # if loop didn't break
                    self._node_hierarchy[node] = level
                    work_queue.extend((child, level + 1) for child in self.imported_modules(node))
                    sub_hierarchies[root_node].add(node)
        min_level = min(self._node_hierarchy.values())
        for node in self._node_hierarchy:
            self._node_hierarchy[node] -= min_level
    
    def add_import(self, import_action: ImportAction) -> None:
        for name in import_action.imported_names():
            edge = (import_action.from_name(), name)
            if self._should_keep_edge(*edge):
                self._add_edge(edge)

    @abc.abstractmethod
    def save(self, filename: str) -> None:
        pass

    @abc.abstractmethod
    def to_string(self) -> str:
        pass


class CouplingGraph:
    def __init__(self, import_graph: AbstractImportGraph) -> None:
        self._import_graph = import_graph


class DotImportGraph(AbstractImportGraph):
    def _build_digraph(self):
        digraph = Digraph(name='Imports', graph_attr={
            'splines': 'ortho',
        })
        for node in self.nodes:
            digraph.node(node, shape='rectangle')
        for edge in self._edges:
            digraph.edge(*edge)
        return digraph

    def to_string(self) -> str:
        return self._build_digraph().source

    def save(self, filename: str) -> None:
        self._build_digraph().save(filename=filename)


class ModuleClusterer(AbstractImportGraph):
    def __init__(self, import_graph: AbstractImportGraph) -> None:
        self._import_graph = import_graph


class ImportGraphCommand:
    def __init__(self, args=List[str]):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            'module',
            nargs='+',
            help='The name of the module to build an import graph from. All specified modules'
            ' will be imported and an import graph will be build for all subsequent imports.',
        )
        parser.add_argument(
            '-o', '--output',
            type=argparse.FileType('w'),
            default=None,
            help='Specify a file to save the output to.'
        )
        parser.add_argument(
            '-r', '--regex',
            type=str,
            default=None,
            help='Define a (python) regex to filter all imports with. This regex will be'
            ' applied to the filenames of an imported module. If the regex does not fully match the'
            ' filename, the module will not be saved to the graph (subsequent imports will still appear).',
        )
        parser.add_argument(
            '-x', '--exclude',
            action='append',
            default=[],
            help='Define a regex to exclude certain modules. If this regex fully matches the filename then'
            ' the module will not be saved on the import graph. This option may be used multiple times to'
            ' exclude multiple patterns.',
        )
        parser.add_argument(
            '-d', '--directory',
            action='store_true',
            default=False,
            help='Use directory names instead of module names. This will import all modules in the specified'
            ' directories recursively. All specified directories will be added to the sys.path to ensure'
            ' that the modules can be found.',
        )
        self._options = parser.parse_args(args=args)
        self._import_graph = DotImportGraph(
            filename_regex=self._options.regex,
            exclude_files=self._options.exclude,
        )

    def _import_wrapper(self, old_import: ImportFunctionType) -> ImportFunctionType:
        def new_import(
            name: str,
            the_globals: Dict[str, Any]=None,
            the_locals: Dict[str, Any]=None,
            fromlist: List[str]=(),
            level: int=0,
        ) -> ModuleType:
            module = old_import(name, the_globals, the_locals, fromlist, level)
            import_action = ImportAction(name, the_globals, fromlist, level, module)
            self._import_graph.add_import(import_action)
            return module
        return new_import

    def _collect_module_names(self, directory, parents=()):
        modules = []
        if '__init__.py' not in os.listdir(directory) and parents:
            return modules
        for file_name in os.listdir(directory):
            full_name = os.path.join(directory, file_name)
            if os.path.isfile(full_name):
                name, extention = os.path.splitext(file_name)
                if extention == '.py':
                    if name == '__init__' and parents:
                        modules.append('.'.join(parents))
                    else:
                        modules.append('.'.join(parents + (name,)))
            elif os.path.isdir(full_name) and not file_name == '__pycache__':
                modules.extend(self._collect_module_names(full_name, parents=parents + (file_name,)))
        return modules

    def _module_names(self):
        if not self._options.directory:
            return self._options.module
        modules = []
        for directory in self._options.module:
            sys.path.append(directory)
            modules += self._collect_module_names(directory)
        return modules

    def run(self):
        old_import = builtins.__import__
        builtins.__import__ = self._import_wrapper(old_import)
        for module_name in self._module_names():
            old_import(module_name)
        if self._options.output is not None:
            self._import_graph.save(self._options.output.name)
        else:
            print(self._import_graph.to_string())


def main():
    command = ImportGraphCommand(sys.argv[1:])
    command.run()

if __name__ == '__main__':
    main()
