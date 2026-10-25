"""Custom pytest fixtures package.

Fixtures are split by concern and re-exported from ``fixtures`` so ``conftest.py``
can simply do ``from fixtures import *``.
"""
from fixtures.browser_fixtures import *  # noqa: F401,F403
from fixtures.page_fixtures import *  # noqa: F401,F403
from fixtures.data_fixtures import *  # noqa: F401,F403
from fixtures.api_fixtures import *  # noqa: F401,F403
from fixtures.utility_fixtures import *  # noqa: F401,F403
