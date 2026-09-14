import os

os.environ["DATABASE_URL"] = "sqlite:///./test_splitzy.db"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_group_with_members(names):
    group = client.post("/groups", json={"name": "Trip"}).json()
    members = []
    for name in names:
        m = client.post(f"/groups/{group['id']}/members", json={"name": name}).json()
        members.append(m)
    return group, members


def test_create_and_get_group():
    resp = client.post("/groups", json={"name": "Goa Trip"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Goa Trip"
    assert data["members"] == []

    get_resp = client.get(f"/groups/{data['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == data["id"]


def test_add_member():
    group = client.post("/groups", json={"name": "Roomies"}).json()
    resp = client.post(f"/groups/{group['id']}/members", json={"name": "Asha"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Asha"


def test_add_expense_equal_split():
    group, members = create_group_with_members(["Asha", "Bala", "Chitra"])
    ids = [m["id"] for m in members]
    resp = client.post(
        f"/groups/{group['id']}/expenses",
        json={
            "description": "Dinner",
            "amount": 300,
            "paid_by_member_id": ids[0],
            "member_ids": ids,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount"] == 300
    assert len(data["shares"]) == 3
    assert sum(s["share_amount"] for s in data["shares"]) == pytest.approx(300)


def test_add_expense_custom_split_must_sum_to_amount():
    group, members = create_group_with_members(["Asha", "Bala"])
    ids = [m["id"] for m in members]
    resp = client.post(
        f"/groups/{group['id']}/expenses",
        json={
            "description": "Groceries",
            "amount": 100,
            "paid_by_member_id": ids[0],
            "shares": [
                {"member_id": ids[0], "share_amount": 40},
                {"member_id": ids[1], "share_amount": 40},
            ],
        },
    )
    assert resp.status_code == 422


def test_balances_and_settle_up():
    group, members = create_group_with_members(["Asha", "Bala"])
    a, b = members[0]["id"], members[1]["id"]
    client.post(
        f"/groups/{group['id']}/expenses",
        json={
            "description": "Hotel",
            "amount": 200,
            "paid_by_member_id": a,
            "member_ids": [a, b],
        },
    )

    balances = client.get(f"/groups/{group['id']}/balances").json()
    by_id = {b_["member_id"]: b_["balance"] for b_ in balances}
    assert by_id[a] == pytest.approx(100)
    assert by_id[b] == pytest.approx(-100)

    settlement = client.get(f"/groups/{group['id']}/settle-up").json()
    assert len(settlement) == 1
    assert settlement[0]["from_member_id"] == b
    assert settlement[0]["to_member_id"] == a
    assert settlement[0]["amount"] == pytest.approx(100)


def test_list_expenses():
    group, members = create_group_with_members(["Asha", "Bala"])
    ids = [m["id"] for m in members]
    client.post(
        f"/groups/{group['id']}/expenses",
        json={"description": "Snacks", "amount": 50, "paid_by_member_id": ids[0], "member_ids": ids},
    )
    resp = client.get(f"/groups/{group['id']}/expenses")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
