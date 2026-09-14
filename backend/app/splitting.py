"""Pure functions for computing balances and a minimal settle-up plan.
Kept separate from DB/route code so they're easy to unit test.
"""


def compute_balances(members: list[dict], expenses: list[dict]) -> dict[int, float]:
    """members: [{id, name}], expenses: [{amount, paid_by_member_id, shares: [{member_id, share_amount}]}]
    Returns {member_id: net_balance} where positive = is owed money.
    """
    balances = {m["id"]: 0.0 for m in members}
    for exp in expenses:
        balances[exp["paid_by_member_id"]] = balances.get(exp["paid_by_member_id"], 0.0) + exp["amount"]
        for share in exp["shares"]:
            balances[share["member_id"]] = balances.get(share["member_id"], 0.0) - share["share_amount"]
    return {k: round(v, 2) for k, v in balances.items()}


def settle_up(balances: dict[int, float]) -> list[dict]:
    """Greedy min-transaction settlement: match biggest creditor with biggest
    debtor repeatedly. Returns [{from_member_id, to_member_id, amount}].
    """
    creditors = sorted(
        [(mid, bal) for mid, bal in balances.items() if bal > 0.01], key=lambda x: -x[1]
    )
    debtors = sorted(
        [(mid, -bal) for mid, bal in balances.items() if bal < -0.01], key=lambda x: -x[1]
    )

    transactions = []
    i, j = 0, 0
    creditors, debtors = list(creditors), list(debtors)
    while i < len(creditors) and j < len(debtors):
        cred_id, cred_amt = creditors[i]
        debt_id, debt_amt = debtors[j]
        amount = round(min(cred_amt, debt_amt), 2)
        if amount > 0.01:
            transactions.append({"from_member_id": debt_id, "to_member_id": cred_id, "amount": amount})
        cred_amt -= amount
        debt_amt -= amount
        creditors[i] = (cred_id, cred_amt)
        debtors[j] = (debt_id, debt_amt)
        if cred_amt <= 0.01:
            i += 1
        if debt_amt <= 0.01:
            j += 1
    return transactions
