import streamlit as st
import numpy as np
import plotly.graph_objects as go
from ui_components.utils import sec, zh, plotly_fig, get_colors, downsample_data
from modules.formulas import WATERFALL_FORMULA, WATERFALL_EXPLANATION

def render_tab_waterfall():
    if not st.session_state.results:
        st.info("Complete Fano fitting in Tab ① first.  请先在 ① 完成拟合。")
        st.stop()

    sec("Temperature-Dependent Spectra (Waterfall)", "温度演化瀑布图 · 偏移量 = 峰高 × offset系数")

    with st.expander("📐 Waterfall Offset — Formula / 偏移公式", expanded=False):
        st.latex(WATERFALL_FORMULA.strip().replace('$$',''))
        st.markdown(WATERFALL_EXPLANATION)
        st.markdown("---")
        st.markdown(
            "**Parameters / 参数**\n\n"
            "- **i**: curve index (sorted by temperature) / 曲线索引（按温度排序）\n"
            "- **median(peak heights)**: auto-calculated from fitting results / 自动从拟合结果计算\n"
            "- **m**: user-adjustable multiplier (slider below) / 用户可调乘子（下方滑块）"
        )

    ctl1, ctl2, ctl3 = st.columns(3)
    with ctl1:
        st.caption("Vertical offset 纵向偏移系数")
        _wo1, _wo2 = st.columns([2, 1])
        with _wo1:
            offset_mult = st.slider("Offset", 0.5, 5.0, 1.8, 0.1, key='wf_off_s', label_visibility='collapsed')
        with _wo2:
            offset_mult = st.number_input("Offset", 0.5, 5.0, offset_mult, 0.1, key='wf_off_n', label_visibility='collapsed')
        x_lo = st.number_input("x min (THz)", value=0.60, step=0.05)
        x_hi = st.number_input("x max (THz)", value=1.60, step=0.05)
    with ctl2:
        show_fit_wf = st.checkbox("Overlay Fano fit  叠加拟合曲线", False)
        st.caption("Label every N curves 每N条标温度")
        _nl1, _nl2 = st.columns([2, 1])
        with _nl1:
            n_label = st.slider("N", 1, 5, 2, key='nl_s', label_visibility='collapsed')
        with _nl2:
            n_label = st.number_input("N", 1, 5, n_label, 1, key='nl_n', label_visibility='collapsed')
    with ctl3:
        st.caption("Plot height (px) 图高")
        _ph1, _ph2 = st.columns([2, 1])
        with _ph1:
            wf_height = st.slider("H", 400, 1000, 650, 50, key='wfh_s', label_visibility='collapsed')
        with _ph2:
            wf_height = st.number_input("H", 400, 1000, wf_height, 50, key='wfh_n', label_visibility='collapsed')

    ok_items = sorted([(k,v) for k,v in st.session_state.results.items() if v], key=lambda x: x[1]['Temperature_K'])
    n_curves = len(ok_items)
    colors_wf = get_colors(n_curves)

    peak_hs = [v['Linear_Depth'] for _,v in ok_items]
    med_h = float(np.median(peak_hs)) if peak_hs else 1.0
    offset_step = med_h * offset_mult

    fig_wf = plotly_fig(int(wf_height), 'Temperature Evolution of Phonon Mode')
    for i, (fname, r) in enumerate(ok_items):
        freq_r = r['freq_roi']
        sig = r['signal']
        mask = (freq_r >= x_lo) & (freq_r <= x_hi)
        fx, sy = freq_r[mask], sig[mask]
        
        # Implement downsampling here to massively boost Waterfall performance
        fx, sy = downsample_data(fx, sy)
        
        if len(fx) == 0: continue
        offset = i * offset_step
        col = colors_wf[i]
        temp = r['Temperature_K']

        fig_wf.add_trace(go.Scatter(
            x=fx, y=sy+offset, mode='lines', line={'color': col, 'width': 1.5},
            name=f'{temp:.0f} K', hovertemplate=(f'<b>{temp:.0f} K</b><br>f = %{{x:.3f}} THz<br>I = %{{y:.4f}}<extra></extra>')))

        if show_fit_wf:
            fit_s = r['fitted_signal'][mask]
            # downsample fit too
            _, fit_s_ds = downsample_data(freq_r[mask], fit_s)
            
            fig_wf.add_trace(go.Scatter(
                x=fx, y=fit_s_ds+offset, mode='lines', line={'color': col, 'width': 1.0, 'dash': 'dash'},
                showlegend=False, hoverinfo='skip'))

        if i % int(n_label) == 0:
            fig_wf.add_annotation(
                x=x_hi+0.01, y=float(sy[-1])+offset if len(sy) else offset,
                xanchor='left', showarrow=False, text=f'<b>{temp:.0f} K</b>', font={'size': 9.5, 'color': col})

    fig_wf.update_xaxes(title_text='Frequency (THz)', range=[x_lo, x_hi+0.14])
    fig_wf.update_yaxes(title_text='Intensity (arb. u., offset)', showticklabels=False)
    fig_wf.update_layout(showlegend=False)
    st.plotly_chart(fig_wf, use_container_width=True)
    zh("颜色：蓝色→低温，红色→高温。偏移量自动以中位峰高为基准，避免曲线重叠。大图已进行降采样抗爆显优化。")
