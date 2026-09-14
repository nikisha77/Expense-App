import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class MemberCreate(BaseModel):
    name: str


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class GroupCreate(BaseModel):
    name: str


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_at: datetime.datetime
    members: list[MemberOut] = []


class ExpenseShareIn(BaseModel):
    member_id: int
    share_amount: float


class ExpenseCreate(BaseModel):
    description: str
    amount: float
    paid_by_member_id: int
    # Either give explicit shares (custom split) or member_ids (equal split
    # across those members). Exactly one of the two should be provided.
    member_ids: list[int] | None = None
    shares: list[ExpenseShareIn] | None = None

    @model_validator(mode="after")
    def check_split(self):
        if not self.member_ids and not self.shares:
            raise ValueError("Provide either member_ids (equal split) or shares (custom split)")
        if self.shares:
            total = round(sum(s.share_amount for s in self.shares), 2)
            if abs(total - round(self.amount, 2)) > 0.01:
                raise ValueError("Custom shares must sum to the expense amount")
        return self


class ExpenseShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    member_id: int
    share_amount: float


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    description: str
    amount: float
    paid_by_member_id: int
    created_at: datetime.datetime
    shares: list[ExpenseShareOut] = []


class BalanceOut(BaseModel):
    member_id: int
    name: str
    balance: float  # positive = is owed, negative = owes


class SettlementOut(BaseModel):
    from_member_id: int
    from_name: str
    to_member_id: int
    to_name: str
    amount: float
