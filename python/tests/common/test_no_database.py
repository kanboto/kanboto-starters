"""The database is optional: without `DATABASE_URL`, nothing opens a pool and `migrate` refuses to run."""

import pytest

from common import db, schema

pytestmark = pytest.mark.usefixtures("no_database")


async def test_nothing_to_check_or_close() -> None:
    assert not db.configured() and db.engines() == []
    await db.ping(0.1)
    await db.dispose()
    with pytest.raises(db.NotConfiguredError):
        db.sessionmaker()


def test_migrate_stops_with_a_clear_message(caplog: pytest.LogCaptureFixture) -> None:
    with pytest.raises(SystemExit) as stopped:
        schema.migrate()
    assert stopped.value.code == 1
    assert "DATABASE_URL is not set: migrate needs a database" in caplog.text
