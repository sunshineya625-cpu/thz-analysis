import streamlit as st
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import io
from ui_components.utils import sec, zh, plotly_fig
from modules.science_plot import apply_nature_style, format_ax, panel_label
from modules.formulas import (FANO_FORMULA, FANO_PARAMS, FANO_EXPLANATION,
                              DEPTH_DB_FORMULA, DEPTH_DB_EXPLANATION,
                              LINEAR_DEPTH_FORMULA, LINEAR_DEPTH_EXPLANATION,
                              FWHM_FORMULA, FWHM_EXPLANATION,
                              AREA_FORMULA, AREA_EXPLANATION,
                              R_SQUARED_FORMULA, R_SQUARED_EXPLANATION)

def _single_fig_export(r, w, h, dpi, fmt):
    apply_nature_style()
    fig, ax = plt.subplots(figsize=(w, h))
    fx, sig, fit_s = r['freq_roi'], r['signal'], r['fitted_signal']
    ax.fill_between(fx, 0, sig, color='#2c6ea5', alpha=0.12)
    ax.plot(fx, sig,   color='#1a5f8a', lw=1.4, label='Signal')
    ax.plot(fx, fit_s, color='#c0392b', lw=1.4, ls='--', label='Fano fit')
    ax.vlines(r['peak_x'], 0, r['Linear_Depth'], colors='#27ae60', lw=1.0, ls=':')
    ax.hlines(r['half_height'], r['left_x'], r['right_x'], colors='#8e44ad', lw=1.0)
    ax.set_xlabel('Frequency (THz)')
    ax.set_ylabel('ΔAmplitude (arb. u.)')
    ax.set_title(f"T = {r['Temperature_K']:.0f} K", pad=5, fontsize=8)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=True)
    format_ax(ax); panel_label(ax, 'a')
    plt.tight_layout(pad=0.4)
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf.read()

def render_tab_peak(export_dpi, export_fmt):
    if not st.session_state.results:
        st.info("Complete Fano fitting in Tab ① first.  请先在 ① 完成拟合。")
        st.stop()

    sec("Single-Peak Detail View  单峰拟合详情", "选择任意温度查看完整拟合图，可直接导出用于论文")

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
    labels_5 = [f"{v['Temperature_K']:.0f} K  —  {k}" for k,v in sorted(ok_r.items(), key=lambda x: x[1]['Temperature_K'])]
    keys_5   = [k for k,_ in sorted(ok_r.items(), key=lambda x: x[1]['Temperature_K'])]

    sel5 = int(st.selectbox("Select temperature  选择温度", range(len(labels_5)), format_func=lambda i: labels_5[i]))
    r = ok_r[keys_5[sel5]]

    fig5 = plotly_fig(420, f"Fano Fit  ·  {r['Temperature_K']:.0f} K  ·  f_r = {r['Peak_Freq_THz']:.4f} THz  ·  R² = {r['R_squared']:.4f}")

    fx, sig, fit_s = r['freq_roi'], r['signal'], r['fitted_signal']
    half, lx, rx   = float(r['half_height']), float(r['left_x']), float(r['right_x'])

    fig5.add_trace(go.Scatter(
        x=np.concatenate([fx, fx[::-1]]),
        y=np.concatenate([sig, np.zeros(len(sig))]),
        fill='toself', fillcolor='rgba(44,110,165,0.12)',
        line={'width': 0.0}, name='Integrated area  积分面积', hoverinfo='skip'))
    fig5.add_trace(go.Scatter(x=fx, y=sig, mode='lines', name='Signal  信号', line={'color': '#1a5f8a', 'width': 2.2}))
    fig5.add_trace(go.Scatter(x=fx, y=fit_s, mode='lines', name='Fano fit  Fano拟合', line={'color': '#c0392b', 'width': 2.0, 'dash': 'dash'}))
    fig5.add_shape(type='line', x0=float(r['peak_x']),x1=float(r['peak_x']), y0=0, y1=float(r['Linear_Depth']), line={'color': '#27ae60', 'width': 2.0, 'dash': 'dot'})
    fig5.add_annotation(x=float(r['peak_x']), y=float(r['Linear_Depth'])*0.52, text=f"  Depth = {r['Linear_Depth']:.4f}", showarrow=False, xanchor='left', font={'color': '#27ae60', 'size': 11})
    fig5.add_shape(type='line', x0=lx,x1=rx, y0=half,y1=half, line={'color': '#8e44ad', 'width': 2.0})
    fig5.add_annotation(x=(lx+rx)/2, y=half*1.15, text=f"FWHM = {r['FWHM_THz']:.4f} THz", showarrow=False, font={'color': '#8e44ad', 'size': 11})

    fig5.update_xaxes(title_text='Frequency (THz)')
    fig5.update_yaxes(title_text='ΔAmplitude (a.u., baseline corrected)', rangemode='tozero')
    fig5.update_layout(legend={'x': 0.62, 'y': 0.98})
    st.plotly_chart(fig5, use_container_width=True)

    pc = st.columns(6)
    for col, lbl, val in zip(pc,
        ['f_r (THz)','κ (THz)','γ (THz)','φ (rad)','h (dB)','R²'],
        [r['Peak_Freq_THz'],r['Fano_Kappa'],r['Fano_Gamma'],r['Fano_Phi'],r['Depth_dB'],r['R_squared']]):
        col.metric(lbl, f"{val:.4f}")
    zh("f_r: 共振频率 · κ: 耦合强度 · γ: 本征线宽 · φ: Fano相位 · h: 峰深度(dB) · R²: 拟合优度")

    st.divider()
    sec("Publication-Quality Figure (matplotlib)", "论文级静态图 · Nature/Science排版标准")

    col_fig, col_opt = st.columns([3,1])
    with col_opt:
        fig_w_in = st.number_input("Width (in)  图宽(英寸)", 2.5, 7.5, 3.5, 0.5)
        fig_h_in = st.number_input("Height (in)  图高(英寸)", 2.0, 6.0, 3.0, 0.5)
        show_fill= st.checkbox("Show area fill  显示面积", True)
        show_ann = st.checkbox("Show annotations  显示标注", True)

    with col_fig:
        apply_nature_style()
        fig_pub, ax = plt.subplots(figsize=(fig_w_in, fig_h_in))

        if show_fill:
            ax.fill_between(fx, 0, sig, color='#2c6ea5', alpha=0.12, zorder=1)
        ax.plot(fx, sig, color='#1a5f8a', lw=1.4, label='Signal', zorder=3)
        ax.plot(fx, fit_s, color='#c0392b', lw=1.4, ls='--', label='Fano fit', zorder=4)

        if show_ann:
            ax.vlines(r['peak_x'], 0, r['Linear_Depth'], colors='#27ae60', lw=1.2, ls=':', zorder=2)
            ax.hlines(half, lx, rx, colors='#8e44ad', lw=1.2, zorder=2)
            ax.annotate(f"FWHM = {r['FWHM_THz']:.4f} THz", xy=((lx+rx)/2, half), xytext=((lx+rx)/2, half*1.3),
                        fontsize=6.5, color='#8e44ad', ha='center', arrowprops=dict(arrowstyle='-', color='#8e44ad', lw=0.8))

        ax.set_xlabel('Frequency (THz)')
        ax.set_ylabel('ΔAmplitude (arb. u.)')
        ax.set_title(f'T = {r["Temperature_K"]:.0f} K', pad=6, fontsize=8)
        ax.set_ylim(bottom=0)
        ax.legend(frameon=True, loc='upper right')
        format_ax(ax)
        panel_label(ax, 'a')
        plt.tight_layout(pad=0.4)

        buf_pub = io.BytesIO()
        fig_pub.savefig(buf_pub, format='png', dpi=200, bbox_inches='tight')
        plt.close(fig_pub)
        buf_pub.seek(0)
        st.image(buf_pub, caption=(f"T = {r['Temperature_K']:.0f} K  ·  f_r = {r['Peak_Freq_THz']:.4f} THz  ·  R² = {r['R_squared']:.4f}"))

    st.download_button(
        f"⬇️  Download this figure (.{export_fmt})  下载此图",
        data=_single_fig_export(r, fig_w_in, fig_h_in, export_dpi, export_fmt),
        file_name=f"fano_{r['Temperature_K']:.0f}K.{export_fmt}",
        mime=f"image/{export_fmt}" if export_fmt!='pdf' else "application/pdf",
        use_container_width=True)
