from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.security import create_access_token
from app.user.model import User
from app.task.model import Task, DayTask

TODAY = date(2026, 11, 2)
PAYLOAD = {
    "title": "Mine",
    "time": 2.0,
    "target": 2.0,
    "date": TODAY.isoformat(),
}

async def _make_user(db, email: str) -> User:
    user = User(username=email.split("@")[0], email=email,
                hashed_password="x", email_verified=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

def _auth(user: User) -> dict:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}

async def _make_task(db, owner: User, title: str = "task") -> Task:
    task = Task(title=title, owner_id=owner.id, target_default=2.0)
    db.add(task)
    await db.flush()
    return task

async def _make_day_task(db, owner, title="task", time=1.0, target=2.0) -> DayTask:
    task = await _make_task(db, owner, title)
    day_task = DayTask(task_id=task.id, date=TODAY, time=time, target=target)
    db.add(day_task)
    await db.commit()
    await db.refresh(day_task)
    return day_task

@pytest.mark.asyncio
async def test_returns_only_current_users_tasks(client, db):
    me = await _make_user(db, "me@example.com")
    other = await _make_user(db, "other@example.com")

    my_task = await _make_task(db, me, "mine")
    their_task = await _make_task(db, other, "theirs")

    db.add_all([
        DayTask(task_id=my_task.id, date=TODAY, time=1.0, target=2.0),
        DayTask(task_id=their_task.id, date=TODAY, time=1.0, target=2.0),
    ])
    await db.commit()

    response = await client.get(f"/days/{TODAY.isoformat()}/tasks", headers=_auth(me))

    assert response.status_code == 200
    titles = [item["task"]["title"] for item in response.json()]
    assert titles == ["mine"]


@pytest.mark.asyncio
async def test_filters_by_date(client, db):
    me = await _make_user(db, "me@example.com")
    task = await _make_task(db, me, "mine")
    db.add(task)
    await db.flush()
    db.add(DayTask(task_id=task.id, date=TODAY + timedelta(days=1), time=1, target=2))
    await db.commit()

    response = await client.get(f"/days/{TODAY.isoformat()}/tasks", headers=_auth(me))

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_requires_auth(client):
    response = await client.get(f"/days/{TODAY.isoformat()}/tasks")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_creates_task(client, db):
    me = await _make_user(db, "me@example.com")

    response = await client.post(
        "/days/day-tasks",
        json=PAYLOAD,
        headers=_auth(me)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["date"] == TODAY.isoformat()
    assert body["task"]["title"] == "Mine"

    tasks = (await db.scalars(select(Task).where(Task.owner_id == me.id))).all()
    assert len(tasks) == 1
    assert tasks[0].target_default == 2.0

async def test_new_task_belongs_to_current_user(client, db):
    me = await _make_user(db, "me@example.com")
    other = await _make_user(db, "other@example.com")
    payload = {"title": "Read", "date": TODAY.isoformat(), "time": 1.0, "target": 2.0}

    await client.post("/days/day-tasks", json=payload, headers=_auth(me))

    other_tasks = (await db.scalars(select(Task).where(Task.owner_id == other.id))).all()
    assert other_tasks == []

async def test_update_block_changes_fields(client, db):
    me = await _make_user(db, "me@example.com")
    day_task = await _make_day_task(db, me, "old")
    payload = {"title": "new", "date": TODAY.isoformat(), "time": 3.0, "target": 5.0}

    response = await client.put(f"days/{day_task.id}", json=payload, headers=_auth(me))

    assert response.status_code == 200
    await db.refresh(day_task, ["task"])
    assert day_task.task.title == "new"
    assert day_task.time == 3.0
    assert day_task.target == 5.0


async def test_update_block_of_another_user_is_forbidden(client, db):
    me = await _make_user(db, "me@example.com")
    other = await _make_user(db, "other@example.com")
    day_task = await _make_day_task(db, other, "theirs")
    payload = {"title": "hacked", "date": TODAY.isoformat(), "time": 1.0, "target": 1.0}

    response = await client.put(f"days/{day_task.id}", json=payload, headers=_auth(me))

    assert response.status_code in (403, 404)
    await db.refresh(day_task, ["task"])
    assert day_task.task.title == "theirs"

async def test_update_description(client, db):
    me = await _make_user(db, "me@example.com")
    day_task = await _make_day_task(db, me)

    response = await client.put(
        f"days/{day_task.id}/description",
        json={"description": "Notes"},
        headers=_auth(me),
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Notes"

async def test_update_time(client, db):
    me = await _make_user(db, "me@example.com")
    day_task = await _make_day_task(db, me, time=1.0)

    response = await client.patch(
        f"days/{day_task.id}/time", json={"time": 4.5}, headers=_auth(me)
    )

    assert response.status_code == 200
    await db.refresh(day_task)
    assert day_task.time == 4.5

async def test_delete_block(client, db):
    me = await _make_user(db, "me@example.com")
    day_task = await _make_day_task(db, me)
    day_id = day_task.id

    response = await client.delete(f"days/{day_id}", headers=_auth(me))

    assert response.status_code == 204
    assert await db.get(DayTask, day_id) is None

async def test_get_current_user(client, db):
    me = await _make_user(db, "me@example.com")

    response = await client.get("days/user", headers=_auth(me))

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
    assert "hashed_password" not in response.json()

async def test_statistic_includes_only_own_data(client, db):
    me = await _make_user(db, "me@example.com")
    other = await _make_user(db, "other@example.com")
    await _make_day_task(db, me, "mine", time=2.0)
    await _make_day_task(db, other, "theirs", time=9.0)

    response = await client.get(
        "days/statistic",
        params={"first_date": TODAY.isoformat(), "last_date": TODAY.isoformat()},
        headers=_auth(me),
    )

    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert "theirs" not in titles
    assert "mine" in titles


async def test_circle_statistic_requires_auth(client):
    response = await client.get(
        "days/circle-statistic",
        params={"first_date": TODAY.isoformat(), "last_date": TODAY.isoformat()},
    )
    assert response.status_code in (401, 403)