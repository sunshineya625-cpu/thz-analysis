import streamlit as st
import numpy as np
import plotly.graph_objects as go
from ui_components.utils import sec, zh, plotly_fig
from modules.formulas import BCS_FORMULA, BCS_PARAMS, BCS_EXPLANATION
from modules.bcs_analyzer import BCSAnalyzer

def render_tab_bcs(tc_fixed):
    if st.session_state.df is None:
        st.info("Complete Fano fitting in Tab ① first.  请先在 ① 完成拟合。")
        st.stop()

    sec("BCS Order Parameter Fitting", "BCS序参量温度依赖拟合 · Δ(T) = A·tanh(β√(Tc/T−1))")
    zh("公式来源：BCS超导理论类比，广泛用于CDW/激子绝缘体相变表征")

    with st.expander("📐 BCS Order Parameter — Formulas & Theory / 公式与理论", expanded=False):
        st.latex(BCS_FORMULA.strip().replace('$$',''))
        st.markdown(BCS_EXPLANATION)
        st.markdown("---")
        st.markdown("### Parameters / 参数说明")
        for k, v in BCS_PARAMS.items():
            st.markdown(f"**{k}** (`{v['unit']}`): {v['name']}")
            st.caption(v['desc'])

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

    df = st.session_state.df.sort_values('Temperature_K')
    bcs = BCSAnalyzer(tc_fixed=tc_fixed)
    T = df['Temperature_K'].values.astype(float)
    T_s = np.linspace(T.min()*0.82, max(T.max()+15, 360), 600)
    colors_bcs = ['#1a5f8a','#27ae60']

    def bcs_panel(y, ylab, color, key):
        params = bcs.fit(T, y)
        fig = plotly_fig(380, f'{ylab} vs Temperature')
        fig.add_trace(go.Scatter(x=T, y=y, mode='markers', name='Experimental data',
            marker={'size': 8, 'color': color, 'line': {'width': 1.2, 'color': '#111'}, 'symbol': 'circle'}))
        if params:
            A, Tc, beta = params
            ys = bcs.bcs(T_s, A, Tc, beta)
            fig.add_trace(go.Scatter(x=T_s, y=ys, mode='lines', name=f'BCS fit  T_c={Tc:.1f} K  β={beta:.2f}',
                                     line={'color': '#c0392b', 'width': 2.2}))
            fig.add_vline(x=Tc, line_dash='dash', line_color='#888', line_width=1.0,
                          annotation_text=f'T_c = {Tc:.1f} K', annotation_position='top right',
                          annotation_font_size=11)
            st.session_state.fitted_tc = f"{Tc:.1f} K"
        fig.update_xaxes(title_text='Temperature (K)')
        fig.update_yaxes(title_text=ylab, rangemode='tozero')
        fig.update_layout(legend={'x': 0.02, 'y': 0.98})
        return fig, params

    col_a, col_b = st.columns(2)
    with col_a:
        fa, pa = bcs_panel(df['Linear_Depth'].values.astype(float), 'Peak Depth (a.u.)', colors_bcs[0], 'd')
        st.plotly_chart(fa, use_container_width=True)
        if pa:
            st.markdown(
                f'<span class="chip">T_c = {pa[1]:.2f} K</span><span class="chip">β = {pa[2]:.3f}</span><span class="chip">A = {pa[0]:.4f}</span>',
                unsafe_allow_html=True)
            zh("深度拟合：峰谷与基线之差，直接体现序参量大小")

    with col_b:
        fb, pb = bcs_panel(df['Area'].values.astype(float), 'Integrated Area (a.u.·THz)', colors_bcs[1], 'a')
        st.plotly_chart(fb, use_container_width=True)
        if pb:
            st.markdown(
                f'<span class="chip">T_c = {pb[1]:.2f} K</span><span class="chip">β = {pb[2]:.3f}</span>',
                unsafe_allow_html=True)
            zh("面积拟合：积分振子强度，对噪声更鲁棒")

    st.divider()
    sec("Phonon Frequency & Linewidth", "声子频率软化与线宽展宽")
    col_c, col_d = st.columns(2)
    with col_c:
        fc = plotly_fig(320, 'Phonon Frequency vs Temperature')
        fc.add_trace(go.Scatter(x=T, y=df['Peak_Freq_THz'].values.astype(float), mode='markers+lines',
            marker={'size': 7, 'color': '#b5860d', 'line': {'width': 1.2, 'color': '#111'}}, line={'color': '#b5860d', 'width': 1.0, 'dash': 'dot'}, name='f_r'))
        fc.update_xaxes(title_text='Temperature (K)')
        fc.update_yaxes(title_text='Frequency (THz)')
        st.plotly_chart(fc, use_container_width=True)
        zh("声子软化/硬化反映晶格动力学随相变的演化")
    with col_d:
        fd = plotly_fig(320, 'Phonon Linewidth (FWHM) vs Temperature')
        fd.add_trace(go.Scatter(x=T, y=df['FWHM_THz'].values.astype(float), mode='markers+lines',
            marker={'size': 7, 'color': '#8e44ad', 'line': {'width': 1.2, 'color': '#111'}}, line={'color': '#8e44ad', 'width': 1.0, 'dash': 'dot'}, name='FWHM'))
        fd.update_xaxes(title_text='Temperature (K)')
        fd.update_yaxes(title_text='FWHM (THz)', rangemode='tozero')
        st.plotly_chart(fd, use_container_width=True)
        zh("线宽展宽反映声子寿命缩短，与散射率增大相关")
