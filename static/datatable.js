/* Tabel data: sorting per kolom (klik judul), pencarian semua kolom, dan pagination dinamis.
   Pakai: <table class="table dt" data-per-page="10">. Kolom tanpa judul atau data-nosort tidak bisa diurutkan. */
(function () {
  "use strict";
  const PAGE_SIZES = [5, 10, 25, 50, 100, 0]; // 0 = semua
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* abaikan */ } }
  };

  function cellValue(td) {
    if (!td) return "";
    const f = td.querySelector("select, input:not([type=hidden]):not([type=checkbox])");
    if (f) return f.tagName === "SELECT" ? (f.selectedOptions[0] || {}).text || "" : f.value;
    return (td.dataset.sort ?? td.textContent).trim();
  }

  function asNumber(s) {
    const t = s.replace(/^CR\s*/i, "").replace(/%$/, "").trim();
    if (/^-?\d+(\.\d+)?$/.test(t)) return parseFloat(t);
    const fr = t.match(/^(\d+)\/(\d+)$/);
    return fr ? parseInt(fr[1], 10) / parseInt(fr[2], 10) : null;
  }

  function enhance(table, idx) {
    // pastikan baris judul ada di <thead>
    let thead = table.tHead;
    if (!thead) {
      const first = table.querySelector("tr");
      if (!first || !first.querySelector("th")) return;
      thead = table.createTHead();
      thead.appendChild(first);
    }
    const head = thead.rows[thead.rows.length - 1];
    const body = table.tBodies[0] || table.createTBody();
    [...table.tBodies].slice(1).forEach(tb => { [...tb.rows].forEach(r => body.appendChild(r)); tb.remove(); });
    let rows = [...body.rows];
    const nCols = head.cells.length;
    // baris "tidak ada data" (satu sel colspan) dibiarkan apa adanya
    if (rows.length === 1 && rows[0].cells.length === 1 && rows[0].cells[0].colSpan > 1) return;
    rows.forEach((r, i) => { r.dataset.dtIndex = i; });

    const key = "dt:" + location.pathname + ":" + (table.id || idx);
    const saved = store.get(key) || {};
    const state = {
      q: "", page: 1,
      size: PAGE_SIZES.includes(saved.size) ? saved.size : parseInt(table.dataset.perPage || "10", 10),
      col: Number.isInteger(saved.col) && saved.col < nCols ? saved.col : null,
      dir: saved.dir === -1 ? -1 : 1
    };

    // ---- toolbar
    const uid = "dt" + idx + "-" + Math.random().toString(36).slice(2, 7);
    const bar = document.createElement("div");
    bar.className = "dt-bar d-flex flex-wrap align-items-center gap-2 mb-2";
    bar.innerHTML =
      `<label class="d-flex align-items-center gap-1 small mb-0" for="${uid}-size">Tampilkan
         <select class="form-select form-select-sm" id="${uid}-size" style="width:auto">${PAGE_SIZES.map(n =>
        `<option value="${n}" ${n === state.size ? "selected" : ""}>${n || "Semua"}</option>`).join("")}</select> baris</label>
       <div class="ms-auto position-relative">
         <input type="search" class="form-control form-control-sm" id="${uid}-q" placeholder="Cari di semua kolom…" aria-label="Cari di tabel" style="min-width:220px">
       </div>`;
    // toolbar di luar pembungkus scroll, kecuali pembungkusnya adalah card-body (agar tetap ber-padding)
    const resp = table.closest(".table-responsive");
    const wrap = resp && !resp.classList.contains("card-body") ? resp : table;
    wrap.parentNode.insertBefore(bar, wrap);
    const foot = document.createElement("div");
    foot.className = "dt-foot d-flex flex-wrap align-items-center gap-2 mt-2 small";
    wrap.parentNode.insertBefore(foot, wrap.nextSibling);
    const sizeSel = bar.querySelector("select"), qInp = bar.querySelector("input");

    // ---- judul kolom yang bisa diurutkan
    const sortable = [...head.cells].map((th, c) => {
      const ok = th.textContent.trim() !== "" && !("nosort" in th.dataset) && th.colSpan === 1;
      if (ok) {
        th.classList.add("dt-sortable");
        th.tabIndex = 0;
        th.setAttribute("role", "button");
        th.title = th.title || "Klik untuk mengurutkan";
        const go = () => { state.dir = state.col === c ? -state.dir : 1; state.col = c; state.page = 1; render(); };
        th.addEventListener("click", go);
        th.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
      }
      return ok;
    });

    function filtered() {
      const q = state.q.toLowerCase();
      let list = rows.filter(r => !q || [...r.cells].some(td => cellValue(td).toLowerCase().includes(q)));
      if (state.col !== null && sortable[state.col]) {
        const c = state.col, d = state.dir;
        list = list.slice().sort((a, b) => {
          const va = cellValue(a.cells[c]), vb = cellValue(b.cells[c]);
          const na = asNumber(va), nb = asNumber(vb);
          if (na !== null && nb !== null) return (na - nb) * d || a.dataset.dtIndex - b.dataset.dtIndex;
          return va.localeCompare(vb, "id", { numeric: true, sensitivity: "base" }) * d || a.dataset.dtIndex - b.dataset.dtIndex;
        });
      } else {
        list = list.slice().sort((a, b) => a.dataset.dtIndex - b.dataset.dtIndex);
      }
      return list;
    }

    function pageButtons(cur, total) {
      const set = new Set([1, total, cur - 1, cur, cur + 1, cur - 2, cur + 2].filter(p => p >= 1 && p <= total));
      const list = [...set].sort((a, b) => a - b), out = [];
      list.forEach((p, i) => { if (i && p - list[i - 1] > 1) out.push("…"); out.push(p); });
      return out;
    }

    function render() {
      const list = filtered(), total = list.length;
      const size = state.size || total || 1, pages = Math.max(1, Math.ceil(total / size));
      state.page = Math.min(Math.max(1, state.page), pages);
      const start = (state.page - 1) * size, shown = list.slice(start, start + size);
      body.replaceChildren(...list);
      rows.forEach(r => { r.hidden = true; });
      shown.forEach(r => { r.hidden = false; });
      let empty = body.querySelector(".dt-empty");
      if (!total) {
        if (!empty) { empty = body.insertRow(); empty.className = "dt-empty"; const td = empty.insertCell(); td.colSpan = nCols; td.className = "text-muted text-center"; }
        empty.cells[0].textContent = `Tidak ada data yang cocok dengan "${state.q}".`;
        empty.hidden = false;
      } else if (empty) { empty.remove(); }
      [...head.cells].forEach((th, c) => {
        th.classList.toggle("dt-asc", c === state.col && state.dir === 1);
        th.classList.toggle("dt-desc", c === state.col && state.dir === -1);
        if (sortable[c]) th.setAttribute("aria-sort", c === state.col ? (state.dir === 1 ? "ascending" : "descending") : "none");
      });
      const from = total ? start + 1 : 0, to = Math.min(start + size, total);
      const btn = (label, p, dis, act, aria) =>
        `<li class="page-item ${dis ? "disabled" : ""} ${act ? "active" : ""}"><button type="button" class="page-link" data-p="${p}" ${dis ? "tabindex=-1" : ""} aria-label="${aria || "Halaman " + p}" ${act ? 'aria-current="page"' : ""}>${label}</button></li>`;
      foot.innerHTML =
        `<span class="text-muted">Menampilkan ${from}–${to} dari ${total} baris${state.q ? ` (disaring dari ${rows.length})` : ""}</span>
         <nav class="ms-auto" aria-label="Navigasi halaman tabel"><ul class="pagination pagination-sm mb-0">
          ${btn("«", 1, state.page === 1, false, "Halaman pertama")}${btn("‹", state.page - 1, state.page === 1, false, "Halaman sebelumnya")}
          ${pageButtons(state.page, pages).map(p => p === "…" ? '<li class="page-item disabled"><span class="page-link">…</span></li>' : btn(p, p, false, p === state.page)).join("")}
          ${btn("›", state.page + 1, state.page === pages, false, "Halaman berikutnya")}${btn("»", pages, state.page === pages, false, "Halaman terakhir")}
         </ul></nav>
         <label class="d-flex align-items-center gap-1 mb-0" for="${uid}-go">Ke halaman
          <input type="number" class="form-control form-control-sm" id="${uid}-go" min="1" max="${pages}" value="${state.page}" style="width:70px"> / ${pages}</label>`;
      store.set(key, { size: state.size, col: state.col, dir: state.dir });
    }

    foot.addEventListener("click", e => {
      const b = e.target.closest("button[data-p]");
      if (b && !b.closest(".disabled")) { state.page = parseInt(b.dataset.p, 10); render(); }
    });
    foot.addEventListener("change", e => {
      if (e.target.type === "number") { state.page = parseInt(e.target.value, 10) || 1; render(); }
    });
    sizeSel.addEventListener("change", () => { state.size = parseInt(sizeSel.value, 10); state.page = 1; render(); });
    let t;
    qInp.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { state.q = qInp.value.trim(); state.page = 1; render(); }, 150); });
    render();
  }

  document.addEventListener("DOMContentLoaded", () => document.querySelectorAll("table.dt").forEach(enhance));
})();
