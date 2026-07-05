"""Phase 0 smoke test: the package imports and its subpackages are present."""

import estatescout
from estatescout import assistant, finance, rag


def test_package_imports():
    assert estatescout.__doc__
    assert finance.__doc__
    assert rag.__doc__
    assert assistant.__doc__
