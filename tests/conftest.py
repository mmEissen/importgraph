import pytest
from unittest.mock import MagicMock

from importgraph import ImportAction


@pytest.fixture
def import_action():
    return ImportAction('some.module.name', {}, [], 0, MagicMock())
