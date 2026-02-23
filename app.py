"""
THz Spectroscopy Analysis Studio  v4.0 (Modularized & Optimized)
Publication-quality · Bilingual UI (EN primary, ZH annotations)
Science / Nature journal figure standards
"""
import streamlit as st
from modules.science_plot import apply_nature_style
from ui_components.utils import average_by_temperature
from ui_components.sidebar import render_sidebar
from ui_components.tab_averaging import render_tab_averaging
from ui_components.tab_fano import render_tab_fano
from ui_components.tab_bcs import render_tab_bcs
from ui_components.tab_waterfall import render_tab_waterfall
from ui_components.tab_dielectric import render_tab_dielectric
from ui_components.tab_peak import render_tab_peak
from ui_components.tab_export import render_tab_export
import copy

apply_nature_style()

st.set_page_config(
    page_title="THz Analysis Studio",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=DM+Mono:wght@400;500&display=swap');

:root {
  --ink:    #0d1117;
  --steel:  #1c3557;
  --ocean:  #1a5f8a;
  --frost:  #e8f1f8;
  --rule:   #c8d8e8;
  --accent: #c0392b;
  --gold:   #b5860d;
  --bg:     #fafbfc;
  --card:   #ffffff;
}

[data-testid="stAppViewContainer"] {
  background: var(--bg);
}
[data-testid="stSidebar"] {
  background: #f0f4f8;
  border-right: 1px solid var(--rule);
}

/* ── masthead ── */
.masthead {
  border-top: 3px solid var(--steel);
  border-bottom: 1px solid var(--rule);
  padding: 18px 0 14px;
  margin-bottom: 20px;
  text-align: center;
}
.masthead-title {
  font-family: 'EB Garamond', Georgia, serif;
  font-size: 2.0rem;
  font-weight: 600;
  color: var(--steel);
  letter-spacing: 0.5px;
  margin: 0;
}
.masthead-sub {
  font-family: 'DM Mono', monospace;
  font-size: 0.72rem;
  color: #5a7898;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-top: 4px;
}
.masthead-zh {
  font-size: 0.78rem;
  color: #7a9ab8;
  margin-top: 3px;
  font-style: italic;
}

/* ── section header ── */
.sec-head {
  font-family: 'EB Garamond', serif;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--steel);
  border-bottom: 1px solid var(--rule);
  padding-bottom: 4px;
  margin: 18px 0 10px;
}

/* ── KPI cards ── */
.kpi-row { display: flex; gap: 14px; margin-bottom: 18px; }
.kpi {
  flex: 1;
  background: var(--card);
  border: 1px solid var(--rule);
  border-top: 3px solid var(--ocean);
  border-radius: 4px;
  padding: 12px 16px 10px;
}
.kpi-val  { font-family:'DM Mono',monospace; font-size:1.55rem;
            color:var(--steel); font-weight:500; }
.kpi-lbl  { font-size:0.73rem; color:#6a8aaa; text-transform:uppercase;
            letter-spacing:0.8px; margin-top:2px; }
.kpi-zh   { font-size:0.68rem; color:#9ab0c4; }

/* ── info chips ── */
.chip {
  display:inline-block;
  background: var(--frost);
  border: 1px solid var(--rule);
  border-radius: 3px;
  font-family:'DM Mono',monospace;
  font-size:0.72rem;
  color: var(--ocean);
  padding: 2px 8px;
  margin: 2px 3px;
}

/* ── annotation style ── */
.zh-note {
  font-size: 0.75rem;
  color: #7a9ab8;
  font-style: italic;
  border-left: 2px solid var(--rule);
  padding-left: 8px;
  margin: 4px 0 10px;
}

/* ── result table ── */
.result-good { background-color: #eaf7ee !important; }
.result-warn { background-color: #fff7e6 !important; }
.result-bad  { background-color: #fdecea !important; }

/* ── tab styling ── */
button[data-baseweb="tab"] {
  font-family: 'DM Mono', monospace !important;
  font-size: 0.75rem !important;
  letter-spacing: 0.5px !important;
}

/* ── sidebar labels ── */
.sidebar-section {
  font-family:'DM Mono',monospace;
  font-size:0.7rem;
  text-transform:uppercase;
  letter-spacing:1px;
  color:#5a7898;
  margin: 14px 0 6px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# SESSION STATE & DEFAULTS
# ══════════════════════════════════════════════════════════════
_defaults = dict(files=[], averaged_files=[], results={}, df=None, step=1,
                 diel=[], roi=(0.8,1.3), fitted_tc="—",
                 ref_data=None, ref_name=None)
for k,v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════
# SIDEBAR RENDERING
# ══════════════════════════════════════════════════════════════
uploaded, use_db, smooth_w, rm_bad, tc_fixed, diel_on, thickness, export_dpi, export_fmt = render_sidebar()

# ══════════════════════════════════════════════════════════════
# MASTHEAD
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="masthead">
  <div class="masthead-title">THz Spectroscopy Analysis Studio (M7 优化版)</div>
  <div class="masthead-sub">Temperature-Dependent Phonon Mode Analysis · Fano Resonance · BCS Order Parameter</div>
  <div class="masthead-zh">太赫兹光谱分析工作站 · 引入内存缓存域防挂死与 Plotly 视口降采样</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# FILE LOADING HOOK
# ══════════════════════════════════════════════════════════════
if uploaded:
    need_reload = (not st.session_state.files or
                   {f.name for f in uploaded} !=
                   {d['filename'] for d in st.session_state.files})
    if (not need_reload and st.session_state.files
            and 'amp_db' not in st.session_state.files[0]):
        need_reload = True
    if need_reload:
        from modules.data_loader import DataLoader
        loader = DataLoader()
        files, errs = [], []
        for uf in uploaded:
            try:
                files.append(loader.load_file(uf))
            except Exception as e:
                errs.append(f"{uf.name}: {e}")
        files.sort(key=lambda x: x['temperature'])
        st.session_state.files = files
        
        # Calling cached function prevents redundant heavy averaging iterations!
        avg_files, grp_info = average_by_temperature(files)
        
        st.session_state.averaged_files = avg_files
        st.session_state.avg_group_info = grp_info
        st.session_state.results = {}
        st.session_state.df = None
        if st.session_state.step == 1:
            st.session_state.step = 2
        for e in errs:
            st.warning(f"⚠️ {e}")

# ══════════════════════════════════════════════════════════════
# KPI HUD & STATE CHECK
# ══════════════════════════════════════════════════════════════
if st.session_state.files:
    files_sys = st.session_state.files
    avg_files = st.session_state.averaged_files or files_sys
    temps = [d['temperature'] for d in avg_files]
    n_ok  = len([r for r in st.session_state.results.values() if r])
    tc_str= st.session_state.fitted_tc
    n_raw = len(files_sys)
    n_avg = len(avg_files)

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi">
        <div class="kpi-val">{n_raw} → {n_avg}</div>
        <div class="kpi-lbl">Raw → Averaged</div>
        <div class="kpi-zh">原始 → 平均后</div>
      </div>
      <div class="kpi">
        <div class="kpi-val">{min(temps):.0f} – {max(temps):.0f} K</div>
        <div class="kpi-lbl">Temperature Range</div>
        <div class="kpi-zh">温度范围</div>
      </div>
      <div class="kpi">
        <div class="kpi-val">{n_ok} / {n_avg}</div>
        <div class="kpi-lbl">Fits Completed</div>
        <div class="kpi-zh">拟合完成数</div>
      </div>
      <div class="kpi">
        <div class="kpi-val">{tc_str}</div>
        <div class="kpi-lbl">Critical Temp T_c</div>
        <div class="kpi-zh">临界温度</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("⬅️  Upload THz data files in the sidebar to begin.  （请在左侧上传 .txt 数据文件）")
    st.stop()

# Evaluate transient dB vs linear copy (no mutation of pristine state)
files_active = copy.deepcopy(st.session_state.averaged_files or st.session_state.files)
if use_db:
    for d in files_active:
        if 'amp_db' in d:
            d['amp'] = d['amp_db']
    amp_label = "Amplitude dB"
else:
    amp_label = "Amplitude (a.u.)"

# Overwrite for downstream UI render
st.session_state._active_files = files_active

# ══════════════════════════════════════════════════════════════
# MODULARISED TABS CONTROLLER
# ══════════════════════════════════════════════════════════════
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "⓪ Averaging", "① ROI & Fitting", "② BCS Analysis", "③ Waterfall", "④ Dielectric", "⑤ Peak Detail", "⑥ Export"
])

with tab0:
    render_tab_averaging(amp_label)
with tab1:
    render_tab_fano(smooth_w, rm_bad, amp_label)
with tab2:
    render_tab_bcs(tc_fixed)
with tab3:
    render_tab_waterfall()
with tab4:
    render_tab_dielectric(diel_on, thickness, files_active)
with tab5:
    render_tab_peak(export_dpi, export_fmt)
with tab6:
    render_tab_export(tc_fixed, export_dpi, export_fmt, smooth_w, rm_bad, thickness, diel_on)
