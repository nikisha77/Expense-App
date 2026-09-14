// All backend calls live here. This is the ONE place the UI talks to a
// server, so swapping mock <-> real backend never touches component code.

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ? JSON.stringify(body.detail) : `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  listGroups: () => request("/groups"),
  createGroup: (name) => request("/groups", { method: "POST", body: JSON.stringify({ name }) }),
  getGroup: (id) => request(`/groups/${id}`),
  addMember: (groupId, name) =>
    request(`/groups/${groupId}/members`, { method: "POST", body: JSON.stringify({ name }) }),
  listExpenses: (groupId) => request(`/groups/${groupId}/expenses`),
  addExpense: (groupId, payload) =>
    request(`/groups/${groupId}/expenses`, { method: "POST", body: JSON.stringify(payload) }),
  getBalances: (groupId) => request(`/groups/${groupId}/balances`),
  getSettleUp: (groupId) => request(`/groups/${groupId}/settle-up`),
};
