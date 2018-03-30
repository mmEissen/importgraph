import pytest
from typing import Dict, Optional, Any
from unittest import TestCase

from importgraph import ImportAction

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

    def test_build_imported_paths(self, import_action) -> None:
        pass
