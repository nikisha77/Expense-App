import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    members: Mapped[list["Member"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)

    group: Mapped["Group"] = relationship(back_populates="members")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    paid_by_member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )

    group: Mapped["Group"] = relationship(back_populates="expenses")
    paid_by: Mapped["Member"] = relationship()
    shares: Mapped[list["ExpenseShare"]] = relationship(
        back_populates="expense", cascade="all, delete-orphan"
    )


class ExpenseShare(Base):
    __tablename__ = "expense_shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    share_amount: Mapped[float] = mapped_column(Float, nullable=False)

    expense: Mapped["Expense"] = relationship(back_populates="shares")
    member: Mapped["Member"] = relationship()
