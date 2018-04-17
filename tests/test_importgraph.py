from typing import Any, Dict, List, Optional, Set, Tuple
from unittest.mock import MagicMock

import pytest

from importgraph import ImportAction, ModulePath


class TestImportAction:

    @pytest.mark.parametrize(
        'the_globals,expected_result',
        [
            ({'__name__': 'an.importing.module'}, 'an.importing.module'),
            ({}, ImportAction.UNKNOWN_MODULE_NAME),
            (None, ImportAction.UNKNOWN_MODULE_NAME),
        ],
    )
    def test_from_name(self, the_globals: Optional[Dict[str, Any]], expected_result: str, import_action: ImportAction):
        import_action._globals = the_globals

        from_name = import_action.from_name()

        assert from_name == expected_result

    @pytest.mark.parametrize(
        'name,fromlist,level,expected_result',
        [
            # from . import module2
            ('', ['module2'], 1, {('some', 'module2')}),
            # from .module2 import SomeClass
            ('module2', ['SomeClass'], 1, {('some', 'module2', 'SomeClass')}),
            # from .. import module
            ('', ['module'], 2, {('module',)}),
            # from some.module1 import SomeClass
            ('some.module2', ['SomeClass'], 0, {('some', 'module2', 'SomeClass')}),
            # from . import module2, module3
            ('', ['module2', 'module3'], 1, {('some', 'module2'), ('some', 'module3')}),
        ],
    )
    def test_build_imported_paths(
        self,
        name: str,
        fromlist: Optional[List[str]],
        level: int,
        expected_result: Set[ModulePath],
        import_action: ImportAction,
    ) -> None:
        import_action.from_name = MagicMock(return_value='some.module')
        import_action._name = name
        import_action._level = level
        import_action._fromlist = fromlist

        import_paths = import_action._build_imported_paths()

        import_paths = list(import_paths)
        import_paths_set = set(import_paths)
        assert len(import_paths) == len(import_paths_set)
        assert import_paths_set == expected_result

    def test_last_module_in_path_returns_full_path_module_not_none(
        self,
        import_action: ImportAction,
    ) -> None:
        import_action._get_module = MagicMock()
        path = ('some', 'module', 'path')

        result = import_action._last_module_in_path(path)

        assert result == path
