# app.py (Streamlit SaaS Panel) — FINAL
import os
import time
import random
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

# =========================
# CONFIG
# =========================
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(
    page_title="Viper Vegas Engine",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# THEME / CSS (SaaS Dark)
# =========================
CSS = """
<style>
html, body, [class*="css"]  { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
.block-container { padding-top: 1.1rem; padding-bottom: 2rem; max-width: 1500px; }

/* ---- cards ---- */
.vv-card {
  background: radial-gradient(1200px 600px at 10% 10%, rgba(56,189,248,0.10), rgba(0,0,0,0)),
              radial-gradient(900px 500px at 90% 10%, rgba(34,197,94,0.08), rgba(0,0,0,0)),
              linear-gradient(180deg, rgba(15,23,42,0.88), rgba(2,6,23,0.88));
  border: 1px solid rgba(148,163,184,0.16);
  border-radius: 18px;
  padding: 14px 14px;
  box-shadow: 0 12px 36px rgba(0,0,0,0.35);
}
.vv-header {
  display:flex; align-items:center; justify-content:space-between;
  gap: 12px; margin-bottom: 8px;
}
.vv-title { font-size: 28px; font-weight: 900; letter-spacing: 0.2px; }
.vv-sub { color: rgba(226,232,240,0.72); font-size: 12px; margin-top: -3px; }

.vv-badge {
  display:inline-flex; align-items:center; gap:8px;
  padding: 7px 11px; border-radius: 999px;
  border: 1px solid rgba(148,163,184,0.18);
  background: rgba(2,6,23,0.45);
  color: rgba(226,232,240,0.82);
  font-size: 12px;
}
.vv-dot { width:8px; height:8px; border-radius:999px; display:inline-block; }
.vv-dot.ok { background:#22c55e; box-shadow: 0 0 12px rgba(34,197,94,.6); }
.vv-dot.bad { background:#ef4444; box-shadow: 0 0 12px rgba(239,68,68,.6); }

/* ---- metrics ---- */
.vv-metrics {
  display:grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}
.vv-tile {
  background: rgba(2,6,23,0.60);
  border: 1px solid rgba(148,163,184,0.12);
  border-radius: 14px;
  padding: 10px 12px;
}
.vv-tile .k { color: rgba(226,232,240,0.70); font-size: 12px; }
.vv-tile .v { font-size: 20px; font-weight: 900; margin-top: 3px; }

.vv-green { color: #22c55e; }
.vv-red { color: #ef4444; }
.vv-yellow { color: #f59e0b; }
.vv-blue { color: #38bdf8; }
.vv-muted { color: rgba(226,232,240,0.72); }

/* ---- alert pulse ---- */
.vv-alert {
  border-radius: 18px;
  padding: 14px 14px;
  border: 1px solid rgba(239,68,68,0.36);
  background: linear-gradient(180deg, rgba(239,68,68,0.22), rgba(2,6,23,0.58));
  position: relative;
  overflow: hidden;
  margin-top: 12px;
}
.vv-alert::after{
  content:"";
  position:absolute; inset:-45%;
  background: radial-gradient(circle at 30% 30%, rgba(239,68,68,0.40), rgba(0,0,0,0));
  animation: vvPulse 1.4s ease-in-out infinite;
}
@keyframes vvPulse{
  0%{ transform: scale(0.95); opacity: .35; }
  50%{ transform: scale(1.05); opacity: .68; }
  100%{ transform: scale(0.95); opacity: .35; }
}
.vv-alert-inner{ position: relative; z-index: 2; }
.vv-alert-title{ font-weight: 1000; font-size: 14px; letter-spacing: .3px; }
.vv-alert-body{ color: rgba(226,232,240,0.92); font-size: 13px; margin-top: 8px; line-height: 1.35; }

/* ---- status chip ---- */
.vv-chip {
  display:inline-flex;
  gap:8px;
  align-items:center;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(148,163,184,0.16);
  background: rgba(2,6,23,0.50);
  font-size: 12px;
}
.vv-chip b{ font-weight:900; }
.vv-pill-green{ color:#22c55e; }
.vv-pill-red{ color:#ef4444; }
.vv-pill-yellow{ color:#f59e0b; }
.vv-pill-blue{ color:#38bdf8; }
.vv-pill-muted{ color: rgba(226,232,240,0.75); }

/* ---- tabs ---- */
.stTabs [data-baseweb="tab-list"] { gap: 10px; }
.stTabs [data-baseweb="tab"] {
  background: rgba(2,6,23,0.42);
  border: 1px solid rgba(148,163,184,0.14);
  border-radius: 999px;
  padding: 8px 14px;
}
.stTabs [aria-selected="true"]{
  border-color: rgba(56,189,248,0.52) !important;
  box-shadow: 0 0 0 4px rgba(56,189,248,0.10);
}

/* ---- section ---- */
.vv-section-title {
  margin-top: 14px;
  font-size: 18px;
  font-weight: 1000;
  letter-spacing: .2px;
}

/* ---- code block nicer ---- */
pre { border-radius: 14px !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# =========================
# HELPERS (API)
# =========================
def api_get(path: str, timeout: float = 4.0) -> Optional[Any]:
    try:
        r = requests.get(f"{BACKEND_URL}{path}", timeout=timeout)
        if r.status_code >= 400:
            return None
        return r.json()
    except Exception:
        return None

def api_post(path: str, payload: Dict[str, Any], timeout: float = 7.0) -> Optional[Any]:
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=timeout)
        if r.status_code >= 400:
            return None
        return r.json()
    except Exception:
        return None

def parse_int(s: str) -> Optional[int]:
    s = (s or "").strip()
    if s == "":
        return None
    try:
        v = int(s)
        if 0 <= v <= 36:
            return v
        return None
    except Exception:
        return None

def normalize_history_item(x: Dict[str, Any]) -> Dict[str, Any]:
    numero = x.get("numero", x.get("n", x.get("value")))
    cor = x.get("cor", x.get("color"))
    padroes = x.get("padroes", x.get("padrao"))
    status = x.get("status", x.get("state", "ANALISE"))
    msg = x.get("mensagem", x.get("message", ""))

    entrada = x.get("entrada", None)
    entradas = x.get("entradas", x.get("entrada", None))

    score_terminal = x.get("score_terminal", 0.0)
    score_padrao = x.get("score_padrao", 0.0)
    score_combinado = x.get("score_combinado", 0.0)

    return {
        "time": x.get("time", x.get("timestamp", "")),
        "source": x.get("source", ""),
        "numero": numero,
        "cor": cor,
        "terminal": x.get("terminal"),
        "status": status,
        "padroes": padroes,
        "score_terminal": score_terminal,
        "score_padrao": score_padrao,
        "score_combinado": score_combinado,
        "mensagem": msg,
        "entrada": entrada,
        "entradas": entradas,
    }

def compute_stats_from_history(df: pd.DataFrame) -> Dict[str, int]:
    out = {"spins": 0, "entradas": 0, "greens": 0, "reds": 0, "blacks": 0, "gales": 0, "padroes": 0}
    if df is None or df.empty:
        return out

    out["spins"] = int(len(df))

    if "cor" in df.columns:
        out["greens"] = int((df["cor"] == "GREEN").sum())
        out["reds"] = int((df["cor"] == "RED").sum())
        out["blacks"] = int((df["cor"] == "BLACK").sum())

    if "status" in df.columns:
        out["gales"] = int((df["status"] == "GALE").sum())
        out["entradas"] = int((df["status"] == "ENTRADA").sum())

    if "padroes" in df.columns:
        out["padroes"] = int(df["padroes"].fillna("").astype(str).str.strip().ne("").sum())

    return out

def is_entry_payload(payload: Dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    return str(payload.get("status", "")).upper() == "ENTRADA" and isinstance(payload.get("entrada", None), dict)

def status_chip(status: str, cor: str) -> str:
    s = (status or "").upper().strip()
    c = (cor or "").upper().strip()

    if s == "ENTRADA":
        klass = "vv-pill-red"
    elif s == "GREEN":
        klass = "vv-pill-green"
    elif s == "RED":
        klass = "vv-pill-red"
    elif s == "GALE":
        klass = "vv-pill-yellow"
    else:
        klass = "vv-pill-muted"

    cor_klass = "vv-pill-muted"
    if c == "GREEN":
        cor_klass = "vv-pill-green"
    elif c == "RED":
        cor_klass = "vv-pill-red"
    elif c == "BLACK":
        cor_klass = "vv-pill-blue"

    return f"""
<div style="display:flex; gap:10px; flex-wrap:wrap;">
  <div class="vv-chip"><span class="{klass}">●</span> <b>Status:</b> {s or "-"} </div>
  <div class="vv-chip"><span class="{cor_klass}">●</span> <b>Cor:</b> {c or "-"} </div>
</div>
"""

# =========================
# SESSION STATE
# =========================
if "last_payload" not in st.session_state:
    st.session_state.last_payload = None
if "auto_running" not in st.session_state:
    st.session_state.auto_running = False
if "auto_last_sent_at" not in st.session_state:
    st.session_state.auto_last_sent_at = 0.0
if "auto_last_num" not in st.session_state:
    st.session_state.auto_last_num = None

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("## 🎰 Viper Vegas")
    modo = st.selectbox("Modo de operação", ["conservador", "normal", "agressivo"], index=1)

    st.markdown("---")
    auto = st.checkbox("Simulação automática", value=False)
    speed = st.slider("Velocidade (segundos)", 0.10, 3.00, 0.55, 0.05)

    st.markdown("---")
    st.caption("Backend URL")
    st.code(BACKEND_URL, language="")

# =========================
# HEADER
# =========================
health = api_get("/health")
online = bool(health and health.get("ok") is True)

st.markdown(
    f"""
<div class="vv-card">
  <div class="vv-header">
    <div>
      <div class="vv-title">🎰 Viper Vegas Engine</div>
      <div class="vv-sub">Painel SaaS — Streamlit consumindo FastAPI (análise e padrões)</div>
    </div>
    <div class="vv-badge">
      <span class="vv-dot {'ok' if online else 'bad'}"></span>
      <span><b>FastAPI</b>: {BACKEND_URL}</span>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# =========================
# INPUT (ENTER) + ACTIONS
# =========================
colA, colB = st.columns([3.2, 1.3], gap="large")

with colA:
    st.markdown('<div class="vv-card">', unsafe_allow_html=True)
    st.caption("Número da roleta (0–36) — pressione ENTER para enviar")

    # FORM = ENTER envia + clear_on_submit apaga o campo automaticamente ✅
    with st.form("send_form", clear_on_submit=True):
        raw = st.text_input(
            "Número",
            value="",
            placeholder="Digite e pressione ENTER…",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Enviar")

    st.markdown("</div>", unsafe_allow_html=True)

with colB:
    st.markdown('<div class="vv-card">', unsafe_allow_html=True)
    st.markdown("### Controles")
    st.markdown("- **ENTER** envia\n- Simulação envia números aleatórios\n- Alerta só aparece se backend retornar **ENTRADA**")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# SEND SPIN (manual)
# =========================
if submitted:
    n = parse_int(raw)
    if n is None:
        st.warning("Digite um número válido entre 0 e 36.")
    else:
        payload = {"numero": n, "modo": modo}
        data = api_post("/spin", payload)
        if not data:
            st.error("Falha ao enviar /spin. Verifique o backend.")
        else:
            st.session_state.last_payload = data

# =========================
# AUTO SIM (no duplicar / sem travar)
# =========================
st.session_state.auto_running = bool(auto)

if st.session_state.auto_running:
    now = time.time()
    # envia só se já passou "speed" desde o último envio
    if (now - float(st.session_state.auto_last_sent_at)) >= float(speed):
        n = random.randint(0, 36)
        # evita repetir o mesmo número seguido (ajuda no visual)
        if st.session_state.auto_last_num is not None and n == st.session_state.auto_last_num:
            n = (n + random.randint(1, 7)) % 37

        data = api_post("/spin", {"numero": int(n), "modo": modo})
        st.session_state.auto_last_sent_at = now
        st.session_state.auto_last_num = n
        if isinstance(data, dict):
            st.session_state.last_payload = data
        st.rerun()

# =========================
# FETCH HISTORY (always)
# =========================
hist_raw = api_get("/historico") or []
if isinstance(hist_raw, dict) and "items" in hist_raw:
    hist_raw = hist_raw["items"]
if not isinstance(hist_raw, list):
    hist_raw = []

df_hist = pd.DataFrame([normalize_history_item(x if isinstance(x, dict) else {}) for x in hist_raw])
stats = compute_stats_from_history(df_hist)

# =========================
# LAST STATUS CARD + ALERT
# =========================
last = st.session_state.last_payload

if isinstance(last, dict):
    st.markdown('<div class="vv-card" style="margin-top:12px;">', unsafe_allow_html=True)

    n = last.get("numero", "-")
    t = last.get("terminal", "-")
    c = last.get("cor", "-")
    stt = last.get("status", "ANALISE")
    msg = last.get("mensagem", "")

    st.markdown(f"### Último Spin: **{n}**  |  Terminal: **{t}**")
    st.markdown(status_chip(str(stt), str(c)), unsafe_allow_html=True)
    if msg:
        st.caption(msg)

    # ALERTA PROFISSIONAL (quando backend manda ENTRADA)
    if is_entry_payload(last):
        entrada = last.get("entrada", {}) or {}
        st.markdown(
            f"""
<div class="vv-alert">
  <div class="vv-alert-inner">
    <div class="vv-alert-title">🚨 ENTRADA IDENTIFICADA</div>
    <div class="vv-alert-body">
      <div><b>Estratégia:</b> {entrada.get("estrategia","-")}</div>
      <div><b>Terminal Previsto:</b> {entrada.get("terminal_previsto","-")}</div>
      <div><b>Padrão:</b> {entrada.get("padrao","-")}</div>
      <div><b>Gale Máx:</b> {entrada.get("gale_max","-")}</div>
      <div style="margin-top:10px;"><b>Números alvo:</b></div>
    </div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        numeros_alvo = entrada.get("numeros_alvo", [])
        if isinstance(numeros_alvo, list) and numeros_alvo:
            st.code("  ".join(map(str, numeros_alvo)))
        else:
            st.code("—")
    else:
        st.caption("Sem entrada ativa no momento.")

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.caption("Envie um spin para começar (ou ative simulação).")

# =========================
# METRICS
# =========================
st.markdown(
    f"""
<div class="vv-metrics">
  <div class="vv-tile"><div class="k">Spins</div><div class="v vv-blue">{stats.get('spins',0)}</div></div>
  <div class="vv-tile"><div class="k">Entradas</div><div class="v vv-yellow">{stats.get('entradas',0)}</div></div>
  <div class="vv-tile"><div class="k">Greens</div><div class="v vv-green">{stats.get('greens',0)}</div></div>
  <div class="vv-tile"><div class="k">Reds</div><div class="v vv-red">{stats.get('reds',0)}</div></div>
  <div class="vv-tile"><div class="k">Blacks</div><div class="v vv-blue">{stats.get('blacks',0)}</div></div>
  <div class="vv-tile"><div class="k">Padrões Detectados</div><div class="v vv-yellow">{stats.get('padroes',0)}</div></div>
</div>
""",
    unsafe_allow_html=True,
)

# =========================
# TABS
# =========================
tab_hist, tab_heat, tab_scores, tab_debug = st.tabs(
    ["📜 Histórico", "🔥 Heatmaps", "📈 Scores", "🧪 Debug"]
)

with tab_hist:
    st.markdown('<div class="vv-section-title">Histórico</div>', unsafe_allow_html=True)
    if df_hist.empty:
        st.info("Sem histórico ainda.")
    else:
        df_view = df_hist.copy()

        # coluna visual de alerta
        def mark_entry(row) -> str:
            try:
                if str(row.get("status", "")).upper() == "ENTRADA":
                    return "🚨"
            except Exception:
                pass
            return ""

        df_view.insert(0, "🚨", df_view.apply(mark_entry, axis=1))

        # mostra mais útil: entrada resumida
        def entrada_short(v) -> str:
            if isinstance(v, dict):
                tprev = v.get("terminal_previsto", "")
                est = v.get("estrategia", "")
                return f"{est} | t={tprev}"
            return ""

        if "entrada" in df_view.columns:
            df_view["entrada_resumo"] = df_view["entrada"].apply(entrada_short)

        st.dataframe(df_view, use_container_width=True, height=560)

with tab_heat:
    st.markdown('<div class="vv-section-title">Heatmaps</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="large")

    heat_t = api_get("/heatmap/terminal") or api_get("/heatmap_terminal") or []
    if isinstance(heat_t, dict) and "items" in heat_t:
        heat_t = heat_t["items"]
    if not isinstance(heat_t, list):
        heat_t = []

    heat_r = api_get("/heatmap/roda") or api_get("/heatmap_roda") or []
    if isinstance(heat_r, dict) and "items" in heat_r:
        heat_r = heat_r["items"]
    if not isinstance(heat_r, list):
        heat_r = []

    with col1:
        st.markdown('<div class="vv-card">', unsafe_allow_html=True)
        st.markdown("#### Heatmap (Terminal)")
        if heat_t:
            st.dataframe(pd.DataFrame(heat_t), use_container_width=True, height=380)
        else:
            st.caption("Sem dados do endpoint de heatmap terminal.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="vv-card">', unsafe_allow_html=True)
        st.markdown("#### Heatmap (Roda EU)")
        if heat_r:
            st.dataframe(pd.DataFrame(heat_r), use_container_width=True, height=380)
        else:
            st.caption("Sem dados do endpoint de heatmap roda.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab_scores:
    st.markdown('<div class="vv-section-title">Scores</div>', unsafe_allow_html=True)
    st.caption("O painel só exibe o que o backend expõe.")

    c1, c2, c3 = st.columns(3, gap="large")

    sc_term = api_get("/scores/terminal") or []
    if isinstance(sc_term, dict) and "items" in sc_term:
        sc_term = sc_term["items"]
    if not isinstance(sc_term, list):
        sc_term = []

    sc_pad = api_get("/scores/padrao") or []
    if isinstance(sc_pad, dict) and "items" in sc_pad:
        sc_pad = sc_pad["items"]
    if not isinstance(sc_pad, list):
        sc_pad = []

    sc_combo = api_get("/scores/terminal-padrao") or api_get("/scores/terminal_padrao") or []
    if isinstance(sc_combo, dict) and "items" in sc_combo:
        sc_combo = sc_combo["items"]
    if not isinstance(sc_combo, list):
        sc_combo = []

    with c1:
        st.markdown('<div class="vv-card">', unsafe_allow_html=True)
        st.markdown("#### Score Terminal")
        if sc_term:
            st.dataframe(pd.DataFrame(sc_term), use_container_width=True, height=340)
        else:
            st.caption("Sem dados / endpoint não disponível.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="vv-card">', unsafe_allow_html=True)
        st.markdown("#### Score Padrão")
        if sc_pad:
            st.dataframe(pd.DataFrame(sc_pad), use_container_width=True, height=340)
        else:
            st.caption("Sem dados / endpoint não disponível.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="vv-card">', unsafe_allow_html=True)
        st.markdown("#### Terminal + Padrão")
        if sc_combo:
            st.dataframe(pd.DataFrame(sc_combo), use_container_width=True, height=340)
        else:
            st.caption("Sem dados / endpoint não disponível.")
        st.markdown("</div>", unsafe_allow_html=True)

with tab_debug:
    st.markdown('<div class="vv-section-title">Debug</div>', unsafe_allow_html=True)
    st.markdown('<div class="vv-card">', unsafe_allow_html=True)
    st.write("**Health**:", health)
    st.write("**Last payload**:", st.session_state.last_payload)
    st.write("**Hist rows**:", len(df_hist))
    st.write("**Auto running**:", st.session_state.auto_running)
    st.markdown("</div>", unsafe_allow_html=True)
