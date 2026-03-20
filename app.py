"""
THz Spectroscopy Analysis Studio  v4.2
Publication-quality · Bilingual UI (EN primary, ZH annotations)
Science / Nature journal figure standards
"""
import io, warnings
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
warnings.filterwarnings("ignore")

from modules.logger import get_logger, get_log_entries, clear_logs
log = get_logger("thz")

from modules.data_loader    import DataLoader
from modules.fano_fitter    import FanoFitter
from modules.bcs_analyzer   import BCSAnalyzer
from modules.dielectric_calc import DielectricCalculator
from modules.session_manager import SessionManager
from modules.science_plot   import (apply_nature_style, apply_plotly_style,
                                    temp_cmap, format_ax, panel_label,
                                    SINGLE_COL, DOUBLE_COL, TALL_DOUBLE, WONG7)
from modules.formulas       import (FANO_FORMULA, FANO_PARAMS, FANO_EXPLANATION,
                                    DEPTH_DB_FORMULA, DEPTH_DB_EXPLANATION,
                                    LINEAR_DEPTH_FORMULA, LINEAR_DEPTH_EXPLANATION,
                                    FWHM_FORMULA, FWHM_EXPLANATION,
                                    AREA_FORMULA, AREA_EXPLANATION,
                                    R_SQUARED_FORMULA, R_SQUARED_EXPLANATION,
                                    BCS_FORMULA, BCS_PARAMS, BCS_EXPLANATION,
                                    TRANSFER_FUNC_FORMULA, REFRACTIVE_INDEX_FORMULA,
                                    EXTINCTION_FORMULA, DIELECTRIC_FORMULA,
                                    DIELECTRIC_PARAMS, DIELECTRIC_EXPLANATION,
                                    WATERFALL_FORMULA, WATERFALL_EXPLANATION,
                                    generate_formula_doc)

apply_nature_style()

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG & DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="THz Analysis Studio v4.2",
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
  font-family: Arial, Helvetica, sans-serif;
}
[data-testid="stSidebar"] {
  background: #f0f4f8;
  border-right: 1px solid var(--rule);
  font-family: Arial, Helvetica, sans-serif;
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
  font-family: Arial, Helvetica, sans-serif;
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
# SESSION STATE
# ══════════════════════════════════════════════════════════════
_defaults = dict(files=[], averaged_files=[], results={}, df=None, step=1,
                 diel=[], roi=(0.8,1.3), fitted_tc="—",
                 ref_data=None, ref_name=None)
for k,v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def plotly_fig(height=400, title=""):
    fig = go.Figure()
    apply_plotly_style(fig, height=height, title=title)
    return fig

def get_colors(n):
    return temp_cmap(n)

def zh(text):
    st.markdown(f'<div class="zh-note">{text}</div>', unsafe_allow_html=True)

def sec(text, zh_text=""):
    st.markdown(f'<div class="sec-head">{text}</div>', unsafe_allow_html=True)
    if zh_text:
        zh(zh_text)

def clear_fano_cache():
    """Clear downstream Fano fitting results when raw data processing changes."""
    st.session_state.df = None
    st.session_state.results = {}
    st.session_state['_files_changed'] = True

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="sidebar-section">📁 Data Input · 数据输入</div>',
                unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload THz data files (.txt)",
        type=["txt"], accept_multiple_files=True,
        help="Filename or header must contain temperature, e.g. '300K'\\n"
             "文件名或表头需含温度，如 300K")

    st.markdown('<div class="sidebar-section">⚙️ Processing · 处理参数</div>',
                unsafe_allow_html=True)
    amp_col_choice = st.radio(
        "Amplitude column / 振幅列",
        ["AMP FD (col 5)", "AMP dB (col 6)"],
        index=0,
        help="Choose which amplitude column to use for analysis.\\n"
             "选择用于分析的振幅列：FD（线性）或 dB（对数）",
        on_change=clear_fano_cache
    )
    use_db = "dB" in amp_col_choice
    smooth_w = st.slider("Smoothing window 平滑窗口", 1, 15, 5, 2, on_change=clear_fano_cache)
    rm_bad   = st.checkbox("Remove outliers 去除坏点", True, on_change=clear_fano_cache)
    use_avg  = st.checkbox("Use averaged data 使用平均后数据", True,
                           help="When checked, spectra at the same temperature are averaged.\n"
                                "取消勾选后将使用所有原始扫描数据（不平均）。", on_change=clear_fano_cache)

    st.markdown('<div class="sidebar-section">📈 BCS Fitting · BCS拟合</div>',
                unsafe_allow_html=True)
    tc_mode = st.radio("T_c mode  临界温度模式",
                       ["Auto-optimize 自动", "Fixed 手动固定"])
    tc_fixed = None
    if "Fixed" in tc_mode:
        _tc_c1, _tc_c2 = st.columns([2, 1])
        with _tc_c1:
            tc_fixed = st.slider("T_c (K)", 280.0, 380.0,
                                 st.session_state.get('_tc_val', 328.0), 0.5,
                                 key='_tc_slider')
        with _tc_c2:
            tc_fixed = st.number_input("T_c", 280.0, 380.0, tc_fixed, 0.5,
                                       key='_tc_num', label_visibility='collapsed')

    st.markdown('<div class="sidebar-section">📎 Reference / Substrate · 参考基底</div>',
                unsafe_allow_html=True)
    ref_uploaded = st.file_uploader(
        "Upload reference file (.txt)  上传参考(基底)文件",
        type=["txt"], accept_multiple_files=False,
        help="Reference/substrate measurement for dielectric calculation.\\n"
             "介电计算所需的参考/基底测量数据。此文件不会参与Fano/BCS分析。",
        key="ref_uploader")

    if ref_uploaded:
        if (st.session_state.ref_name != ref_uploaded.name):
            loader_ref = DataLoader()
            try:
                st.session_state.ref_data = loader_ref.load_file(ref_uploaded)
                st.session_state.ref_name = ref_uploaded.name
            except Exception as e:
                st.error(f"❌ Reference load failed: {e}")
                st.session_state.ref_data = None
                st.session_state.ref_name = None

    if st.session_state.ref_data:
        st.caption(f"📌 Ref: **{st.session_state.ref_name}** · "
                   f"T={st.session_state.ref_data['temperature']:.0f} K")

    st.markdown('<div class="sidebar-section">⚡ Dielectric · 介电函数</div>',
                unsafe_allow_html=True)
    diel_on = st.checkbox("Enable dielectric calculation 启用介电计算")
    thickness = 0.5
    if diel_on:
        thickness = st.number_input("Sample thickness (mm) 样品厚度",
                                    0.01, 20.0, 0.5, 0.01)
        if not st.session_state.ref_data:
            st.warning("⚠️ Upload a reference file above for dielectric.\\n"
                       "请在上方上传参考文件以启用介电计算。")
    ref_name = st.session_state.ref_name


    st.markdown('<div class="sidebar-section">🖼️ Figure Export · 图片导出</div>',
                unsafe_allow_html=True)
    export_dpi = st.selectbox("Export DPI", [150, 300, 600], index=1)
    export_fmt = st.selectbox("Format 格式", ["pdf", "png", "svg"], index=0)

    st.divider()
    if st.button("↺  Reset all · 重置", use_container_width=True):
        clear_logs()
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()



# ══════════════════════════════════════════════════════════════
# MASTHEAD
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="masthead">
  <div class="masthead-title">THz Spectroscopy Analysis Studio <span style="font-size:0.6em;color:#5a7898;">v4.2</span></div>
  <div class="masthead-sub">Temperature-Dependent Phonon Mode Analysis · Fano Resonance · BCS Order Parameter</div>
  <div class="masthead-zh">太赫兹光谱分析工作站 · 声子模式 · Fano共振 · BCS序参量</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TEMPERATURE AVERAGING
# ══════════════════════════════════════════════════════════════
def average_by_temperature(files, tol=1.0):
    """Group files by temperature (±tol K) and average within each group.

    Returns a list of averaged dicts (same structure as DataLoader output)
    plus a grouping info dict {temp: [filenames]}.

    Fixes applied:
    - freq/amp sorted before interpolation
    - np.linspace for stable common grid
    - validation of overlapping freq ranges
    """
    from collections import defaultdict

    # Sort by temperature
    sorted_files = sorted(files, key=lambda d: d['temperature'])

    # Group using tolerance
    groups = []  # [(representative_temp, [file_dicts])]
    for d in sorted_files:
        matched = False
        for g in groups:
            if abs(d['temperature'] - g[0]) <= tol:
                g[1].append(d)
                matched = True
                break
        if not matched:
            groups.append((d['temperature'], [d]))

    averaged = []
    group_info = {}  # {temp: [filenames]}
    for rep_temp, members in groups:
        mean_temp = np.mean([m['temperature'] for m in members])
        fnames = [m['filename'] for m in members]
        group_info[round(mean_temp, 1)] = fnames

        if len(members) == 1:
            m = members[0]
            averaged.append({
                'filename': m['filename'],
                'temperature': m['temperature'],
                'freq': m['freq'].copy(),
                'amp': m['amp'].copy(),
                'amp_db': m.get('amp_db', m['amp']).copy(),
                'time': m['time'].copy() if 'time' in m else np.array([]),
                'E_field': m['E_field'].copy() if 'E_field' in m else np.array([]),
                'n_averaged': 1,
                'source_files': fnames,
            })
            continue

        # ── Ensure each member's freq is sorted ──
        for m in members:
            sort_idx = np.argsort(m['freq'])
            m['freq'] = m['freq'][sort_idx]
            m['amp'] = m['amp'][sort_idx]
            if 'amp_db' in m and m['amp_db'] is not None:
                m['amp_db'] = m['amp_db'][sort_idx]

        # ── Build common frequency grid ──
        # Use the FIRST member's grid as reference to minimize interpolation
        # Only interpolate others onto this grid (within overlapping range)
        ref = members[0]
        f_min = max(m['freq'].min() for m in members)
        f_max = min(m['freq'].max() for m in members)

        if f_min >= f_max:
            # No overlapping range — fall back to first member
            m = members[0]
            averaged.append({
                'filename': f"avg_{mean_temp:.0f}K (NO OVERLAP, using first)",
                'temperature': mean_temp,
                'freq': m['freq'].copy(),
                'amp': m['amp'].copy(),
                'amp_db': m.get('amp_db', m['amp']).copy(),
                'time': m.get('time', np.array([])),
                'E_field': m.get('E_field', np.array([])),
                'n_averaged': 1,
                'source_files': fnames,
            })
            continue

        # Use reference grid within overlap region
        ref_mask = (ref['freq'] >= f_min) & (ref['freq'] <= f_max)
        f_common = ref['freq'][ref_mask]

        if len(f_common) < 2:
            # Too few points in overlap
            steps = [np.median(np.abs(np.diff(m['freq']))) for m in members
                     if len(m['freq']) > 1]
            df = min(steps) if steps else 0.001
            n_pts = max(2, int(round((f_max - f_min) / df)))
            f_common = np.linspace(f_min, f_max, n_pts)

        # ── Interpolate all members onto common grid and average ──
        interp_amps = []
        interp_amps_db = []
        for m in members:
            interp_amps.append(
                np.interp(f_common, m['freq'], m['amp']))
            db_col = m.get('amp_db', m['amp'])
            interp_amps_db.append(
                np.interp(f_common, m['freq'], db_col))

        avg_amp = np.mean(interp_amps, axis=0)
        avg_amp_db = np.mean(interp_amps_db, axis=0)

        # ── Diagnostic Logging ──
        log.info(f"Math Avg {mean_temp:.0f}K (n={len(members)}): "
                 f"Linear[mean={avg_amp.mean():.4e}, max={avg_amp.max():.4e}] | "
                 f"dB[mean={avg_amp_db.mean():.2f}, max={avg_amp_db.max():.2f}]")

        # For time-domain: use the first member's data (needed for dielectric)
        m0 = members[0]
        averaged.append({
            'filename': f"avg_{mean_temp:.0f}K ({len(members)} scans)",
            'temperature': mean_temp,
            'freq': f_common,
            'amp': avg_amp,
            'amp_db': avg_amp_db,
            'time': m0.get('time', np.array([])),
            'E_field': m0.get('E_field', np.array([])),
            'n_averaged': len(members),
            'source_files': fnames,
        })

    averaged.sort(key=lambda x: x['temperature'])
    return averaged, group_info


# ══════════════════════════════════════════════════════════════
# FILE LOADING
# ══════════════════════════════════════════════════════════════
if uploaded:
    need_reload = (not st.session_state.files or
                   {f.name for f in uploaded} !=
                   {d['filename'] for d in st.session_state.files})
    # Also reload if old data format (missing amp_db)
    if (not need_reload and st.session_state.files
            and 'amp_db' not in st.session_state.files[0]):
        need_reload = True
    if need_reload:
        loader = DataLoader()
        files, errs = [], []
        for uf in uploaded:
            try:
                files.append(loader.load_file(uf))
                log.info(f"Loaded {uf.name} — T={files[-1]['temperature']:.0f} K, {len(files[-1]['freq'])} pts")
            except Exception as e:
                errs.append(f"{uf.name}: {e}")
                log.error(f"Failed to load {uf.name}: {e}")
        files.sort(key=lambda x: x['temperature'])
        st.session_state.files = files
        log.info(f"Total files loaded: {len(files)}")
        # Compute averages
        avg_files, grp_info = average_by_temperature(files)
        st.session_state.averaged_files = avg_files
        st.session_state.avg_group_info = grp_info
        st.session_state.results = {}
        st.session_state.df = None
        st.session_state['_files_changed'] = True  # Trigger auto peak-finding
        if st.session_state.step == 1:
            st.session_state.step = 2
        for e in errs:
            st.warning(f"⚠️ {e}")

# Render Activity Log in sidebar AFTER file loading is completed so newest logs appear
with st.sidebar:
    st.markdown('<div class="sidebar-section">📋 Activity Log · 操作日志</div>',
                unsafe_allow_html=True)
    with st.expander("Show log  查看日志", expanded=False):
        entries = get_log_entries()
        if entries:
            st.code("\n".join(entries[-30:]), language="log")
        else:
            st.caption("No log entries yet.  暂无日志。")

# ── KPI bar ──────────────────────────────────────────────────
if st.session_state.files:
    files = st.session_state.files
    avg_files = st.session_state.averaged_files or files
    temps = [d['temperature'] for d in avg_files]
    n_ok  = len([r for r in st.session_state.results.values() if r])
    tc_str= st.session_state.fitted_tc
    n_raw = len(files)
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
    st.info("⬅️  Upload THz data files in the sidebar to begin.  "
            "（请在左侧上传 .txt 数据文件）")
    st.stop()

# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════

def _single_fig_export(r, w, h, dpi, fmt, style='Nature'):
    if style == 'Origin': apply_origin_style()
    else: apply_nature_style()
    
    fig, ax = plt.subplots(figsize=(w, h))
    fx, sig, fit_s = r['freq_roi'], r['signal'], r['fitted_signal']
    ax.fill_between(fx, 0, sig, color='#2c6ea5', alpha=0.12)
    ax.plot(fx, sig,   color='#1a5f8a', lw=1.5, label='Signal')
    ax.plot(fx, fit_s, color='#c0392b', lw=1.5, ls='--', label='Fano fit')
    ax.vlines(r['peak_x'], 0, r['Linear_Depth'],
              colors='#27ae60', lw=1.2, ls=':')
    ax.hlines(r['half_height'], r['left_x'], r['right_x'],
              colors='#8e44ad', lw=1.2)
    ax.set_xlabel('Frequency (THz)')
    ax.set_ylabel('ΔAmplitude (arb. u.)')
    ax.set_title(f"T = {r['Temperature_K']:.0f} K", pad=5, fontsize=8)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=True)
    format_ax(ax); panel_label(ax, 'a')
    plt.tight_layout(pad=0.2)
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _make_excel(df, diel_rs):
    buf = io.BytesIO()
    drop = ['freq_roi','signal','fitted_signal',
            'half_height','left_x','right_x','peak_x']
    df_out = (df.drop(columns=drop, errors='ignore')
                .sort_values('Temperature_K'))
    with pd.ExcelWriter(buf, engine='openpyxl') as xw:
        df_out.to_excel(xw, sheet_name='Fano_Parameters', index=False)
        if diel_rs:
            rows = []
            for res in diel_rs:
                for j in range(len(res['freq'])):
                    rows.append({'T (K)': res['temp'],
                                 'Freq (THz)': res['freq'][j],
                                 'n': res['n'][j], 'k': res['k'][j],
                                 'eps1': res['e1'][j],
                                 'eps2': res['e2'][j]})
            pd.DataFrame(rows).to_excel(
                xw, sheet_name='Dielectric_Functions', index=False)
    buf.seek(0)
    return buf.getvalue()


def _make_pdf_report(df, results, tc_fixed_val, dpi, style='Nature'):
    if style == 'Origin': apply_origin_style()
    else: apply_nature_style()
    
    bcs = BCSAnalyzer(tc_fixed=tc_fixed_val)
    df  = df.sort_values('Temperature_K')
    T   = df['Temperature_K'].values.astype(float)
    T_s = np.linspace(T.min()*0.82, max(T.max()+15,360), 500)
    buf = io.BytesIO()

    with PdfPages(buf) as pdf:
        # ── page 1: BCS fits ────────────────────────────────────────────
        fig, axes = plt.subplots(1, 2, figsize=DOUBLE_COL)
        for ax, col, lbl, color in [
            (axes[0],'Linear_Depth','Peak Depth (arb. u.)','#1a5f8a'),
            (axes[1],'Area',        'Integrated Area (arb. u.·THz)','#27ae60'),
        ]:
            y = df[col].values.astype(float)
            ax.scatter(T, y, s=28, color=color,
                       edgecolors='#111', linewidths=0.8, zorder=5)
            p = bcs.fit(T, y)
            if p:
                ax.plot(T_s, bcs.bcs(T_s,*p),
                        color='#c0392b', lw=1.6,
                        label=f'BCS  $T_c$={p[1]:.1f} K  $\\beta$={p[2]:.2f}')
                ax.axvline(p[1], color='#888', ls='--', lw=1.0)
            ax.set_xlabel('Temperature (K)')
            ax.set_ylabel(lbl)
            ax.set_ylim(bottom=0)
            ax.legend(fontsize=7)
            format_ax(ax)
        panel_label(axes[0],'a'); panel_label(axes[1],'b')
        plt.suptitle('BCS Order Parameter Fitting', fontsize=10,
                     fontweight='bold', y=1.01)
        plt.tight_layout(pad=0.3)
        pdf.savefig(fig, dpi=dpi, bbox_inches='tight'); plt.close()

        # ── page 2: freq + FWHM ─────────────────────────────────────────
        fig, axes = plt.subplots(1, 2, figsize=DOUBLE_COL)
        for ax, col, ylab, col2 in [
            (axes[0],'Peak_Freq_THz','Phonon Frequency (THz)','#b5860d'),
            (axes[1],'FWHM_THz',    'FWHM (THz)','#8e44ad'),
        ]:
            ax.plot(T, df[col].values, 'o--', color=col2,
                    ms=4.5, lw=1.2, mec='#111', mew=0.8)
            ax.set_xlabel('Temperature (K)')
            ax.set_ylabel(ylab)
            ax.set_ylim(bottom=0)
            format_ax(ax)
        panel_label(axes[0],'c'); panel_label(axes[1],'d')
        plt.suptitle('Phonon Frequency and Linewidth', fontsize=10,
                     fontweight='bold', y=1.01)
        plt.tight_layout(pad=0.3)
        pdf.savefig(fig, dpi=dpi, bbox_inches='tight'); plt.close()

        # ── page 3+: waterfall ──────────────────────────────────────────
        ok_items = sorted(
            [(k,v) for k,v in results.items() if v],
            key=lambda x: x[1]['Temperature_K'])
        n_c  = len(ok_items)
        cols_wf = temp_cmap(n_c)
        peak_hs = [v['Linear_Depth'] for _,v in ok_items]
        off_stp = float(np.median(peak_hs))*1.8 if peak_hs else 1.0

        fig, ax = plt.subplots(figsize=(3.5, max(4.0, n_c*0.22)))
        for i,(_, r) in enumerate(ok_items):
            fx = r['freq_roi']
            sy = r['signal']
            m  = (fx>=0.60)&(fx<=1.60)
            if not m.any(): continue
            off = i*off_stp
            c   = cols_wf[i]
            ax.plot(fx[m], sy[m]+off, color=c, lw=0.9)
            if i%(max(1,n_c//10))==0:
                ax.text(1.61, float(sy[m][-1])+off if m.any() else off,
                        f"{r['Temperature_K']:.0f} K",
                        fontsize=5.5, color=c, va='center')
        ax.set_xlabel('Frequency (THz)')
        ax.set_ylabel('Intensity (arb. u., offset)')
        ax.set_xlim(0.60, 1.75)
        ax.set_yticks([])
        ax.set_title('Temperature Evolution of Phonon Mode',
                     fontsize=8, pad=5)
        format_ax(ax, minor=False)
        panel_label(ax,'e')
        plt.tight_layout(pad=0.4)
        pdf.savefig(fig, dpi=dpi, bbox_inches='tight'); plt.close()

        # ── page 4+: individual fits ────────────────────────────────────
        step_sel = max(1, n_c//12)
        sel_fits = ok_items[::step_sel][:12]
        n_sub    = len(sel_fits)
        ncols    = 3; nrows = (n_sub+ncols-1)//ncols
        fig, axes = plt.subplots(nrows, ncols,
                                 figsize=(7.0, nrows*2.4))
        axes = axes.flatten()
        for i,(_, r) in enumerate(sel_fits):
            ax = axes[i]
            ax.fill_between(r['freq_roi'],0,r['signal'],
                            color='#2c6ea5',alpha=0.12)
            ax.plot(r['freq_roi'],r['signal'],
                    color='#1a5f8a',lw=1.0,label='Signal')
            ax.plot(r['freq_roi'],r['fitted_signal'],
                    color='#c0392b',lw=1.0,ls='--',label='Fano fit')
            ax.vlines(r['peak_x'],0,r['Linear_Depth'],
                      colors='#27ae60',lw=0.9,ls=':')
            ax.hlines(r['half_height'],r['left_x'],r['right_x'],
                      colors='#8e44ad',lw=0.9)
            ax.set_title(f"{r['Temperature_K']:.0f} K  "
                         f"R²={r['R_squared']:.3f}",
                         fontsize=7, pad=3)
            ax.set_ylim(bottom=0)
            ax.set_xlabel('Frequency (THz)', fontsize=6)
            ax.set_ylabel('ΔAmpl. (arb. u.)', fontsize=6)
            format_ax(ax)
        for j in range(i+1, len(axes)):
            axes[j].axis('off')
        plt.suptitle('Representative Fano Fits', fontsize=9,
                     fontweight='bold', y=1.01)
        plt.tight_layout(pad=0.4)
        pdf.savefig(fig, dpi=dpi, bbox_inches='tight'); plt.close()

        d = pdf.infodict()
        d['Title']   = 'THz Spectroscopy Analysis Report'
        d['Author']  = 'THz Analysis Studio v3.0'
        d['Subject'] = 'Fano resonance & BCS order parameter'

    buf.seek(0)
    return buf.read()


def _export_all_figs(results, dpi, style='Nature'):
    if style == 'Origin': apply_origin_style()
    else: apply_nature_style()
    
    buf = io.BytesIO()
    ok_items = sorted(
        [(k,v) for k,v in results.items() if v],
        key=lambda x: x[1]['Temperature_K'])

    with PdfPages(buf) as pdf:
        for _, r in ok_items:
            fig, ax = plt.subplots(figsize=SINGLE_COL)
            ax.fill_between(r['freq_roi'],0,r['signal'],
                            color='#2c6ea5',alpha=0.12)
            ax.plot(r['freq_roi'],r['signal'],
                    color='#1a5f8a',lw=1.5,label='Signal')
            ax.plot(r['freq_roi'],r['fitted_signal'],
                    color='#c0392b',lw=1.5,ls='--',label='Fano fit')
            ax.vlines(r['peak_x'],0,r['Linear_Depth'],
                      colors='#27ae60',lw=1.2,ls=':')
            ax.hlines(r['half_height'],r['left_x'],r['right_x'],
                      colors='#8e44ad',lw=1.2)
            ax.set_xlabel('Frequency (THz)')
            ax.set_ylabel('ΔAmplitude (arb. u.)')
            ax.set_title(f"T = {r['Temperature_K']:.0f} K  ·  "
                         f"$f_r$ = {r['Peak_Freq_THz']:.4f} THz  ·  "
                         f"R² = {r['R_squared']:.4f}",
                         fontsize=7, pad=4)
            ax.set_ylim(bottom=0)
            ax.legend(fontsize=7)
            format_ax(ax)
            plt.tight_layout(pad=0.2)
            pdf.savefig(fig, dpi=dpi, bbox_inches='tight')
            plt.close(fig)

    buf.seek(0)
    return buf.read()


tab0, tab_mg, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "⓪ Averaging",
    "① Mode Grouping",
    "② ROI & Fitting",
    "③ BCS Analysis",
    "④ Waterfall",
    "⑤ Dielectric",
    "⑥ Peak Detail",
    "⑦ Export",
    "⑧ History",
])

# Use averaged or raw files based on user toggle
if use_avg:
    files = st.session_state.averaged_files or st.session_state.files
else:
    files = st.session_state.files
raw_files = st.session_state.files

# ── Apply amplitude column selection ──
if use_db:
    import copy
    files = copy.deepcopy(files)
    raw_files = copy.deepcopy(raw_files)
    for d in files:
        if 'amp_db' in d:
            d['amp'] = d['amp_db']
    for d in raw_files:
        if 'amp_db' in d:
            d['amp'] = d['amp_db']
_amp_label = "Amplitude (dB)" if use_db else "Amplitude (A.U.)"

# ── Apply mode group filtering (from Tab ① Mode Grouping) ──
if st.session_state.get('mode_group_files') is not None:
    files = st.session_state['mode_group_files']
    # Also apply dB override to mode-filtered files if needed
    if use_db:
        import copy as _mode_cp
        files = _mode_cp.deepcopy(files)
        for d in files:
            if 'amp_db' in d:
                d['amp'] = d['amp_db']
    # Auto-set ROI from mode grouping
    if st.session_state.get('mode_group_roi') is not None:
        _mode_roi = st.session_state['mode_group_roi']
        if 'roi_l_val' not in st.session_state or st.session_state.get('_mode_roi_applied') != _mode_roi:
            st.session_state['roi_l_val'] = _mode_roi[0]
            st.session_state['roi_r_val'] = _mode_roi[1]
            st.session_state['roi_l_num'] = _mode_roi[0]
            st.session_state['roi_r_num'] = _mode_roi[1]
            st.session_state['_mode_roi_applied'] = _mode_roi

# ─────────────────────────────────────────────────
# TAB 0 — Averaging
# ─────────────────────────────────────────────────
with tab0:
    sec("Temperature Averaging", "按温度分组平均 · 可排除异常扫描后重新平均")

    _raw = st.session_state.files
    _avg = st.session_state.averaged_files or _raw
    _grp = getattr(st.session_state, 'avg_group_info', None) or {}

    # Initialize excluded scans set
    if 'excluded_scans' not in st.session_state:
        st.session_state.excluded_scans = set()

    # ── Grouping summary table ──
    grp_rows = []
    for d in _avg:
        src = d.get('source_files', [d['filename']])
        grp_rows.append({
            'Temperature (K)': f"{d['temperature']:.1f}",
            '# Scans': d.get('n_averaged', 1),
            'Source Files': ', '.join(src),
            'Freq Points': len(d['freq']),
        })
    grp_df = pd.DataFrame(grp_rows)
    st.dataframe(grp_df, use_container_width=True, hide_index=True)

    n_excluded = len(st.session_state.excluded_scans)
    info_txt = f"共 {len(_raw)} 个原始文件 → 按温度分组平均后得到 {len(_avg)} 组数据"
    if n_excluded > 0:
        info_txt += f" · 已排除 {n_excluded} 个扫描"
    zh(info_txt)

    # ── Scan selection & exclusion ──
    st.divider()
    sec("Scan Selection  扫描选择", "取消勾选要排除的扫描，然后点击「重新平均」")

    # Group raw files by temperature (same logic as average_by_temperature)
    from collections import defaultdict
    sorted_raw = sorted(_raw, key=lambda d: d['temperature'])
    temp_groups = []
    for d in sorted_raw:
        matched = False
        for g in temp_groups:
            if abs(d['temperature'] - g[0]) <= 1.0:
                g[1].append(d)
                matched = True
                break
        if not matched:
            temp_groups.append((d['temperature'], [d]))

    multi_temp_groups = [(t, members) for t, members in temp_groups if len(members) > 1]

    if multi_temp_groups:
        # Show each temperature group with checkboxes
        for g_idx, (rep_temp, members) in enumerate(multi_temp_groups):
            mean_t = np.mean([m['temperature'] for m in members])
            st.markdown(f"**{mean_t:.1f} K** — {len(members)} scans")

            # Plot all scans in this group
            colors_grp = get_colors(len(members))
            fig_grp = plotly_fig(320,
                f"{mean_t:.1f} K — select scans to keep  选择要保留的扫描")

            kept_count = 0
            scan_cols = st.columns(min(len(members), 4))
            for j, m in enumerate(members):
                fname = m['filename']
                is_excluded = fname in st.session_state.excluded_scans
                col_idx = j % len(scan_cols)
                with scan_cols[col_idx]:
                    keep = st.checkbox(
                        f"✓ {fname}",
                        value=not is_excluded,
                        key=f"scan_{g_idx}_{j}_{fname}",
                    )
                    if not keep:
                        st.session_state.excluded_scans.add(fname)
                    else:
                        st.session_state.excluded_scans.discard(fname)

                # Plot this scan
                opacity = 0.2 if fname in st.session_state.excluded_scans else 0.8
                lw = 0.6 if fname in st.session_state.excluded_scans else 1.4
                dash = 'dot' if fname in st.session_state.excluded_scans else 'solid'
                fig_grp.add_trace(go.Scatter(
                    x=m['freq'], y=m['amp'],
                    mode='lines',
                    name=f"{'❌ ' if fname in st.session_state.excluded_scans else ''}{fname}",
                    line=dict(color=colors_grp[j], width=lw, dash=dash),
                    opacity=opacity,
                ))
                if fname not in st.session_state.excluded_scans:
                    kept_count += 1

            # If there's a current average, overlay it
            avg_d = next((a for a in _avg
                          if abs(a['temperature'] - mean_t) <= 1.0
                          and a.get('n_averaged', 1) > 1), None)
            if avg_d is not None:
                fig_grp.add_trace(go.Scatter(
                    x=avg_d['freq'], y=avg_d['amp'],
                    mode='lines',
                    name=f'Current average ({avg_d.get("n_averaged",1)} scans)',
                    line=dict(color='#c0392b', width=2.5),
                ))

            fig_grp.update_xaxes(title_text='Frequency (THz)')
            fig_grp.update_yaxes(title_text=_amp_label)
            st.plotly_chart(fig_grp, use_container_width=True, config={'editable': True})
            zh(f"保留 {kept_count}/{len(members)} 个扫描 · "
               f"虚线/半透明 = 已排除 · 粗红线 = 当前平均结果")
            st.markdown("---")

        # ── Re-average button ──
        rea_col1, rea_col2 = st.columns([1, 2])
        with rea_col1:
            if st.button("🔄 Re-average with selection  重新平均",
                         type="primary", use_container_width=True,
                         key="tab0_reavg_btn"):
                # Filter out excluded scans and re-average
                kept_files = [f for f in _raw
                              if f['filename'] not in st.session_state.excluded_scans]
                if not kept_files:
                    st.error("No scans left after exclusion!  排除后没有数据了！")
                else:
                    avg_new, grp_new = average_by_temperature(kept_files)
                    st.session_state.averaged_files = avg_new
                    st.session_state.avg_group_info = grp_new
                    # Clear fitting results since data changed
                    st.session_state.results = {}
                    st.session_state.df = None
                    log.info(f"Re-averaged: {len(kept_files)}/{len(_raw)} scans kept, "
                             f"excluded: {st.session_state.excluded_scans}")
                    st.rerun()
        with rea_col2:
            if st.button("↺ Reset exclusions  重置排除", use_container_width=True,
                         key="tab0_reset_btn"):
                st.session_state.excluded_scans = set()
                avg_new, grp_new = average_by_temperature(_raw)
                st.session_state.averaged_files = avg_new
                st.session_state.avg_group_info = grp_new
                st.session_state.results = {}
                st.session_state.df = None
                log.info("Exclusions reset, re-averaged with all scans")
                st.rerun()
    else:
        st.info("No temperatures have multiple scans to average.  "
                "没有温度有多次扫描需要平均。每个温度只有一个文件。")
# ─────────────────────────────────────────────────
# TAB MG — Mode Grouping (auto-detect & cluster dips)
# ─────────────────────────────────────────────────
with tab_mg:
    sec("Phonon Mode Grouping",
        "自动检测吸收峰（dip），按频率聚类分组，每组独立分析导出")

    if not files:
        st.info("Please upload data files first.  请先上传数据。")
        st.stop()

    # ── Controls ──
    mg_row1_c1, mg_row1_c2 = st.columns(2)
    with mg_row1_c1:
        mg_freq_range = st.slider(
            "Search frequency range (THz) / 搜索频率范围",
            0.1, 5.0, (0.5, 2.0), 0.05,
            help="Only look for dips within this frequency range. "
                 "Ignore noisy regions outside.",
            key="mg_freq_range")
    with mg_row1_c2:
        mg_max_groups = st.slider(
            "Max groups / 最多分组数",
            1, 8, 4, 1,
            help="Keep only the N most prominent mode groups.",
            key="mg_max_groups")

    mg_row2_c1, mg_row2_c2, mg_row2_c3 = st.columns(3)
    with mg_row2_c1:
        mg_prominence = st.slider(
            "Dip prominence / 凹陷显著性",
            0.001, 0.5, 0.02, 0.005,
            help="Minimum relative prominence. Larger = only deeper dips.",
            key="mg_prom")
    with mg_row2_c2:
        mg_tolerance = st.slider(
            "Grouping tolerance (THz) / 聚类容差",
            0.01, 0.5, 0.08, 0.01,
            help="Dips within this range are merged into one group.",
            key="mg_tol")
    with mg_row2_c3:
        mg_smooth = st.slider(
            "Detection smoothing / 检测平滑",
            1, 15, 5, 2, key="mg_smooth")

    # ── Dip detection per scan (within freq range only) ──
    from scipy.signal import find_peaks
    import copy as _cp

    f_search_lo, f_search_hi = mg_freq_range
    all_dip_records = []

    for d in files:
        freq_arr = d['freq'].astype(float)
        amp_arr  = d['amp'].astype(float)

        # Restrict to search range
        search_mask = (freq_arr >= f_search_lo) & (freq_arr <= f_search_hi)
        freq_s = freq_arr[search_mask]
        amp_s  = amp_arr[search_mask]
        if len(freq_s) < 10:
            continue

        # Smooth
        if mg_smooth > 1 and len(amp_s) > mg_smooth:
            try:
                from scipy.signal import savgol_filter as _sgf
                sw = mg_smooth if mg_smooth % 2 == 1 else mg_smooth + 1
                amp_sm = _sgf(amp_s, sw, 3)
            except Exception:
                amp_sm = pd.Series(amp_s).rolling(mg_smooth, center=True).mean().bfill().ffill().values
        else:
            amp_sm = amp_s

        # Invert to find dips
        inverted = -amp_sm + np.max(amp_sm)
        peaks, props = find_peaks(inverted, width=3,
                                   prominence=np.max(inverted) * mg_prominence)

        for pi, pk_idx in enumerate(peaks):
            all_dip_records.append({
                'filename':    d['filename'],
                'temperature': d['temperature'],
                'dip_freq':    float(freq_s[pk_idx]),
                'dip_amp':     float(amp_s[pk_idx]),
                'prominence':  float(props['prominences'][pi]),
            })

    if not all_dip_records:
        st.warning("No dips detected in the search range. "
                   "Try widening the frequency range or lowering prominence.  "
                   "搜索范围内未检测到凹陷。")
        st.stop()

    # ── Clustering ──
    dip_freqs_all = np.array([r['dip_freq'] for r in all_dip_records])
    sorted_indices = np.argsort(dip_freqs_all)
    clusters = []

    current_cluster = [sorted_indices[0]]
    for idx in sorted_indices[1:]:
        if dip_freqs_all[idx] - dip_freqs_all[current_cluster[-1]] <= mg_tolerance:
            current_cluster.append(idx)
        else:
            clusters.append(current_cluster)
            current_cluster = [idx]
    clusters.append(current_cluster)

    # Build cluster info and sort by total prominence (most significant first)
    cluster_info = []
    for ci, members in enumerate(clusters):
        freqs = dip_freqs_all[members]
        temps = [all_dip_records[m]['temperature'] for m in members]
        total_prom = sum(all_dip_records[m]['prominence'] for m in members)
        cluster_info.append({
            'id':        ci,
            'center':    float(np.mean(freqs)),
            'std':       float(np.std(freqs)) if len(freqs) > 1 else 0.0,
            'count':     len(members),
            'min_freq':  float(np.min(freqs)),
            'max_freq':  float(np.max(freqs)),
            'temps':     temps,
            'total_prom': total_prom,
            'members':   members,
        })

    # Keep only top N groups by prominence
    cluster_info.sort(key=lambda x: x['total_prom'], reverse=True)
    cluster_info = cluster_info[:mg_max_groups]
    cluster_info.sort(key=lambda x: x['center'])
    for i, c in enumerate(cluster_info):
        c['id'] = i

    # ── Summary table ──
    st.divider()
    sec("Detected Mode Groups",
        f"检测到 {len(cluster_info)} 个声子模式"
        f"（频率范围 {f_search_lo}–{f_search_hi} THz）")
    summary_rows = []
    for c in cluster_info:
        summary_rows.append({
            'Mode':           f"Mode {c['id']+1}",
            'Center (THz)':   f"{c['center']:.3f}",
            'Spread':         f"±{c['std']:.4f}",
            '# Dips found':   c['count'],
            'T range (K)':    f"{min(c['temps']):.0f} – {max(c['temps']):.0f}",
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True,
                 hide_index=True)

    # ── Mode selection for downstream ──
    st.divider()
    sec("Select Active Mode",
        "选择模式 → 下游 ROI/BCS 将自动对准该频率区间（所有扫描都保留）")

    mode_options = ["All scans (no grouping) / 全部扫描"]
    for c in cluster_info:
        mode_options.append(f"Mode {c['id']+1} @ {c['center']:.3f} THz")
    selected_mode = st.radio("Active mode / 活跃模式", mode_options,
                              key="mg_active", horizontal=True)

    if "All scans" in selected_mode:
        st.session_state['mode_group_files'] = None
        st.session_state['mode_group_roi']   = None
    else:
        mode_idx = int(selected_mode.split("Mode ")[1].split(" @")[0]) - 1
        c = cluster_info[mode_idx]
        # ALL files go downstream — just auto-set ROI
        mode_files = [_cp.deepcopy(d) for d in files]
        margin = max(0.15, (c['max_freq'] - c['min_freq']) / 2 + 0.15)
        flo_g = min(dd['freq'].min() for dd in mode_files)
        fhi_g = max(dd['freq'].max() for dd in mode_files)
        auto_l = float(np.clip(c['center'] - margin, flo_g, fhi_g))
        auto_r = float(np.clip(c['center'] + margin, flo_g, fhi_g))
        st.session_state['mode_group_files'] = mode_files
        st.session_state['mode_group_roi']   = (auto_l, auto_r)
        st.success(
            f"✅ Mode {mode_idx+1}: ROI → [{auto_l:.3f}, {auto_r:.3f}] THz  "
            f"（{len(mode_files)} scans）")

    # ── Per-cluster charts & export (ALL scans, zoomed) ──
    st.divider()
    sec("Mode Group Charts",
        "每组图表包含所有扫描，自动放大到该模式的频率区间")

    n_groups = len(cluster_info)
    if n_groups <= 2:
        _mg_cols = st.columns(n_groups)
    else:
        _mg_cols = None

    for ci_idx, c in enumerate(cluster_info):
        if _mg_cols is not None:
            _mg_container = _mg_cols[ci_idx]
        else:
            if ci_idx % 2 == 0:
                _mg_row = st.columns(2)
            _mg_container = _mg_row[ci_idx % 2]

        with _mg_container:
            st.markdown(f"**Mode {c['id']+1} — {c['center']:.3f} THz**")

            zoom_margin = max(0.3, (c['max_freq'] - c['min_freq']) / 2 + 0.3)
            zoom_lo = c['center'] - zoom_margin
            zoom_hi = c['center'] + zoom_margin

            n_f = len(files)
            colors_f = get_colors(n_f)
            fig_mg = plotly_fig(320,
                f"Mode {c['id']+1} @ {c['center']:.3f} THz")

            for j, d in enumerate(
                    sorted(files, key=lambda x: x['temperature'])):
                fa = d['freq'].astype(float)
                aa = d['amp'].astype(float)
                zmask = (fa >= zoom_lo) & (fa <= zoom_hi)
                if zmask.sum() < 2:
                    continue
                fig_mg.add_trace(go.Scatter(
                    x=fa[zmask], y=aa[zmask], mode='lines',
                    name=f"{d['temperature']:.0f} K",
                    line=dict(color=colors_f[j], width=1.2)))

            fig_mg.add_vrect(x0=c['min_freq'] - 0.02,
                             x1=c['max_freq'] + 0.02,
                             fillcolor="#c0392b", opacity=0.08,
                             line_width=0)
            fig_mg.update_xaxes(title_text='Frequency (THz)',
                                range=[zoom_lo, zoom_hi])
            fig_mg.update_yaxes(title_text=_amp_label)
            fig_mg.update_layout(
                legend=dict(yanchor="top", y=1, xanchor="left", x=1.02,
                            bgcolor="rgba(255,255,255,0.8)"),
                margin=dict(l=40, r=10, t=40, b=40))
            st.plotly_chart(fig_mg, use_container_width=True,
                            config={'editable': True})

            # Per-group Excel export
            export_data = {}
            for d in sorted(files, key=lambda x: x['temperature']):
                fa = d['freq'].astype(float)
                aa = d['amp'].astype(float)
                zmask = (fa >= zoom_lo) & (fa <= zoom_hi)
                if zmask.sum() < 2:
                    continue
                col_name = f"{d['temperature']:.0f}K"
                if 'Frequency_THz' not in export_data:
                    export_data['Frequency_THz'] = fa[zmask]
                export_data[col_name] = np.interp(
                    export_data['Frequency_THz'], fa[zmask], aa[zmask])

            if export_data:
                export_df = pd.DataFrame(export_data)
                output_xls = io.BytesIO()
                with pd.ExcelWriter(output_xls, engine='openpyxl') as xw:
                    export_df.to_excel(xw, index=False,
                        sheet_name=f'Mode{c["id"]+1}_{c["center"]:.2f}THz')
                st.download_button(
                    f"⬇ Export Mode {c['id']+1} (.xlsx)",
                    data=output_xls.getvalue(),
                    file_name=f"Mode_{c['id']+1}_{c['center']:.2f}THz.xlsx",
                    mime="application/vnd.openxmlformats-officedocument"
                         ".spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"mg_export_{c['id']}")





# TAB 1 — ROI & Fano fitting
# ─────────────────────────────────────────────────
with tab1:
    sec("File Overview", "文件列表与频率范围")
    tbl = pd.DataFrame([{
        "Filename": d['filename'],
        "T (K)":    d['temperature'],
        "f range (THz)": (f"{d['freq'].min():.3f} – {d['freq'].max():.3f}"
                          if len(d['freq']) else "—"),
        "Points":   len(d['freq']),
    } for d in files])
    st.dataframe(tbl, use_container_width=True, height=170,
                 hide_index=True)

    st.divider()
    sec("ROI Selection", "感兴趣区域选择（将统一应用到所有文件）")

    # ── Formula documentation ──
    with st.expander("📐 Fano Resonance — Formulas & Theory / 公式与理论", expanded=False):
        st.markdown("### Fano Resonance Model / Fano 共振模型")
        st.latex(FANO_FORMULA.strip().replace('$$',''))
        st.markdown(FANO_EXPLANATION)
        st.markdown("---")
        st.markdown("### Parameters / 参数说明")
        for k, v in FANO_PARAMS.items():
            st.markdown(f"**{k}** (`{v['unit']}`): {v['name']}")
            st.caption(v['desc'])
        st.markdown("---")
        st.markdown("### Derived Quantities / 导出量")
        for title, formula, expl in [
            ("Peak Depth (dB)", DEPTH_DB_FORMULA, DEPTH_DB_EXPLANATION),
            ("Linear Depth / 线性深度", LINEAR_DEPTH_FORMULA, LINEAR_DEPTH_EXPLANATION),
            ("FWHM / 半高全宽", FWHM_FORMULA, FWHM_EXPLANATION),
            ("Integrated Area / 积分面积", AREA_FORMULA, AREA_EXPLANATION),
            ("R² / 决定系数", R_SQUARED_FORMULA, R_SQUARED_EXPLANATION),
        ]:
            st.markdown(f"**{title}**")
            st.latex(formula.strip().replace('$$',''))
            st.caption(expl)

    # ── Editable fitting bounds ──
    with st.expander("⚙️ Advanced: Fano Fitting Bounds / 高级：拟合参数边界", expanded=False):
        st.caption("Adjust the parameter bounds for Fano fitting. "
                   "调整 Fano 拟合的参数边界约束。")
        adv_c1, adv_c2 = st.columns(2)
        with adv_c1:
            kappa_max = st.number_input("κ max", 0.1, 10.0, 2.0, 0.1,
                                        key="kappa_max")
            gamma_max = st.number_input("γ max", 0.1, 10.0, 2.0, 0.1,
                                        key="gamma_max")
        with adv_c2:
            phi_range = st.slider("φ range (rad)", -3.14, 3.14,
                                  (-3.14, 3.14), 0.01, key="phi_range")
            max_iter  = st.number_input("Max iterations / 最大迭代",
                                        1000, 50000, 10000, 1000,
                                        key="max_iter")
        st.session_state['adv_fano'] = {
            'kappa_max': kappa_max, 'gamma_max': gamma_max,
            'phi_range': phi_range, 'max_iter': int(max_iter),
        }

    col_ctrl, col_plot = st.columns([1, 3])
    with col_ctrl:
        view_mode = st.radio("View mode / 查看模式",
                             ["Single file 单文件",
                              "All overlay 全部叠加",
                              "Raw scans (select/exclude) 原始扫描"],
                             key="roi_view_mode")

        if "Single" in view_mode:
            idx = st.selectbox("Preview file  预览文件",
                range(len(files)),
                format_func=lambda i:
                    f"{files[i]['filename']} ({files[i]['temperature']:.0f} K)")
        sel = files[idx] if "Single" in view_mode else files[0]
        fa  = sel['freq'].astype(float)
        flo, fhi = float(fa.min()), float(fa.max())

        # Auto ROI Detection logic
        st.write("### Target Frequency (Auto-detect anchor)")
        target_f = st.number_input("Look for Fano dip near (THz)", min_value=flo, max_value=fhi, value=1.0, step=0.05, key='target_f')
        
        def run_auto_roi():
            try:
                from scipy.signal import find_peaks
                # Use the lowest temperature data for best peak visibility
                low_t_data = min(files, key=lambda d: d['temperature'])
                y_sm = pd.Series(low_t_data['amp'].astype(float)).rolling(window=5, center=True).mean().fillna(method='bfill').fillna(method='ffill').values
                
                # Fano in transmission is a dip, so we invert the signal to find peaks
                inverted_y = -y_sm + np.max(y_sm)
                
                # Find prominent peaks (dips)
                peaks, properties = find_peaks(inverted_y, width=3, prominence=np.max(inverted_y)*0.02)
                
                if len(peaks) > 0:
                    # Find the peak closest to the user's requested target frequency
                    peak_freqs = fa[peaks]
                    closest_peak_idx = peaks[np.argmin(np.abs(peak_freqs - st.session_state['target_f']))]
                    center_freq = fa[closest_peak_idx]
                    
                    # Set bounds roughly ±0.25 THz around the peak, bounded by data limits
                    init_l = np.clip(center_freq - 0.25, flo, fhi)
                    init_r = np.clip(center_freq + 0.25, flo, fhi)
                    if init_l < init_r:
                        st.session_state['roi_l_val'] = float(init_l)
                        st.session_state['roi_r_val'] = float(init_r)
                        return
            except Exception as e:
                log.warning(f"Auto ROI failed: {e}")
            
            # Fallback if detection fails
            st.session_state['roi_l_val'] = float(np.clip(0.8, flo, fhi))
            st.session_state['roi_r_val'] = float(np.clip(1.3, flo, fhi))

        # Run Auto ROI on first load or when files change
        if 'roi_l_val' not in st.session_state or st.session_state.get('_files_changed', False):
            run_auto_roi()
            st.session_state['_files_changed'] = False
        
        # UI controls
        st.button("✨ Auto-detect Fano Dip  自动寻找共振区间", 
                  on_click=run_auto_roi, use_container_width=True)
        st.divider()

        st.write("### ROI Manual Override / 手动微调")
        def sync_l_slider(): st.session_state['roi_l_num'] = st.session_state['roi_l_val']
        def sync_l_num(): st.session_state['roi_l_val'] = st.session_state['roi_l_num']
        def sync_r_slider(): st.session_state['roi_r_num'] = st.session_state['roi_r_val']
        def sync_r_num(): st.session_state['roi_r_val'] = st.session_state['roi_r_num']
        
        if 'roi_l_num' not in st.session_state: st.session_state['roi_l_num'] = st.session_state['roi_l_val']
        if 'roi_r_num' not in st.session_state: st.session_state['roi_r_num'] = st.session_state['roi_r_val']

        st.caption("Left boundary (THz) 左边界")
        _rl1, _rl2 = st.columns([2, 1])
        with _rl1:
            roi_l = st.slider("Left THz", flo, fhi,
                              float(np.clip(st.session_state['roi_l_val'], flo, fhi)), 0.005,
                              key='roi_l_val', on_change=sync_l_slider, label_visibility='collapsed')
        with _rl2:
            roi_l = st.number_input("Left", flo, fhi, st.session_state['roi_l_num'], 0.005,
                                    format="%.3f", key='roi_l_num', on_change=sync_l_num,
                                    label_visibility='collapsed')

        st.caption("Right boundary (THz) 右边界")
        _rr1, _rr2 = st.columns([2, 1])
        with _rr1:
            roi_r = st.slider("Right THz", flo, fhi,
                              float(np.clip(st.session_state['roi_r_val'], flo, fhi)), 0.005,
                              key='roi_r_val', on_change=sync_r_slider, label_visibility='collapsed')
        with _rr2:
            roi_r = st.number_input("Right", flo, fhi, st.session_state['roi_r_num'], 0.005,
                                    format="%.3f", key='roi_r_num', on_change=sync_r_num,
                                    label_visibility='collapsed')

        if roi_l >= roi_r:
            st.error("Left boundary must be < right boundary")
        
        # Explicit bounds protection
        roi_l = max(roi_l, flo)
        roi_r = min(roi_r, fhi)
        st.session_state.roi = (roi_l, roi_r)

        do_fit = st.button("▶  Run batch Fano fitting\\n批量拟合",
                           type="primary", use_container_width=True)

    with col_plot:
        if "Single" in view_mode:
            # ── Single file preview ──
            aa = sel['amp'].astype(float)
            fig = plotly_fig(380, f"{sel['filename']}  ·  {sel['temperature']:.0f} K")
            fig.add_trace(go.Scatter(x=fa, y=aa, mode='lines',
                name='Spectrum', line=dict(color='#334466', width=1.2)))
            mask = (fa >= roi_l) & (fa <= roi_r)
            fig.add_trace(go.Scatter(x=fa[mask], y=aa[mask], mode='lines',
                name='ROI', line=dict(color='#c0392b', width=2.2)))
            fig.add_vrect(x0=roi_l, x1=roi_r, fillcolor="#c0392b",
                          opacity=0.07, line_width=0)
            fig.update_xaxes(title_text="Frequency (THz)")
            fig.update_yaxes(title_text=_amp_label)
            st.plotly_chart(fig, use_container_width=True, config={'editable': True})

        elif "Raw" in view_mode:
            # ── Raw scans with select/exclude controls ──
            _all_raw = st.session_state.files
            _plot_raw = raw_files  # use the properly formatted data (Linear or dB) for plotting
            if 'excluded_scans' not in st.session_state:
                st.session_state.excluded_scans = set()

            n_raw = len(_plot_raw)
            colors_raw = get_colors(n_raw)
            fig = plotly_fig(500,
                f"All Raw Scans ({n_raw} files) — "
                f"uncheck to exclude  取消勾选排除异常扫描")

            for i, d in enumerate(_plot_raw):
                fname = d['filename']
                is_excl = fname in st.session_state.excluded_scans
                opacity = 0.15 if is_excl else 0.85
                lw = 0.5 if is_excl else 1.3
                dash = 'dot' if is_excl else 'solid'
                fig.add_trace(go.Scatter(
                    x=d['freq'].astype(float),
                    y=d['amp'].astype(float),
                    mode='lines',
                    name=f"{'❌ ' if is_excl else ''}{d['temperature']:.0f}K {fname}",
                    line=dict(color=colors_raw[i], width=lw, dash=dash),
                    opacity=opacity,
                    legendgroup=fname,
                    hovertemplate=(
                        f"<b>{d['temperature']:.0f} K</b><br>"
                        f"{fname}<br>"
                        f"f = %{{x:.3f}} THz<br>"
                        f"amp = %{{y:.4f}}<extra></extra>"),
                ))

            fig.add_vrect(x0=roi_l, x1=roi_r, fillcolor="#c0392b",
                          opacity=0.07, line_width=0,
                          annotation_text="ROI",
                          annotation_position="top left")
            fig.update_xaxes(title_text="Frequency (THz)")
            fig.update_yaxes(title_text=_amp_label)
            fig.update_layout(legend=dict(title="Scans",
                                          orientation='v', x=1.01,
                                          font=dict(size=8)))
            st.plotly_chart(fig, use_container_width=True, config={'editable': True})

            # ── Per-file checkboxes ──
            st.markdown("**Select scans to keep  勾选要保留的扫描（取消勾选 = 排除）**")

            # Group raw files by temperature for organized display
            from collections import defaultdict
            temp_file_map = defaultdict(list)
            for d in _all_raw:
                temp_file_map[d['temperature']].append(d['filename'])

            for temp_k in sorted(temp_file_map.keys()):
                fnames_in_temp = temp_file_map[temp_k]
                if len(fnames_in_temp) <= 1:
                    continue  # no need for exclusion if only 1 scan
                st.caption(f"**{temp_k:.0f} K** — {len(fnames_in_temp)} scans")
                chk_cols = st.columns(min(len(fnames_in_temp), 4))
                for j, fname in enumerate(fnames_in_temp):
                    with chk_cols[j % len(chk_cols)]:
                        keep = st.checkbox(
                            fname,
                            value=(fname not in st.session_state.excluded_scans),
                            key=f"roi_excl_{fname}",
                        )
                        if not keep:
                            st.session_state.excluded_scans.add(fname)
                        else:
                            st.session_state.excluded_scans.discard(fname)

            # Action buttons
            n_excl = len(st.session_state.excluded_scans)
            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if st.button(
                    "🔄 Apply & Re-average  应用并重新平均",
                    type="primary", use_container_width=True,
                    key="roi_reavg_btn"):
                    kept = [f for f in _all_raw
                            if f['filename'] not in st.session_state.excluded_scans]
                    if not kept:
                        st.error("Cannot exclude all scans!  不能排除所有数据！")
                    elif n_excl == 0:
                        st.info("No scans excluded. Nothing to change.  没有排除任何扫描。")
                    else:
                        avg_new, grp_new = average_by_temperature(kept)
                        st.session_state.averaged_files = avg_new
                        st.session_state.avg_group_info = grp_new
                        st.session_state.results = {}
                        st.session_state.df = None
                        log.info(f"Re-averaged from ROI tab: "
                                 f"{len(kept)}/{len(_all_raw)} kept, "
                                 f"excluded={st.session_state.excluded_scans}")
                        st.rerun()
            with btn_c2:
                if st.button("↺ Reset all  重置", use_container_width=True,
                             key="roi_reset_btn"):
                    st.session_state.excluded_scans = set()
                    avg_new, grp_new = average_by_temperature(_all_raw)
                    st.session_state.averaged_files = avg_new
                    st.session_state.avg_group_info = grp_new
                    st.session_state.results = {}
                    st.session_state.df = None
                    log.info("ROI tab: exclusions reset")
                    st.rerun()

            zh(f"实线 = 保留 · 虚线/半透明 = 已排除 · "
               f"当前排除 {n_excl} 个扫描 · "
               f"点击「应用并重新平均」后会重新计算平均数据并清除之前的拟合结果")

        else:
            # ── All files overlay ──
            n_files = len(files)
            colors_all = get_colors(n_files)
            fig = plotly_fig(480, f"All Spectra ({n_files} files)  ·  全部光谱叠加")
            for i, d in enumerate(files):
                fx = d['freq'].astype(float)
                fy = d['amp'].astype(float)
                show_leg = (i == 0 or i == n_files - 1 or n_files <= 8)
                fig.add_trace(go.Scatter(
                    x=fx, y=fy, mode='lines',
                    name=f"{d['temperature']:.0f} K",
                    line=dict(color=colors_all[i], width=1.0),
                    showlegend=show_leg,
                    legendgroup=str(i),
                    hovertemplate=(
                        f"<b>{d['temperature']:.0f} K</b><br>"
                        f"f = %{{x:.3f}} THz<br>"
                        f"amp = %{{y:.4f}}<extra></extra>"),
                ))
            fig.add_vrect(x0=roi_l, x1=roi_r, fillcolor="#c0392b",
                          opacity=0.07, line_width=0,
                          annotation_text="ROI", annotation_position="top left")
            fig.update_xaxes(title_text="Frequency (THz)")
            fig.update_yaxes(title_text=_amp_label)
            fig.update_layout(legend=dict(title="Temperature",
                                          orientation='v', x=1.01))
            st.plotly_chart(fig, use_container_width=True, config={'editable': True})

            # --- Export Overlay Data ---
            dfs = []
            for d in files:
                df_temp = pd.DataFrame({
                    'Freq_Rounded': np.round(d['freq'].astype(float), 4),
                    f'Amplitude_{d["temperature"]:.0f}K': d['amp']
                })
                # Drop potential duplicates due to rounding
                df_temp = df_temp.drop_duplicates(subset=['Freq_Rounded']).set_index('Freq_Rounded')
                dfs.append(df_temp)

            # Concatenate all dataframes along columns based on the rounded frequency index
            df_export = pd.concat(dfs, axis=1).sort_index()
            df_export.index.name = 'Frequency (THz)'
            df_export.reset_index(inplace=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Overlay Spectra')

            st.download_button(
                label="📥 Export Overlay Spectra to Excel",
                data=output.getvalue(),
                file_name="overlay_spectra.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            zh(f"颜色：蓝→低温，红→高温 · 共 {n_files} 条曲线 · "
               "阴影区域为选定的 ROI 范围")

    # ── batch fitting ──────────────────────────────
    if do_fit:
        fitter = FanoFitter(smooth_window=smooth_w, remove_outliers=rm_bad)
        roi    = st.session_state.roi
        prog   = st.progress(0)
        stat   = st.empty()
        results= {}
        log.info(f"Batch Fano fitting started: {len(files)} files, ROI={roi}")
        for i, d in enumerate(files):
            stat.text(f"Fitting {d['filename']}  ({i+1}/{len(files)}) …")
            try:
                r = fitter.fit(d['freq'].astype(float),
                               d['amp'].astype(float),
                               roi, d['temperature'], d['filename'])
                results[d['filename']] = r
                log.info(f"  ✓ {d['temperature']:.0f} K  R²={r['R_squared']:.4f}")
            except Exception as e:
                st.warning(f"⚠️ {d['filename']}: {e}")
                log.warning(f"  ✗ {d['filename']}: {e}")
                results[d['filename']] = None
            prog.progress((i+1)/len(files))
        st.session_state.results = results
        ok = [r for r in results.values() if r]
        st.session_state.df = pd.DataFrame(ok) if ok else None
        st.session_state.step = 3
        prog.empty(); stat.empty()
        log.info(f"Fitting complete: {len(ok)}/{len(files)} successful")
        st.success(f"✅ Fitting complete · 拟合完成  —  "
                   f"{len(ok)}/{len(files)} successful")
        st.rerun()

    # ── results table ──────────────────────────────
    if st.session_state.df is not None:
        st.divider()
        sec("Fitting Results", "拟合结果汇总 · 绿色 R²>0.97 · 红色 R²<0.90")
        cols_show = ['Temperature_K','Peak_Freq_THz','Depth_dB',
                     'Linear_Depth','FWHM_THz','Area','R_squared']
        df_s = (st.session_state.df[cols_show]
                .sort_values('Temperature_K')
                .rename(columns={
                    'Temperature_K':'T (K)',
                    'Peak_Freq_THz':'f_r (THz)',
                    'Depth_dB':'h (dB)',
                    'Linear_Depth':'Depth (a.u.)',
                    'FWHM_THz':'FWHM (THz)',
                    'Area':'Area (a.u.·THz)',
                    'R_squared':'R²',
                }))

        def _r2_style(val):
            if val > 0.97: return 'background-color:#d4edda;color:#155724'
            if val < 0.90: return 'background-color:#f8d7da;color:#721c24'
            return 'background-color:#fff3cd;color:#856404'

        styled = (df_s.style
                  .map(_r2_style, subset=['R²'])
                  .format({'T (K)':'{:.1f}','f_r (THz)':'{:.4f}',
                           'h (dB)':'{:.2f}','Depth (a.u.)':'{:.4f}',
                           'FWHM (THz)':'{:.4f}','Area (a.u.·THz)':'{:.5f}',
                           'R²':'{:.4f}'}))
        st.dataframe(styled, use_container_width=True, height=300,
                     hide_index=True)

        # ── quick trend row ────────────────────────
        df   = st.session_state.df.sort_values('Temperature_K')
        T    = df['Temperature_K'].values.astype(float)
        c1,c2,c3 = st.columns(3)
        for container, ycol, ylab, color in [
            (c1,'Peak_Freq_THz','f_r (THz)','#1a5f8a'),
            (c2,'Linear_Depth', 'Depth (a.u.)','#c0392b'),
            (c3,'FWHM_THz',     'FWHM (THz)','#27ae60'),
        ]:
            f2 = plotly_fig(230, ylab)
            f2.add_trace(go.Scatter(x=T, y=df[ycol].values,
                mode='markers+lines',
                marker=dict(size=6, color=color,
                            line=dict(width=1, color='#111')),
                line=dict(color=color, width=1.0, dash='dot')))
            f2.update_xaxes(title_text='Temperature (K)')
            f2.update_yaxes(title_text=ylab)
            container.plotly_chart(f2, use_container_width=True)

# ─────────────────────────────────────────────────
# TAB 2 — BCS analysis
# ─────────────────────────────────────────────────
with tab2:
    if st.session_state.df is None:
        st.info("Complete Fano fitting in Tab ② first.  请先在 ② 完成拟合。")
        st.stop()

    sec("BCS Order Parameter Fitting",
        "BCS序参量温度依赖拟合 · Δ(T) = A·tanh(β√(Tc/T−1))")
    zh("公式来源：BCS超导理论类比，广泛用于CDW/激子绝缘体相变表征")

    # ── Formula documentation ──
    with st.expander("📐 BCS Order Parameter — Formulas & Theory / 公式与理论", expanded=False):
        st.latex(BCS_FORMULA.strip().replace('$$',''))
        st.markdown(BCS_EXPLANATION)
        st.markdown("---")
        st.markdown("### Parameters / 参数说明")
        for k, v in BCS_PARAMS.items():
            st.markdown(f"**{k}** (`{v['unit']}`): {v['name']}")
            st.caption(v['desc'])

    # ── Editable BCS bounds ──
    with st.expander("⚙️ Advanced: BCS Fitting Bounds / 高级：BCS拟合边界", expanded=False):
        bcs_c1, bcs_c2 = st.columns(2)
        with bcs_c1:
            tc_lo = st.number_input("T_c lower bound (K)", 200.0, 400.0, 290.0, 5.0, key="tc_lo")
            tc_hi = st.number_input("T_c upper bound (K)", 200.0, 500.0, 360.0, 5.0, key="tc_hi")
        with bcs_c2:
            beta_lo = st.number_input("β lower bound", 0.1, 5.0, 0.3, 0.1, key="beta_lo")
            beta_hi = st.number_input("β upper bound", 0.5, 10.0, 8.0, 0.5, key="beta_hi")
        st.session_state['adv_bcs'] = {
            'tc_bounds': (tc_lo, tc_hi), 'beta_bounds': (beta_lo, beta_hi),
        }

    df  = st.session_state.df.sort_values('Temperature_K')
    bcs = BCSAnalyzer(tc_fixed=tc_fixed)
    T   = df['Temperature_K'].values.astype(float)
    T_s = np.linspace(T.min()*0.82, max(T.max()+15, 360), 600)
    colors_bcs = ['#1a5f8a','#27ae60']

    def bcs_panel(y, ylab, color, key):
        params = bcs.fit(T, y)
        fig = plotly_fig(380, f'{ylab} vs Temperature')
        fig.add_trace(go.Scatter(x=T, y=y, mode='markers',
            name='Experimental data',
            marker=dict(size=8, color=color,
                        line=dict(width=1.2, color='#111'),
                        symbol='circle')))
        if params:
            A, Tc, beta = params
            ys = bcs.bcs(T_s, A, Tc, beta)
            fig.add_trace(go.Scatter(x=T_s, y=ys,
                mode='lines', name=f'BCS fit  T_c={Tc:.1f} K  β={beta:.2f}',
                line=dict(color='#c0392b', width=2.2)))
            fig.add_vline(x=Tc, line_dash='dash', line_color='#888',
                          line_width=1.0,
                          annotation_text=f'T_c = {Tc:.1f} K',
                          annotation_position='top right',
                          annotation_font_size=11)
            st.session_state.fitted_tc = f"{Tc:.1f} K"
        fig.update_xaxes(title_text='Temperature (K)')
        fig.update_yaxes(title_text=ylab, rangemode='tozero')
        # Allow plotly to auto-place legend outside data bounds
        fig.update_layout(legend=dict(yanchor="top", y=1, xanchor="left", x=1.02, bgcolor="rgba(255,255,255,0.8)"))
        return fig, params

    col_a, col_b = st.columns(2)
    with col_a:
        fa, pa = bcs_panel(df['Linear_Depth'].values.astype(float),
                           'Peak Depth (a.u.)', colors_bcs[0], 'd')
        st.plotly_chart(fa, use_container_width=True, config={'editable': True})
        if pa:
            st.markdown(
                f'<span class="chip">T_c = {pa[1]:.2f} K</span>'
                f'<span class="chip">β = {pa[2]:.3f}</span>'
                f'<span class="chip">A = {pa[0]:.4f}</span>',
                unsafe_allow_html=True)
            zh("深度拟合：峰谷与基线之差，直接体现序参量大小")

    with col_b:
        fb, pb = bcs_panel(df['Area'].values.astype(float),
                           'Integrated Area (a.u.·THz)', colors_bcs[1], 'a')
        st.plotly_chart(fb, use_container_width=True, config={'editable': True})
        if pb:
            st.markdown(
                f'<span class="chip">T_c = {pb[1]:.2f} K</span>'
                f'<span class="chip">β = {pb[2]:.3f}</span>',
                unsafe_allow_html=True)
            zh("面积拟合：积分振子强度，对噪声更鲁棒")

    st.divider()
    sec("Phonon Frequency & Linewidth", "声子频率软化与线宽展宽")
    col_c, col_d = st.columns(2)
    with col_c:
        fc = plotly_fig(320, 'Phonon Frequency vs Temperature')
        fc.add_trace(go.Scatter(x=T,
            y=df['Peak_Freq_THz'].values.astype(float),
            mode='markers+lines',
            marker=dict(size=7, color='#b5860d',
                        line=dict(width=1.2,color='#111')),
            line=dict(color='#b5860d', width=1.0, dash='dot'),
            name='f_r'))
        fc.update_xaxes(title_text='Temperature (K)')
        fc.update_yaxes(title_text='Frequency (THz)')
        st.plotly_chart(fc, use_container_width=True, config={'editable': True})
        zh("声子软化/硬化反映晶格动力学随相变的演化")
    with col_d:
        fd = plotly_fig(320, 'Phonon Linewidth (FWHM) vs Temperature')
        fd.add_trace(go.Scatter(x=T,
            y=df['FWHM_THz'].values.astype(float),
            mode='markers+lines',
            marker=dict(size=7, color='#8e44ad',
                        line=dict(width=1.2,color='#111')),
            line=dict(color='#8e44ad', width=1.0, dash='dot'),
            name='FWHM'))
        fd.update_xaxes(title_text='Temperature (K)')
        fd.update_yaxes(title_text='FWHM (THz)', rangemode='tozero')
        st.plotly_chart(fd, use_container_width=True, config={'editable': True})
        zh("线宽展宽反映声子寿命缩短，与散射率增大相关")

# ─────────────────────────────────────────────────
# TAB 3 — Waterfall
# ─────────────────────────────────────────────────
with tab3:
    if not st.session_state.results:
        st.info("Complete Fano fitting in Tab ② first.  请先在 ② 完成拟合。")
        st.stop()

    sec("Temperature-Dependent Spectra (Waterfall)",
        "温度演化瀑布图 · 偏移量 = 峰高 × offset系数")

    # ── Formula documentation ──
    with st.expander("📐 Waterfall Offset — Formula / 偏移公式", expanded=False):
        st.latex(WATERFALL_FORMULA.strip().replace('$$',''))
        st.markdown(WATERFALL_EXPLANATION)
        st.markdown("---")
        st.markdown(
            "**Parameters / 参数**\\n\\n"
            "- **i**: curve index (sorted by temperature) / 曲线索引（按温度排序）\\n"
            "- **median(peak heights)**: auto-calculated from fitting results / 自动从拟合结果计算\\n"
            "- **m**: user-adjustable multiplier (slider below) / 用户可调乘子（下方滑块）"
        )

    ctl1, ctl2, ctl3 = st.columns(3)
    with ctl1:
        st.caption("Vertical offset 纵向偏移系数")
        _wo1, _wo2 = st.columns([2, 1])
        with _wo1:
            offset_mult = st.slider("Offset", 0.5, 5.0, 1.8, 0.1,
                                    key='wf_off_s', label_visibility='collapsed')
        with _wo2:
            offset_mult = st.number_input("Offset", 0.5, 5.0, offset_mult, 0.1,
                                          key='wf_off_n', label_visibility='collapsed')
        x_lo = st.number_input("x min (THz)", value=0.60, step=0.05)
        x_hi = st.number_input("x max (THz)", value=1.60, step=0.05)
    with ctl2:
        show_fit_wf = st.checkbox("Overlay Fano fit  叠加拟合曲线", False)
        st.caption("Label every N curves 每N条标温度")
        _nl1, _nl2 = st.columns([2, 1])
        with _nl1:
            n_label = st.slider("N", 1, 5, 2, key='nl_s',
                                label_visibility='collapsed')
        with _nl2:
            n_label = st.number_input("N", 1, 5, n_label, 1,
                                      key='nl_n', label_visibility='collapsed')
    with ctl3:
        st.caption("Plot height (px) 图高")
        _ph1, _ph2 = st.columns([2, 1])
        with _ph1:
            wf_height = st.slider("H", 400, 1000, 650, 50,
                                  key='wfh_s', label_visibility='collapsed')
        with _ph2:
            wf_height = st.number_input("H", 400, 1000, wf_height, 50,
                                        key='wfh_n', label_visibility='collapsed')

    ok_items_all = sorted(
        [(k,v) for k,v in st.session_state.results.items() if v],
        key=lambda x: x[1]['Temperature_K'])

    # ── Temperature multiselect ──────────────────────────
    all_temps = [v['Temperature_K'] for _,v in ok_items_all]
    temp_labels = [f"{t:.0f} K" for t in all_temps]
    st.markdown("**Select temperatures to plot  选择要绘制的温度**")
    _sel_col1, _sel_col2 = st.columns([1, 4])
    with _sel_col1:
        select_all_wf = st.checkbox("Select all  全选", True, key="wf_sel_all")
    with _sel_col2:
        if select_all_wf:
            selected_temps = st.multiselect(
                "Temperatures  温度", temp_labels, default=temp_labels,
                key="wf_temps", label_visibility='collapsed')
        else:
            selected_temps = st.multiselect(
                "Temperatures  温度", temp_labels, default=[],
                key="wf_temps_partial", label_visibility='collapsed')

    # Filter ok_items to selected temperatures
    selected_set = set(selected_temps)
    ok_items = [(k,v) for k,v in ok_items_all
                if f"{v['Temperature_K']:.0f} K" in selected_set]

    if not ok_items:
        st.warning("No temperatures selected.  请至少选择一个温度。")
        st.stop()

    n_curves = len(ok_items)
    colors_wf = temp_cmap(n_curves)

    # auto offset from data
    peak_hs = [v['Linear_Depth'] for _,v in ok_items]
    med_h   = float(np.median(peak_hs)) if peak_hs else 1.0
    offset_step = med_h * offset_mult

    fig_wf = plotly_fig(wf_height,
        f'Temperature Evolution of Phonon Mode  ({n_curves} curves)')
    wf_export_rows = []  # for Excel export
    for i, (fname, r) in enumerate(ok_items):
        freq_r = r['freq_roi']
        sig    = r['signal']
        mask   = (freq_r >= x_lo) & (freq_r <= x_hi)
        fx, sy = freq_r[mask], sig[mask]
        if len(fx) == 0: continue
        offset = i * offset_step
        col    = colors_wf[i]
        temp   = r['Temperature_K']

        fig_wf.add_trace(go.Scatter(
            x=fx, y=sy+offset, mode='lines',
            line=dict(color=col, width=1.5),
            name=f'{temp:.0f} K',
            hovertemplate=(f'<b>{temp:.0f} K</b><br>'
                           f'f = %{{x:.3f}} THz<br>'
                           f'I = %{{y:.4f}}<extra></extra>')))

        if show_fit_wf:
            fit_s = r['fitted_signal'][mask]
            fig_wf.add_trace(go.Scatter(
                x=fx, y=fit_s+offset, mode='lines',
                line=dict(color=col, width=1.0, dash='dash'),
                showlegend=False, hoverinfo='skip'))

        if i % n_label == 0:
            fig_wf.add_annotation(
                x=x_hi+0.01, y=float(sy[-1])+offset if len(sy) else offset,
                xanchor='left', showarrow=False,
                text=f'<b>{temp:.0f} K</b>',
                font=dict(size=9.5, color=col))

        # Collect data for Excel export
        for j in range(len(fx)):
            wf_export_rows.append({
                'Temperature_K': temp,
                'Frequency_THz': float(fx[j]),
                'Signal': float(sy[j]),
                'Signal_with_offset': float(sy[j]) + offset,
                'Offset': offset,
            })

    fig_wf.update_xaxes(title_text='Frequency (THz)',
                        range=[x_lo, x_hi+0.14])
    fig_wf.update_yaxes(title_text='Intensity (arb. u., offset)',
                        showticklabels=False)
    fig_wf.update_layout(showlegend=False)
    st.plotly_chart(fig_wf, use_container_width=True, config={'editable': True})
    zh("颜色：蓝色→低温，红色→高温。偏移量自动以中位峰高为基准，避免曲线重叠。")

    # ── Waterfall data export ────────────────────────────
    if wf_export_rows:
        wf_df = pd.DataFrame(wf_export_rows)
        wf_buf = io.BytesIO()
        with pd.ExcelWriter(wf_buf, engine='openpyxl') as xw:
            # Long format sheet
            wf_df.to_excel(xw, sheet_name='Waterfall_Long', index=False)
            # Wide format: each temperature as a column pair
            for temp_val in sorted(wf_df['Temperature_K'].unique()):
                sub = wf_df[wf_df['Temperature_K'] == temp_val]
                wide_df = pd.DataFrame({
                    'Frequency_THz': sub['Frequency_THz'].values,
                    f'Signal_{temp_val:.0f}K': sub['Signal'].values,
                    f'Signal_offset_{temp_val:.0f}K': sub['Signal_with_offset'].values,
                })
                safe_name = f"T{temp_val:.0f}K"[:31]
                wide_df.to_excel(xw, sheet_name=safe_name, index=False)
        wf_buf.seek(0)
        st.download_button(
            "📥 Export Waterfall data (Excel)  导出瀑布图数据",
            data=wf_buf.getvalue(),
            file_name="Waterfall_Spectra_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
        zh("Excel 包含长格式汇总 Sheet 和每个温度的独立 Sheet（含原始信号与偏移后坐标）")

# ─────────────────────────────────────────────────
# TAB 4 — Dielectric
# ─────────────────────────────────────────────────
with tab4:
    if not diel_on:
        st.info("Enable **Dielectric calculation** in the sidebar.  "
                "请在左侧勾选启用介电计算。")
        st.stop()

    ref_data = st.session_state.ref_data
    if ref_data is None or len(ref_data.get('time',[]))==0:
        st.error("No reference file uploaded, or reference has no time-domain data.  "
                 "没有上传参考文件，或参考文件无时域数据。请在侧边栏上传参考基底文件。")
        st.stop()

    sec("Optical Constants & Dielectric Functions",
        "光学常数与复介电函数 · n, k, ε₁, ε₂")
    zh("方法：频域传输函数法 H(ω)=S_sam/S_ref → n(ω) → k(ω) → ε(ω)=ε₁+iε₂")

    # ── Formula documentation ──
    with st.expander("📐 Optical Constants — Formulas & Theory / 公式与理论", expanded=False):
        st.markdown("### Transfer Function / 传输函数")
        st.latex(TRANSFER_FUNC_FORMULA.strip().replace('$$',''))
        st.markdown("### Refractive Index / 折射率")
        st.latex(REFRACTIVE_INDEX_FORMULA.strip().replace('$$',''))
        st.markdown("### Extinction Coefficient / 消光系数")
        st.latex(EXTINCTION_FORMULA.strip().replace('$$',''))
        st.markdown("### Dielectric Function / 介电函数")
        st.latex(DIELECTRIC_FORMULA.strip().replace('$$',''))
        st.markdown("---")
        st.markdown(DIELECTRIC_EXPLANATION)
        st.markdown("### Parameters / 参数说明")
        for k, v in DIELECTRIC_PARAMS.items():
            st.markdown(f"**{k}** (`{v['unit']}`): {v['name']}")
            st.caption(v['desc'])

    # ── Editable dielectric parameters ──
    with st.expander("⚙️ Advanced: Dielectric Calculation Parameters / 高级：介电计算参数", expanded=False):
        diel_c1, diel_c2 = st.columns(2)
        with diel_c1:
            gain_limit = st.number_input("Gain limit / 增益限制", 0.5, 1.0, 0.85, 0.05,
                                         key="gain_limit",
                                         help="Max |H| normalization threshold")
            diel_smooth = st.number_input("Smoothing window / 平滑窗口", 1, 21, 5, 2,
                                          key="diel_smooth")
        with diel_c2:
            phase_fit_lo = st.number_input("Phase fit range low (THz)", 0.1, 2.0, 0.5, 0.1,
                                           key="phase_lo")
            phase_fit_hi = st.number_input("Phase fit range high (THz)", 0.5, 4.0, 1.0, 0.1,
                                           key="phase_hi")

    with st.spinner("Computing dielectric functions …  计算中 …"):
        calc    = DielectricCalculator(thickness=thickness)
        diel_rs = calc.calculate_all(ref_data, files)

    if not diel_rs:
        st.error("Calculation failed. Check reference file.  计算失败，请检查参考文件。")
        st.stop()

    st.session_state.diel = diel_rs
    diel_rs.sort(key=lambda x: x['temp'])
    nd = len(diel_rs)

    # Show all temperatures (no subsampling)
    subset = diel_rs
    colors_d = temp_cmap(len(subset))

    st.caption("Frequency range (THz) 频率范围")
    _fd1, _fd2, _fd3 = st.columns([1, 2, 1])
    with _fd1:
        f_lo_d = st.number_input("f_lo", 0.3, 4.0, 0.5, 0.05,
                                  format="%.2f", key='diel_flo')
    with _fd2:
        f_lo_d, f_hi_d = st.slider("Freq", 0.3, 4.0, (f_lo_d, 2.8), 0.05,
                                    key='diel_fs', label_visibility='collapsed')
    with _fd3:
        f_hi_d = st.number_input("f_hi", 0.3, 4.0, f_hi_d, 0.05,
                                  format="%.2f", key='diel_fhi')

    fig_d = make_subplots(rows=2, cols=2, horizontal_spacing=0.12,
                          vertical_spacing=0.14,
                          subplot_titles=['Refractive index  n',
                                          'Extinction coefficient  k',
                                          'Real permittivity  ε₁',
                                          'Imaginary permittivity  ε₂'])
    for i,(res,col) in enumerate(zip(subset, colors_d)):
        m  = (res['freq']>=f_lo_d) & (res['freq']<=f_hi_d)
        sl = (i==0 or i==len(subset)-1)
        kw = dict(mode='lines', line=dict(color=col,width=1.3),
                  name=f"{res['temp']:.0f} K", legendgroup=str(i),
                  showlegend=sl)
        fig_d.add_trace(go.Scatter(x=res['freq'][m],y=res['n'][m], **kw),
                        row=1,col=1)
        fig_d.add_trace(go.Scatter(x=res['freq'][m],y=res['k'][m],
                        **{**kw,'showlegend':False}), row=1,col=2)
        fig_d.add_trace(go.Scatter(x=res['freq'][m],y=res['e1'][m],
                        **{**kw,'showlegend':False}), row=2,col=1)
        fig_d.add_trace(go.Scatter(x=res['freq'][m],y=res['e2'][m],
                        **{**kw,'showlegend':False}), row=2,col=2)

    apply_plotly_style(fig_d, height=680,
                       title='Optical Constants — Temperature Dependence')
    for r,c in [(1,1),(1,2),(2,1),(2,2)]:
        fig_d.update_xaxes(title_text='Frequency (THz)',
                           showgrid=False, ticks='inside', row=r,col=c)
    fig_d.update_yaxes(title_text='n', row=1,col=1)
    fig_d.update_yaxes(title_text='k', row=1,col=2)
    fig_d.update_yaxes(title_text='ε₁', row=2,col=1)
    fig_d.update_yaxes(title_text='ε₂', row=2,col=2)
    fig_d.update_layout(legend=dict(title='Temperature',
                                    orientation='v', x=1.01))
    st.plotly_chart(fig_d, use_container_width=True, config={'editable': True})

    # low T vs high T comparison
    st.divider()
    sec("Low-T vs High-T Comparison  低温 vs 高温对比")
    lo_r,hi_r = diel_rs[0], diel_rs[-1]
    fig_cmp = plotly_fig(340,
        f'ε₂: {lo_r["temp"]:.0f} K vs {hi_r["temp"]:.0f} K')
    for res, col, lbl in [
        (lo_r,'#2980b9',f'Low-T  {lo_r["temp"]:.0f} K'),
        (hi_r,'#c0392b',f'High-T  {hi_r["temp"]:.0f} K'),
    ]:
        m = (res['freq']>=f_lo_d) & (res['freq']<=f_hi_d)
        fig_cmp.add_trace(go.Scatter(x=res['freq'][m], y=res['e2'][m],
            mode='lines', name=lbl, line=dict(color=col,width=2.2)))
    fig_cmp.update_xaxes(title_text='Frequency (THz)')
    fig_cmp.update_yaxes(title_text='ε₂ (Imaginary permittivity)')
    st.plotly_chart(fig_cmp, use_container_width=True, config={'editable': True})
    zh("ε₂ 在声子频率处出现峰值；低温下峰更尖锐，线宽更窄，反映声子寿命增长。")

# ─────────────────────────────────────────────────
# TAB 5 — Peak detail (publication figure)
# ─────────────────────────────────────────────────
with tab5:
    if not st.session_state.results:
        st.info("Complete Fano fitting in Tab ② first.  请先在 ② 完成拟合。")
        st.stop()

    sec("Single-Peak Detail View  单峰拟合详情",
        "选择任意温度查看完整拟合图，可直接导出用于论文")

    # ── Formula documentation ──
    with st.expander("📐 Fano Parameters — Complete Reference / 参数完整参考", expanded=False):
        st.markdown("### Fano Resonance Model")
        st.latex(FANO_FORMULA.strip().replace('$$',''))
        st.markdown(FANO_EXPLANATION)
        st.markdown("---")
        st.markdown("### All Parameters")
        for k, v in FANO_PARAMS.items():
            st.markdown(f"**{k}** (`{v['unit']}`): {v['name']}")
            st.caption(v['desc'])
        st.markdown("---")
        for title, formula, expl in [
            ("Peak Depth (dB)", DEPTH_DB_FORMULA, DEPTH_DB_EXPLANATION),
            ("Linear Depth", LINEAR_DEPTH_FORMULA, LINEAR_DEPTH_EXPLANATION),
            ("FWHM", FWHM_FORMULA, FWHM_EXPLANATION),
            ("Area", AREA_FORMULA, AREA_EXPLANATION),
            ("R²", R_SQUARED_FORMULA, R_SQUARED_EXPLANATION),
        ]:
            st.markdown(f"**{title}**")
            st.latex(formula.strip().replace('$$',''))
            st.caption(expl)

    ok_r = {k:v for k,v in st.session_state.results.items() if v}
    labels_5 = [f"{v['Temperature_K']:.0f} K  —  {k}"
                for k,v in sorted(ok_r.items(),
                                  key=lambda x: x[1]['Temperature_K'])]
    keys_5   = [k for k,_ in sorted(ok_r.items(),
                                    key=lambda x: x[1]['Temperature_K'])]

    sel5 = st.selectbox("Select temperature  选择温度",
                        range(len(labels_5)),
                        format_func=lambda i: labels_5[i])
    r = ok_r[keys_5[sel5]]

    # ── Plotly interactive ──
    fig5 = plotly_fig(420,
        f"Fano Fit  ·  {r['Temperature_K']:.0f} K  ·  "
        f"f_r = {r['Peak_Freq_THz']:.4f} THz  ·  R² = {r['R_squared']:.4f}")

    fx, sig, fit_s = r['freq_roi'], r['signal'], r['fitted_signal']
    half, lx, rx   = r['half_height'], r['left_x'], r['right_x']

    # shaded area
    fig5.add_trace(go.Scatter(
        x=np.concatenate([fx, fx[::-1]]),
        y=np.concatenate([sig, np.zeros(len(sig))]),
        fill='toself', fillcolor='rgba(44,110,165,0.12)',
        line=dict(width=0), name='Integrated area',
        hoverinfo='skip'))
    # signal
    fig5.add_trace(go.Scatter(x=fx, y=sig, mode='lines',
        name='Signal',
        line=dict(color='#1a5f8a', width=2.2)))
    # fano fit
    fig5.add_trace(go.Scatter(x=fx, y=fit_s, mode='lines',
        name='Fano fit',
        line=dict(color='#c0392b', width=2.0, dash='dash')))
    # depth
    fig5.add_shape(type='line', x0=r['peak_x'],x1=r['peak_x'],
                   y0=0, y1=r['Linear_Depth'],
                   line=dict(color='#27ae60',width=2.0,dash='dot'))
    fig5.add_annotation(x=r['peak_x'], y=r['Linear_Depth']*0.52,
        text=f"  Depth = {r['Linear_Depth']:.4f}",
        showarrow=False, xanchor='left',
        font=dict(color='#27ae60',size=11))
    # FWHM
    fig5.add_shape(type='line', x0=lx,x1=rx, y0=half,y1=half,
                   line=dict(color='#8e44ad',width=2.0))
    fig5.add_annotation(x=(lx+rx)/2, y=half*1.15,
        text=f"FWHM = {r['FWHM_THz']:.4f} THz",
        showarrow=False, font=dict(color='#8e44ad',size=11))

    fig5.update_xaxes(title_text='Frequency (THz)')
    fig5.update_yaxes(title_text='ΔAmplitude (a.u., baseline corrected)',
                      rangemode='tozero')
    fig5.update_layout(legend=dict(yanchor="top", y=1, xanchor="left", x=1.02, bgcolor="rgba(255,255,255,0.8)"))
    # Make plotly charts editable to allow manual legend dragging
    st.plotly_chart(fig5, use_container_width=True, config={'editable': True})

    # parameter metrics
    pc = st.columns(6)
    for col, lbl, val in zip(pc,
        ['f_r (THz)','κ (THz)','γ (THz)','φ (rad)','h (dB)','R²'],
        [r['Peak_Freq_THz'],r['Fano_Kappa'],r['Fano_Gamma'],
         r['Fano_Phi'],r['Depth_dB'],r['R_squared']]):
        col.metric(lbl, f"{val:.4f}")
    zh("f_r: 共振频率 · κ: 耦合强度 · γ: 本征线宽 · φ: Fano相位 · h: 峰深度(dB) · R²: 拟合优度")

    # ── Publication matplotlib figure ──────────────────────────
    st.divider()
    sec("Publication-Quality Figure (matplotlib)",
        "论文级静态图 · 现支持 Nature / Origin 排版风格")

    col_fig, col_opt = st.columns([3,1])
    with col_opt:
        plot_style = st.selectbox("Style 风格", ["Nature", "Origin"])
        fig_w_in = st.number_input("Width (in) 图宽(英寸)",
                                   2.5, 7.5, 3.5, 0.5)
        fig_h_in = st.number_input("Height (in) 图高(英寸)",
                                   2.0, 6.0, 3.0, 0.5)
        show_fill= st.checkbox("Show area fill 面积着色", True)
        show_ann = st.checkbox("Show annotations 显示标注", True)
        
        st.divider()
        export_fmt = st.selectbox("Format 格式", ['png', 'pdf', 'svg', 'eps'])
        export_dpi = st.select_slider("DPI 分辨率", [150, 300, 600], 300)

    with col_fig:
        if plot_style == 'Origin': apply_origin_style()
        else: apply_nature_style()
        
        fig_pub, ax = plt.subplots(figsize=(fig_w_in, fig_h_in))

        if show_fill:
            ax.fill_between(fx, 0, sig, color='#2c6ea5', alpha=0.12,
                            zorder=1)
        
        # Origin lines are slightly thicker, controlled automatically by RC params
        ax.plot(fx, sig, color='#1a5f8a', label='Signal', zorder=3)
        ax.plot(fx, fit_s, color='#c0392b', ls='--', label='Fano fit', zorder=4)

        if show_ann:
            ax.vlines(r['peak_x'], 0, r['Linear_Depth'],
                      colors='#27ae60', ls=':', zorder=2)
            ax.hlines(half, lx, rx,
                      colors='#8e44ad', zorder=2)
            ax.annotate(f"FWHM = {r['FWHM_THz']:.4f} THz",
                        xy=((lx+rx)/2, half),
                        xytext=((lx+rx)/2, half*1.3),
                        fontsize=matplotlib.rcParams['font.size'] - 1.5, 
                        color='#8e44ad', ha='center',
                        arrowprops=dict(arrowstyle='-',
                                        color='#8e44ad', lw=0.8))

        ax.set_xlabel('Frequency (THz)')
        ax.set_ylabel('ΔAmplitude (arb. u.)')
        ax.set_title(f'T = {r["Temperature_K"]:.0f} K',
                     pad=6, fontsize=matplotlib.rcParams['axes.titlesize'])
        ax.set_ylim(bottom=0)
        ax.legend(loc='best')
        format_ax(ax)
        if plot_style == 'Nature':
            panel_label(ax, 'a')
            plt.tight_layout(pad=0.2)
        else:
            # Origin plots rarely have 'a' panel labels inside the box, tighter layout
            plt.tight_layout(pad=0.1)

        buf_pub = io.BytesIO()
        fig_pub.savefig(buf_pub, format='png', dpi=export_dpi,
                        bbox_inches='tight')
        plt.close(fig_pub)
        buf_pub.seek(0)
        st.image(buf_pub, caption=(
            f"T = {r['Temperature_K']:.0f} K  ·  "
            f"f_r = {r['Peak_Freq_THz']:.4f} THz  ·  "
            f"R² = {r['R_squared']:.4f}"))

    # export this single figure
    st.download_button(
        f"⬇️  Download this figure (.{export_fmt})  下载此图",
        data=_single_fig_export(r, fig_w_in, fig_h_in,
                                export_dpi, export_fmt, plot_style),
        file_name=f"fano_{r['Temperature_K']:.0f}K.{export_fmt}",
        mime=f"image/{export_fmt}" if export_fmt!='pdf'
             else "application/pdf",
        use_container_width=True)

# ─────────────────────────────────────────────────
# TAB 6 — Export
# ─────────────────────────────────────────────────
with tab6:
    sec("Export Results  导出结果", "Excel数据 · 光谱数据 · PDF报告 · 高分辨率图集 · 公式文档")

    col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns(5)

    # Excel parameters
    with col_e1:
        st.markdown("### 📊 Parameters")
        zh("包含Fano参数、介电函数参数表")
        if st.session_state.df is not None:
            buf_xl = _make_excel(st.session_state.df,
                                 st.session_state.diel)
            st.download_button("⬇️  Download Excel",
                data=buf_xl, use_container_width=True,
                file_name="THz_Analysis_Results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Complete fitting first.  请先完成拟合。")

    # Spectra data TXT + Excel (NEW)
    with col_e2:
        st.markdown("### 📈 Spectra data")
        zh("所有温度的完整数据 (Excel/TXT皆可直接进Origin)")
        if st.session_state.results:
            ok_r = {k:v for k,v in st.session_state.results.items() if v}
            if ok_r:
                # ── Generate Excel ──
                spec_buf = io.BytesIO()
                with pd.ExcelWriter(spec_buf, engine='openpyxl') as xw:
                    # Sheet 1: Summary of all raw spectra (wide format)
                    raw_dfs = []
                    for d in files:
                        col_name = f"{d['temperature']:.0f}K"
                        tmp_df = pd.DataFrame({
                            'Freq_THz': np.round(d['freq'].astype(float), 4),
                            col_name: d['amp'].astype(float),
                        }).drop_duplicates(subset=['Freq_THz']).set_index('Freq_THz')
                        raw_dfs.append(tmp_df)
                    if raw_dfs:
                        raw_wide = pd.concat(raw_dfs, axis=1).sort_index()
                        raw_wide.index.name = 'Frequency (THz)'
                        raw_wide.reset_index(inplace=True)
                        raw_wide.to_excel(xw, sheet_name='Raw_Spectra', index=False)

                    # Sheet 2: Summary of all fitting ROI data (wide format)
                    fit_signal_dfs = []
                    fit_curve_dfs = []
                    for k, v in sorted(ok_r.items(), key=lambda x: x[1]['Temperature_K']):
                        t_lbl = f"{v['Temperature_K']:.0f}K"
                        fx = np.round(v['freq_roi'].astype(float), 4)
                        s_df = pd.DataFrame({
                            'Freq_THz': fx,
                            f'Signal_{t_lbl}': v['signal'].astype(float),
                        }).drop_duplicates(subset=['Freq_THz']).set_index('Freq_THz')
                        fit_signal_dfs.append(s_df)
                        f_df = pd.DataFrame({
                            'Freq_THz': fx,
                            f'FanoFit_{t_lbl}': v['fitted_signal'].astype(float),
                        }).drop_duplicates(subset=['Freq_THz']).set_index('Freq_THz')
                        fit_curve_dfs.append(f_df)

                    if fit_signal_dfs:
                        sig_wide = pd.concat(fit_signal_dfs, axis=1).sort_index()
                        sig_wide.index.name = 'Frequency (THz)'
                        sig_wide.reset_index(inplace=True)
                        sig_wide.to_excel(xw, sheet_name='ROI_Signal', index=False)

                    if fit_curve_dfs:
                        fit_wide = pd.concat(fit_curve_dfs, axis=1).sort_index()
                        fit_wide.index.name = 'Frequency (THz)'
                        fit_wide.reset_index(inplace=True)
                        fit_wide.to_excel(xw, sheet_name='Fano_Fit_Curves', index=False)

                    # Sheet 3: BCS plot data
                    if st.session_state.df is not None:
                        df_bcs = st.session_state.df.sort_values('Temperature_K')
                        bcs_df = df_bcs[['Temperature_K','Linear_Depth','Area',
                                         'Peak_Freq_THz','FWHM_THz']].copy()
                        bcs_df.to_excel(xw, sheet_name='BCS_Plot_Data', index=False)

                spec_buf.seek(0)
                st.download_button("⬇️  Excel (.xlsx)",
                    data=spec_buf.getvalue(), use_container_width=True,
                    file_name="THz_Spectra_Data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                # ── Generate TXT (Origin ready) from raw_wide ──
                if raw_dfs:
                    txt_data = raw_wide.to_csv(sep='\t', index=False)
                    st.download_button("⬇️  Origin TXT",
                        data=txt_data.encode('utf-8'), use_container_width=True,
                        file_name="Origin_Raw_Spectra.txt",
                        mime="text/plain")
            else:
                st.info("No fitting results.  无拟合结果。")
        else:
            st.info("Complete fitting first.  请先完成拟合。")

    # PDF report
    with col_e3:
        st.markdown("### 📄 PDF report")
        zh("包含BCS拟合图、瀑布图、所有代表性单峰拟合图")
        report_style = st.selectbox("Style", ["Nature", "Origin"], key="rep_style", label_visibility="collapsed")
        
        disabled_pdf = st.session_state.df is None
        if st.button("Generate PDF report  生成报告",
                     use_container_width=True, disabled=disabled_pdf):
            with st.spinner("Generating publication-quality PDF …  生成中 …"):
                buf_pdf = _make_pdf_report(
                    st.session_state.df,
                    st.session_state.results,
                    tc_fixed, export_dpi, report_style)
            st.download_button("⬇️  Download PDF",
                data=buf_pdf, use_container_width=True,
                file_name=f"THz_Analysis_Report_{report_style}.pdf",
                mime="application/pdf")

    # Figure pack
    with col_e4:
        st.markdown("### 🖼️ Figure pack")
        zh("所有温度的拟合图集整理打包为单一PDF卷宗")
        pack_style = st.selectbox("Style", ["Nature", "Origin"], key="pack_style", label_visibility="collapsed")
        if (st.button("Export all fit figures  导出图集",
                      use_container_width=True,
                      disabled=(not st.session_state.results))):
            with st.spinner("Rendering all figures …"):
                buf_all = _export_all_figs(
                    st.session_state.results, export_dpi, pack_style)
            st.download_button("⬇️  Download figure pack",
                data=buf_all, use_container_width=True,
                file_name=f"THz_All_Fits_{pack_style}.pdf",
                mime="application/pdf")

    # Formula documentation
    with col_e5:
        st.markdown("### 📐 Formula doc")
        zh("所有公式、参数说明、当前参数值的完整文档")
        # Collect current session parameters
        current_params = {
            "Smoothing window": smooth_w,
            "Remove outliers": rm_bad,
            "Export DPI": export_dpi,
            "Export format": export_fmt,
            "Sample thickness (mm)": thickness,
            "Dielectric enabled": diel_on,
        }
        if st.session_state.get('adv_fano'):
            af = st.session_state['adv_fano']
            current_params["Fano κ max"] = af['kappa_max']
            current_params["Fano γ max"] = af['gamma_max']
            current_params["Fano φ range"] = f"{af['phi_range']}"
            current_params["Fano max iterations"] = af['max_iter']
        if st.session_state.get('adv_bcs'):
            ab = st.session_state['adv_bcs']
            current_params["BCS T_c bounds (K)"] = f"{ab['tc_bounds']}"
            current_params["BCS β bounds"] = f"{ab['beta_bounds']}"
        if tc_fixed is not None:
            current_params["T_c fixed (K)"] = tc_fixed
        if st.session_state.get('fitted_tc'):
            current_params["Fitted T_c"] = st.session_state['fitted_tc']

        formula_md = generate_formula_doc(current_params)
        st.download_button("⬇️  Download formula doc",
            data=formula_md.encode('utf-8'),
            use_container_width=True,
            file_name="THz_Formula_Documentation.md",
            mime="text/markdown")

    st.divider()
    st.markdown("### 💾 Workspace Saving")
    zh("持久化保存当前分析会话（包含数据、参数和拟合结果）并生成Markdown总结报告")
    
    _ws1, _ws2 = st.columns([1, 4])
    with _ws1:
        session_name = st.text_input("Session Name 命名", value="MyExperiment", label_visibility="collapsed")
    with _ws2:
        if st.button("Save entire workspace and generate report  保存工作区", type="primary", use_container_width=True):
            if st.session_state.files:
                try:
                    with st.spinner("Saving session & generating report..."):
                        # dict() natively unrolls session_state to a python dict
                        saved_dir = SessionManager.save_session(session_name, dict(st.session_state))
                        st.success(f"✅ Session saved successfully to `{saved_dir}/`")
                        log.info(f"Session '{session_name}' saved to {saved_dir}")
                except Exception as e:
                    st.error(f"Failed to save session: {e}")
                    log.error(f"Session save failed: {e}")
            else:
                st.warning("Workspace is empty. Load files first. ")

# ─────────────────────────────────────────────────
# TAB 7 — History & Reports
# ─────────────────────────────────────────────────
with tab7:
    sec("History & Auto-Reports  历史记录与自动报告", "管理过去保存的分析会话，直接查看Markdown摘要文档")
    
    sessions = SessionManager.list_sessions()
    
    if not sessions:
        st.info("No saved sessions found. Save a workspace in the Export tab. 暂无保存的会话记录。")
    else:
        # Layout: Timeline on the left, Report viewer on the right
        col_list, col_view = st.columns([1, 3])
        
        with col_list:
            st.markdown("### Saved Sessions")
            for s in sessions:
                # Add a button for each session
                lbl = f"📁 {s['dir'][16:]}\n({s['date']})"
                if st.button(lbl, key=f"btn_{s['dir']}", use_container_width=True):
                    st.session_state['view_session_report'] = s['dir']
                    
        with col_view:
            st.markdown("### Report Viewer")
            target_sess = st.session_state.get('view_session_report')
            if target_sess:
                report_path = os.path.join("sessions", target_sess, "report.md")
                if os.path.exists(report_path):
                    with open(report_path, 'r', encoding='utf-8') as f:
                        md_content = f.read()
                    
                    st.markdown(md_content)
                    
                    st.divider()
                    st.caption(f"Raw data and parameters are stored in `{os.path.join('sessions', target_sess, 'workspace.json')}`")
                    
                    with open(report_path, 'r', encoding='utf-8') as f:
                        st.download_button("⬇️ Download this Report (.md)", data=f.read().encode('utf-8'),
                                          file_name=f"{target_sess}_report.md", mime="text/markdown", use_container_width=True)
                else:
                    st.warning("Report file missing for this session.")
            else:
                st.info("Select a session from the list to view its report.  在左侧选择要查看的记录。")


# ══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (defined after tabs to allow st.stop() above)
# ══════════════════════════════════════════════════════════════