from datetime import UTC, datetime

import pytest

from fairy.servers import store, tasks
from fairy.servers.models import Category

NOW = datetime(2026, 9, 17, 9, 0, tzinfo=UTC)


@pytest.fixture
def conn(tmp_path):
    """an empty database for each test"""
    with store.session(tmp_path / "test.db") as c:
        yield c


def test_add_task_assigns_id(conn):
    task = tasks.add_task(conn, "email professor")
    assert task.id == 1
    assert task.title == "email professor"
    assert task.done is False


def test_add_task_strips_whitespace(conn):
    task = tasks.add_task(conn, "  spaced out  ", now=NOW)
    assert task.title == "spaced out"


def test_add_task_defaults_to_optional(conn):
    task = tasks.add_task(conn, "something", now=NOW)
    assert task.category is Category.OPTIONAL


def test_add_task_accepts_a_category(conn):
    task = tasks.add_task(conn, "class at 2", Category.ANCHOR, now=NOW)
    assert task.category is Category.ANCHOR


def test_list_tasks_hides_completed_by_default(conn):
    tasks.add_task(conn, "keep me", now=NOW)
    finish = tasks.add_task(conn, "finish me", now=NOW)
    tasks.complete_task(conn, finish.id, now=NOW)

    assert [t.title for t in tasks.list_tasks(conn)] == ["keep me"]
    assert len(tasks.list_tasks(conn, include_done=True)) == 2


def test_complete_task_sets_timestamp(conn):
    task = tasks.add_task(conn, "do the thing", now=NOW)
    done = tasks.complete_task(conn, task.id, now=NOW)
    assert done.done is True
    assert done.completed_at == NOW


def test_get_unknown_task_raises(conn):
    with pytest.raises(KeyError):
        tasks.get_task(conn, 999)


def test_complete_unknown_task_raises(conn):
    with pytest.raises(KeyError):
        tasks.complete_task(conn, 999, now=NOW)
