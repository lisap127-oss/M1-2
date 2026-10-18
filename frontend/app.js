// ===== 학습 코치 프론트엔드 로직 (바닐라 JS) =====
const API = window.API_BASE_URL;

// 현재 열려있는 대화 ID (없으면 새 대화)
let currentConversationId = null;

// ---- DOM ----
const $ = (id) => document.getElementById(id);
const messagesEl = $("messages");
const chatForm = $("chatForm");
const chatInput = $("chatInput");
const sendBtn = $("sendBtn");
const convListEl = $("conversationList");
const chatTitleEl = $("chatTitle");

// ---------------------------------------------------------------
// 공통 유틸
// ---------------------------------------------------------------
function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2200);
}

async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (e) {}
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

// ---------------------------------------------------------------
// 채팅
// ---------------------------------------------------------------
function clearWelcome() {
  const w = messagesEl.querySelector(".welcome");
  if (w) w.remove();
}

function addMessage(role, content) {
  clearWelcome();
  const wrap = document.createElement("div");
  wrap.className = "msg " + (role === "user" ? "user" : "ai");
  wrap.innerHTML = `
    <div class="avatar">${role === "user" ? "🙂" : "🎓"}</div>
    <div class="bubble"></div>`;
  wrap.querySelector(".bubble").textContent = content;
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

function addTyping() {
  clearWelcome();
  const wrap = document.createElement("div");
  wrap.className = "msg ai";
  wrap.innerHTML = `
    <div class="avatar">🎓</div>
    <div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>`;
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

async function sendChat(message) {
  addMessage("user", message);
  const typing = addTyping();
  sendBtn.disabled = true;
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        conversation_id: currentConversationId,
      }),
    });
    typing.remove();
    addMessage("assistant", data.reply);
    // 새 대화였다면 ID를 기억하고 목록 갱신
    if (!currentConversationId) {
      currentConversationId = data.conversation_id;
      await loadConversations();
      setActiveConversation(currentConversationId);
    }
  } catch (err) {
    typing.remove();
    addMessage("assistant", "⚠️ 오류가 발생했어요: " + err.message);
    toast("요청 실패: " + err.message);
  } finally {
    sendBtn.disabled = false;
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const msg = chatInput.value.trim();
  if (!msg) return;
  chatInput.value = "";
  sendChat(msg);
});

// 추천 질문 칩
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("chip")) {
    chatInput.value = e.target.textContent;
    chatForm.dispatchEvent(new Event("submit"));
  }
});

// 새 대화
$("newChatBtn").addEventListener("click", () => {
  currentConversationId = null;
  chatTitleEl.textContent = "새 대화";
  messagesEl.innerHTML = `
    <div class="welcome">
      <h3>무엇이든 물어보세요</h3>
      <p>내 학습 시간 데이터를 바탕으로 답해드려요.</p>
      <div class="chips">
        <button class="chip">이번 주 공부 어땠어?</button>
        <button class="chip">가장 많이 공부한 날은?</button>
        <button class="chip">요즘 추세가 어때?</button>
      </div>
    </div>`;
  setActiveConversation(null);
});

// ---------------------------------------------------------------
// 대화 기록
// ---------------------------------------------------------------
async function loadConversations() {
  try {
    const list = await api("/api/conversations");
    if (!list.length) {
      convListEl.innerHTML = `<li class="empty-hint">아직 저장된 대화가 없어요.</li>`;
      return;
    }
    convListEl.innerHTML = "";
    list.forEach((c) => {
      const li = document.createElement("li");
      li.className = "conv";
      li.dataset.id = c.id;
      li.innerHTML = `<span class="conv-title">${escapeHtml(c.title)}</span>
                      <button class="conv-del" title="삭제">✕</button>`;
      li.querySelector(".conv-title").addEventListener("click", () => openConversation(c.id, c.title));
      li.querySelector(".conv-del").addEventListener("click", (e) => {
        e.stopPropagation();
        deleteConversation(c.id);
      });
      convListEl.appendChild(li);
    });
    if (currentConversationId) setActiveConversation(currentConversationId);
  } catch (err) {
    toast("대화 목록 로드 실패: " + err.message);
  }
}

async function openConversation(id, title) {
  try {
    const conv = await api("/api/conversations/" + id);
    currentConversationId = id;
    chatTitleEl.textContent = title || conv.title || "대화";
    messagesEl.innerHTML = "";
    conv.messages
      .filter((m) => m.role !== "system")
      .forEach((m) => addMessage(m.role, m.content));
    setActiveConversation(id);
  } catch (err) {
    toast("대화 불러오기 실패: " + err.message);
  }
}

async function deleteConversation(id) {
  if (!confirm("이 대화를 삭제할까요?")) return;
  try {
    await api("/api/conversations/" + id, { method: "DELETE" });
    if (currentConversationId === id) $("newChatBtn").click();
    await loadConversations();
    toast("대화를 삭제했어요.");
  } catch (err) {
    toast("삭제 실패: " + err.message);
  }
}

function setActiveConversation(id) {
  document.querySelectorAll(".conv-list li.conv").forEach((li) => {
    li.classList.toggle("active", li.dataset.id === id);
  });
}

// ---------------------------------------------------------------
// 데이터 요약 + 차트
// ---------------------------------------------------------------
let trendChart = null;

async function loadSummary() {
  const body = $("summaryBody");
  try {
    const s = await api("/api/data/summary");
    const trend = s.trend || "";
    let cls = "trend-flat";
    if (trend.includes("상승")) cls = "trend-up";
    else if (trend.includes("하락")) cls = "trend-down";

    body.innerHTML = `
      <div class="sum-row"><span class="k">기간</span><span class="v">${s.period}</span></div>
      <div class="sum-row"><span class="k">기록 수</span><span class="v">${s.count}개</span></div>
      <div class="sum-row"><span class="k">최근 추세</span>
        <span class="trend-badge ${cls}">${trend}</span></div>
      <div class="metric-grid">
        <div class="metric"><div class="label">총 시간(분)</div><div class="num">${s.metrics.total}</div></div>
        <div class="metric"><div class="label">일 평균(분)</div><div class="num">${s.metrics.average}</div></div>
        <div class="metric"><div class="label">최대(분)</div><div class="num">${s.metrics.max}</div></div>
        <div class="metric"><div class="label">최소(분)</div><div class="num">${s.metrics.min}</div></div>
      </div>`;
  } catch (err) {
    body.innerHTML = `<p class="muted">요약을 불러오지 못했어요. (${escapeHtml(err.message)})</p>`;
  }
}

async function loadChart() {
  try {
    const stats = await api("/api/data/statistics");
    if (!stats.series || !stats.series.length) return;
    const labels = stats.series.map((p) => p.date);
    const values = stats.series.map((p) => p.value);
    const ma = (stats.moving_average_7 || []).map((p) => p.value);

    const style = getComputedStyle(document.body);
    const primary = style.getPropertyValue("--primary").trim();
    const muted = style.getPropertyValue("--muted").trim();

    if (trendChart) trendChart.destroy();
    trendChart = new Chart($("trendChart"), {
      type: "line",
      data: {
        labels,
        datasets: [
          { label: "일별(분)", data: values, borderColor: primary,
            backgroundColor: "transparent", borderWidth: 1.4, pointRadius: 0, tension: .25 },
          { label: "7일 이동평균", data: ma, borderColor: muted,
            borderDash: [5, 4], backgroundColor: "transparent", borderWidth: 1.4, pointRadius: 0, tension: .25 },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { boxWidth: 12, font: { size: 11 } } } },
        scales: {
          x: { ticks: { maxTicksLimit: 6, font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { font: { size: 10 } }, grid: { color: "rgba(128,128,128,.12)" } },
        },
      },
    });
  } catch (err) {
    /* 차트는 부가 기능이라 조용히 실패 */
  }
}

// ---------------------------------------------------------------
// 데이터 관리 (CRUD)
// ---------------------------------------------------------------
async function loadDataTable() {
  const tbody = $("dataTableBody");
  try {
    const items = await api("/api/data");
    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="muted">데이터가 없어요. 위에서 추가해보세요.</td></tr>`;
      return;
    }
    // 최근 것이 위로 오도록 역순 표시
    tbody.innerHTML = "";
    items.slice().reverse().forEach((it) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${it.date}</td>
        <td>${it.value}</td>
        <td>${escapeHtml(it.memo || "")}</td>
        <td><button class="row-del" title="삭제">✕</button></td>`;
      tr.querySelector(".row-del").addEventListener("click", () => deleteDataRow(it.id));
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="muted">로드 실패: ${escapeHtml(err.message)}</td></tr>`;
  }
}

$("dataForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    date: $("d_date").value,
    value: Number($("d_value").value),
    memo: $("d_memo").value.trim(),
  };
  try {
    await api("/api/data", { method: "POST", body: JSON.stringify(payload) });
    $("dataForm").reset();
    toast("데이터를 추가했어요.");
    await Promise.all([loadDataTable(), loadSummary(), loadChart()]);
  } catch (err) {
    toast("추가 실패: " + err.message);
  }
});

async function deleteDataRow(id) {
  try {
    await api("/api/data/" + id, { method: "DELETE" });
    toast("데이터를 삭제했어요.");
    await Promise.all([loadDataTable(), loadSummary(), loadChart()]);
  } catch (err) {
    toast("삭제 실패: " + err.message);
  }
}

// ---------------------------------------------------------------
// CSV 내보내기 (보너스)
// ---------------------------------------------------------------
$("exportCsv").addEventListener("click", async () => {
  try {
    const items = await api("/api/data");
    if (!items.length) return toast("내보낼 데이터가 없어요.");
    const header = "date,value,memo\n";
    const rows = items.map((it) => `${it.date},${it.value},"${(it.memo || "").replace(/"/g, '""')}"`).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "study_time.csv";
    a.click();
    URL.revokeObjectURL(url);
    toast("CSV를 내보냈어요.");
  } catch (err) {
    toast("내보내기 실패: " + err.message);
  }
});

// ---------------------------------------------------------------
// 다크 모드 (보너스)
// ---------------------------------------------------------------
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  $("themeIcon").textContent = theme === "dark" ? "☀️" : "🌙";
  $("themeLabel").textContent = theme === "dark" ? "라이트 모드" : "다크 모드";
  try { localStorage.setItem("theme", theme); } catch (e) {}
  loadChart(); // 차트 색상 갱신
}
$("themeToggle").addEventListener("click", () => {
  const cur = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  applyTheme(cur === "dark" ? "light" : "dark");
});

// ---------------------------------------------------------------
// 기타
// ---------------------------------------------------------------
function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

$("refreshSummary").addEventListener("click", () => { loadSummary(); loadChart(); });

// ---------------------------------------------------------------
// 초기화
// ---------------------------------------------------------------
(function init() {
  let saved = "light";
  try { saved = localStorage.getItem("theme") || "light"; } catch (e) {}
  applyTheme(saved);

  // 오늘 날짜 기본값
  $("d_date").value = new Date().toISOString().slice(0, 10);

  loadConversations();
  loadSummary();
  loadChart();
  loadDataTable();
})();
