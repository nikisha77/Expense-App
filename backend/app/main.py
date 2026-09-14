from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import Base, SessionLocal, engine, get_db
from app.splitting import compute_balances, settle_up

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Splitzy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev-friendly; tighten before real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/groups", response_model=schemas.GroupOut)
def create_group(payload: schemas.GroupCreate, db: Session = Depends(get_db)):
    group = models.Group(name=payload.name)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@app.get("/groups", response_model=list[schemas.GroupOut])
def list_groups(db: Session = Depends(get_db)):
    return db.query(models.Group).all()


@app.get("/groups/{group_id}", response_model=schemas.GroupOut)
def get_group(group_id: int, db: Session = Depends(get_db)):
    group = db.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@app.post("/groups/{group_id}/members", response_model=schemas.MemberOut)
def add_member(group_id: int, payload: schemas.MemberCreate, db: Session = Depends(get_db)):
    group = db.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    member = models.Member(group_id=group_id, name=payload.name)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@app.post("/groups/{group_id}/expenses", response_model=schemas.ExpenseOut)
def add_expense(group_id: int, payload: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    group = db.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    expense = models.Expense(
        group_id=group_id,
        description=payload.description,
        amount=payload.amount,
        paid_by_member_id=payload.paid_by_member_id,
    )
    db.add(expense)
    db.flush()  # get expense.id before creating shares

    if payload.shares:
        for s in payload.shares:
            db.add(models.ExpenseShare(expense_id=expense.id, member_id=s.member_id, share_amount=s.share_amount))
    else:
        n = len(payload.member_ids)
        equal_share = round(payload.amount / n, 2)
        remainder = round(payload.amount - equal_share * n, 2)
        for idx, member_id in enumerate(payload.member_ids):
            amt = equal_share + (remainder if idx == 0 else 0)
            db.add(models.ExpenseShare(expense_id=expense.id, member_id=member_id, share_amount=amt))

    db.commit()
    db.refresh(expense)
    return expense


@app.get("/groups/{group_id}/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(group_id: int, db: Session = Depends(get_db)):
    return db.query(models.Expense).filter(models.Expense.group_id == group_id).all()


def _group_balances(group_id: int, db: Session) -> dict[int, float]:
    group = db.get(models.Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    members = [{"id": m.id, "name": m.name} for m in group.members]
    expenses = [
        {
            "amount": e.amount,
            "paid_by_member_id": e.paid_by_member_id,
            "shares": [{"member_id": s.member_id, "share_amount": s.share_amount} for s in e.shares],
        }
        for e in group.expenses
    ]
    return members, compute_balances(members, expenses)


@app.get("/groups/{group_id}/balances", response_model=list[schemas.BalanceOut])
def get_balances(group_id: int, db: Session = Depends(get_db)):
    members, balances = _group_balances(group_id, db)
    name_by_id = {m["id"]: m["name"] for m in members}
    return [
        {"member_id": mid, "name": name_by_id[mid], "balance": bal} for mid, bal in balances.items()
    ]


@app.get("/groups/{group_id}/settle-up", response_model=list[schemas.SettlementOut])
def get_settle_up(group_id: int, db: Session = Depends(get_db)):
    members, balances = _group_balances(group_id, db)
    name_by_id = {m["id"]: m["name"] for m in members}
    plan = settle_up(balances)
    return [
        {
            "from_member_id": t["from_member_id"],
            "from_name": name_by_id[t["from_member_id"]],
            "to_member_id": t["to_member_id"],
            "to_name": name_by_id[t["to_member_id"]],
            "amount": t["amount"],
        }
        for t in plan
    ]
