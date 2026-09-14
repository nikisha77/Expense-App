import { api } from "./api.js";

const app = document.getElementById("app");

const state = {
  groups: [],
  activeGroupId: null,
  activeGroup: null, // { id, name, members }
  expenses: [],
  balances: [],
  settlements: [],
  tab: "expenses", // expenses | balances | settle
  selectedMemberIds: new Set(), // for new expense "split between"
  error: null,
};

function fmt(n) {
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function loadGroups() {
  state.groups = await api.listGroups();
  render();
}

async function selectGroup(id) {
  state.activeGroupId = id;
  state.error = null;
  state.tab = "expenses";
  await refreshActiveGroup();
}

async function refreshActiveGroup() {
  if (!state.activeGroupId) return;
  const [group, expenses, balances, settlements] = await Promise.all([
    api.getGroup(state.activeGroupId),
    api.listExpenses(state.activeGroupId),
    api.getBalances(state.activeGroupId),
    api.getSettleUp(state.activeGroupId),
  ]);
  state.activeGroup = group;
  state.expenses = expenses;
  state.balances = balances;
  state.settlements = settlements;
  state.selectedMemberIds = new Set(group.members.map((m) => m.id));
  render();
}

async function withErrorHandling(fn) {
  try {
    state.error = null;
    await fn();
  } catch (e) {
    state.error = e.message;
    render();
  }
}

function render() {
  app.innerHTML = "";
  app.appendChild(renderBrand());
  if (state.error) app.appendChild(renderError());

  const layout = document.createElement("div");
  layout.style.display = "grid";
  layout.style.gridTemplateColumns = "220px 1fr";
  layout.style.gap = "24px";
  layout.appendChild(renderSidebar());
  layout.appendChild(renderMain());
  app.appendChild(layout);
}

function renderBrand() {
  const div = document.createElement("div");
  div.className = "brand";
  div.innerHTML = `
    <h1>Splitzy</h1>
    <span class="tagline">Split expenses, settle up, move on.</span>
  `;
  return div;
}

function renderError() {
  const div = document.createElement("div");
  div.className = "error-banner";
  div.textContent = state.error;
  return div;
}

function renderSidebar() {
  const panel = document.createElement("div");
  panel.className = "panel";

  const heading = document.createElement("h3");
  heading.textContent = "Groups";
  heading.style.marginBottom = "14px";
  heading.style.fontSize = "16px";
  panel.appendChild(heading);

  const list = document.createElement("div");
  list.className = "group-list";
  if (state.groups.length === 0) {
    const empty = document.createElement("div");
    empty.style.fontSize = "13px";
    empty.style.color = "var(--ink-soft)";
    empty.textContent = "No groups yet.";
    list.appendChild(empty);
  }
  state.groups.forEach((g) => {
    const item = document.createElement("div");
    item.className = "group-item" + (g.id === state.activeGroupId ? " active" : "");
    item.textContent = g.name;
    item.onclick = () => withErrorHandling(() => selectGroup(g.id));
    list.appendChild(item);
  });
  panel.appendChild(list);

  const form = document.createElement("div");
  form.style.marginTop = "16px";
  form.innerHTML = `
    <label class="field-label">New group</label>
    <div class="row">
      <input id="new-group-name" placeholder="e.g. Goa Trip" style="flex:1" />
    </div>
    <button id="create-group-btn" style="margin-top:8px; width:100%">Create group</button>
  `;
  panel.appendChild(form);

  panel.querySelector("#create-group-btn").onclick = () =>
    withErrorHandling(async () => {
      const input = panel.querySelector("#new-group-name");
      const name = input.value.trim();
      if (!name) return;
      const group = await api.createGroup(name);
      await loadGroups();
      await selectGroup(group.id);
    });

  return panel;
}

function renderMain() {
  const wrap = document.createElement("div");

  if (!state.activeGroup) {
    const panel = document.createElement("div");
    panel.className = "panel empty-state";
    panel.textContent = "Create or select a group to get started.";
    wrap.appendChild(panel);
    return wrap;
  }

  wrap.appendChild(renderMembersPanel());
  wrap.appendChild(renderTabs());
  wrap.appendChild(renderTabContent());
  return wrap;
}

function renderMembersPanel() {
  const panel = document.createElement("div");
  panel.className = "panel";

  const h = document.createElement("h3");
  h.style.fontSize = "16px";
  h.style.marginBottom = "12px";
  h.textContent = state.activeGroup.name;
  panel.appendChild(h);

  const row = document.createElement("div");
  row.className = "row";
  state.activeGroup.members.forEach((m) => {
    const chip = document.createElement("span");
    chip.className = "member-chip";
    chip.textContent = m.name;
    row.appendChild(chip);
  });
  panel.appendChild(row);

  const addRow = document.createElement("div");
  addRow.className = "row";
  addRow.style.marginTop = "12px";
  addRow.innerHTML = `
    <input id="new-member-name" placeholder="Add member name" />
    <button class="secondary" id="add-member-btn">Add member</button>
  `;
  panel.appendChild(addRow);

  addRow.querySelector("#add-member-btn").onclick = () =>
    withErrorHandling(async () => {
      const input = addRow.querySelector("#new-member-name");
      const name = input.value.trim();
      if (!name) return;
      await api.addMember(state.activeGroupId, name);
      await refreshActiveGroup();
    });

  return panel;
}

function renderTabs() {
  const tabs = document.createElement("div");
  tabs.className = "tabs";
  [
    ["expenses", "Expenses"],
    ["balances", "Balances"],
    ["settle", "Settle up"],
  ].forEach(([key, label]) => {
    const tab = document.createElement("div");
    tab.className = "tab" + (state.tab === key ? " active" : "");
    tab.textContent = label;
    tab.onclick = () => {
      state.tab = key;
      render();
    };
    tabs.appendChild(tab);
  });
  return tabs;
}

function renderTabContent() {
  if (state.tab === "expenses") return renderExpensesTab();
  if (state.tab === "balances") return renderBalancesTab();
  return renderSettleTab();
}

function renderExpensesTab() {
  const wrap = document.createElement("div");

  const formPanel = document.createElement("div");
  formPanel.className = "panel";
  const members = state.activeGroup.members;

  formPanel.innerHTML = `<h3 style="font-size:16px; margin-bottom:14px;">Add expense</h3>`;

  const row1 = document.createElement("div");
  row1.className = "row";
  row1.innerHTML = `
    <div class="field">
      <label class="field-label">Description</label>
      <input id="exp-desc" placeholder="Dinner" style="width:220px" />
    </div>
    <div class="field">
      <label class="field-label">Amount</label>
      <input id="exp-amount" type="number" step="0.01" placeholder="0.00" style="width:120px" />
    </div>
    <div class="field">
      <label class="field-label">Paid by</label>
      <select id="exp-paid-by">
        ${members.map((m) => `<option value="${m.id}">${m.name}</option>`).join("")}
      </select>
    </div>
  `;
  formPanel.appendChild(row1);

  const splitLabel = document.createElement("label");
  splitLabel.className = "field-label";
  splitLabel.style.marginTop = "12px";
  splitLabel.style.display = "block";
  splitLabel.textContent = "Split equally between";
  formPanel.appendChild(splitLabel);

  const chipsRow = document.createElement("div");
  chipsRow.className = "row";
  members.forEach((m) => {
    const chip = document.createElement("span");
    chip.className = "member-chip" + (state.selectedMemberIds.has(m.id) ? " selected" : "");
    chip.textContent = m.name;
    chip.onclick = () => {
      if (state.selectedMemberIds.has(m.id)) state.selectedMemberIds.delete(m.id);
      else state.selectedMemberIds.add(m.id);
      render();
    };
    chipsRow.appendChild(chip);
  });
  formPanel.appendChild(chipsRow);

  const submitRow = document.createElement("div");
  submitRow.style.marginTop = "16px";
  const submitBtn = document.createElement("button");
  submitBtn.textContent = "Add expense";
  submitBtn.disabled = members.length === 0;
  submitBtn.onclick = () =>
    withErrorHandling(async () => {
      const desc = formPanel.querySelector("#exp-desc").value.trim();
      const amount = parseFloat(formPanel.querySelector("#exp-amount").value);
      const paidBy = parseInt(formPanel.querySelector("#exp-paid-by").value, 10);
      const memberIds = Array.from(state.selectedMemberIds);
      if (!desc || !amount || amount <= 0 || memberIds.length === 0) {
        state.error = "Fill in description, a positive amount, and at least one person to split with.";
        render();
        return;
      }
      await api.addExpense(state.activeGroupId, {
        description: desc,
        amount,
        paid_by_member_id: paidBy,
        member_ids: memberIds,
      });
      await refreshActiveGroup();
    });
  submitRow.appendChild(submitBtn);
  formPanel.appendChild(submitRow);

  wrap.appendChild(formPanel);

  const listPanel = document.createElement("div");
  listPanel.className = "panel";
  if (state.expenses.length === 0) {
    listPanel.innerHTML = `<div class="empty-state">No expenses yet. Add the first one above.</div>`;
  } else {
    const memberName = (id) => members.find((m) => m.id === id)?.name || "?";
    const rows = state.expenses
      .slice()
      .reverse()
      .map(
        (e) => `
      <tr>
        <td>${e.description}</td>
        <td>${memberName(e.paid_by_member_id)}</td>
        <td class="amount">${fmt(e.amount)}</td>
      </tr>`
      )
      .join("");
    listPanel.innerHTML = `
      <table>
        <thead><tr><th>Description</th><th>Paid by</th><th>Amount</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }
  wrap.appendChild(listPanel);

  return wrap;
}

function renderBalancesTab() {
  const panel = document.createElement("div");
  panel.className = "panel";
  if (state.balances.length === 0) {
    panel.innerHTML = `<div class="empty-state">No balances yet.</div>`;
    return panel;
  }
  const rows = state.balances
    .map((b) => {
      const cls = b.balance > 0 ? "balance-owed" : b.balance < 0 ? "balance-owe" : "";
      const text =
        b.balance > 0 ? `is owed ${fmt(b.balance)}` : b.balance < 0 ? `owes ${fmt(-b.balance)}` : "settled up";
      return `<tr><td>${b.name}</td><td class="amount ${cls}">${text}</td></tr>`;
    })
    .join("");
  panel.innerHTML = `
    <table>
      <thead><tr><th>Member</th><th>Balance</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  return panel;
}

function renderSettleTab() {
  const panel = document.createElement("div");
  panel.className = "panel";
  if (state.settlements.length === 0) {
    panel.innerHTML = `<div class="empty-state">Everyone's settled up. Nothing to pay.</div>`;
    return panel;
  }
  state.settlements.forEach((s) => {
    const line = document.createElement("div");
    line.className = "settle-line";
    line.innerHTML = `
      <span>${s.from_name}</span>
      <span class="arrow">&rarr; pays &rarr;</span>
      <span>${s.to_name}</span>
      <span class="amt">${fmt(s.amount)}</span>
    `;
    panel.appendChild(line);
  });
  return panel;
}

// initial load
withErrorHandling(loadGroups);
