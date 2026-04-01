const api =
  import.meta.env.DEV ? "" : "";

function headers() {
  const h = { "Content-Type": "application/json" };
  const t = localStorage.getItem("token");
  if (t) h["Authorization"] = `Bearer ${t}`;
  return h;
}

async function req(path, opts = {}) {
  const r = await fetch(`${api}${path}`, {
    ...opts,
    headers: { ...headers(), ...opts.headers },
  });
  const text = await r.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!r.ok) {
    const msg =
      data?.detail ??
      (Array.isArray(data?.detail) ? JSON.stringify(data.detail) : r.statusText);
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
}

function setErr(id, e) {
  document.getElementById(id).textContent = e?.message || String(e);
}

function clearErrs() {
  ["authErr", "addErr", "listErr", "sumErr"].forEach((id) => {
    document.getElementById(id).textContent = "";
  });
}

document.getElementById("btnReg").onclick = async () => {
  clearErrs();
  try {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;
    await req("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password, role }),
    });
    alert("Registered — now login");
  } catch (e) {
    setErr("authErr", e);
  }
};

document.getElementById("btnLogin").onclick = async () => {
  clearErrs();
  try {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const data = await req("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    localStorage.setItem("token", data.access_token);
    await refreshList();
  } catch (e) {
    setErr("authErr", e);
  }
};

document.getElementById("btnLogout").onclick = () => {
  localStorage.removeItem("token");
  clearErrs();
  document.getElementById("tbody").innerHTML = "";
  document.getElementById("totalLbl").textContent = "";
};

document.getElementById("btnAdd").onclick = async () => {
  clearErrs();
  try {
    const amount = parseFloat(document.getElementById("amt").value);
    const type = document.getElementById("typ").value;
    const category = document.getElementById("cat").value.trim();
    const date = document.getElementById("dt").value;
    const note = document.getElementById("note").value.trim() || null;
    await req("/transactions", {
      method: "POST",
      body: JSON.stringify({ amount, type, category, date, note }),
    });
    document.getElementById("amt").value = "";
    document.getElementById("note").value = "";
    await refreshList();
  } catch (e) {
    setErr("addErr", e);
  }
};

async function refreshList() {
  clearErrs();
  try {
    const data = await req("/transactions");
    const tbody = document.getElementById("tbody");
    tbody.innerHTML = "";
    document.getElementById("totalLbl").textContent = `(total: ${data.total})`;
    for (const row of data.items) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${row.id}</td><td>${row.date}</td><td>${row.type}</td><td>${row.category}</td><td>${row.amount}</td><td>${row.note || ""}</td>`;
      tbody.appendChild(tr);
    }
  } catch (e) {
    setErr("listErr", e);
  }
}

document.getElementById("btnRefresh").onclick = refreshList;

document.getElementById("btnSumV").onclick = async () => {
  clearErrs();
  try {
    const data = await req("/summary/viewer");
    document.getElementById("sumOut").textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    setErr("sumErr", e);
  }
};

document.getElementById("btnSumA").onclick = async () => {
  clearErrs();
  try {
    const data = await req("/summary");
    document.getElementById("sumOut").textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    setErr("sumErr", e);
  }
};

document.getElementById("dt").valueAsDate = new Date();

refreshList().catch(() => {});
