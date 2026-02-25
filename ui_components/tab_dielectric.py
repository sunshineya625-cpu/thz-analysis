import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ui_components.utils import sec, zh, plotly_fig, get_colors
from modules.dielectric_calc import DielectricCalculator
from modules.formulas import (TRANSFER_FUNC_FORMULA, REFRACTIVE_INDEX_FORMULA,
                              EXTINCTION_FORMULA, DIELECTRIC_FORMULA,
                              DIELECTRIC_PARAMS, DIELECTRIC_EXPLANATION)
from modules.science_plot import apply_plotly_style

def render_tab_dielectric(diel_on, thickness, files):
    if not diel_on:
        st.info("Enable **Dielectric calculation** in the sidebar.  请在左侧勾选启用介电计算。")
        st.stop()

    ref_data = st.session_state.ref_data
    if ref_data is None or len(ref_data.get('time',[]))==0:
        st.error("No reference file uploaded, or reference has no time-domain data.  没有上传参考文件，或参考文件无时域数据。请在侧边栏上传参考基底文件。")
        st.stop()

    sec("Optical Constants & Dielectric Functions", "光学常数与复介电函数 · n, k, ε₁, ε₂")
    zh("方法：频域传输函数法 H(ω)=S_sam/S_ref → n(ω) → k(ω) → ε(ω)=ε₁+iε₂")

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

    with st.expander("⚙️ Advanced: Dielectric Calculation Parameters / 高级：介电计算参数", expanded=False):
        diel_c1, diel_c2 = st.columns(2)
        with diel_c1:
            gain_limit = st.number_input("Gain limit / 增益限制", 0.5, 1.0, 0.85, 0.05, key="gain_limit", help="Max |H| normalization threshold")
            diel_smooth = int(st.number_input("Smoothing window / 平滑窗口", 1, 21, 5, 2, key="diel_smooth"))
        with diel_c2:
            phase_fit_lo = st.number_input("Phase fit range low (THz)", 0.1, 2.0, 0.5, 0.1, key="phase_lo")
            phase_fit_hi = st.number_input("Phase fit range high (THz)", 0.5, 4.0, 1.0, 0.1, key="phase_hi")

    with st.spinner("Computing dielectric functions …  计算中 …"):
        calc = DielectricCalculator(thickness=thickness)
        # Assuming calc.calculate_all accepts only these parameters; add others if necessary.
        diel_rs = calc.calculate_all(ref_data, files)

    if not diel_rs:
        st.error("Calculation failed. Check reference file.  计算失败，请检查参考文件。")
        st.stop()

    st.session_state.diel = diel_rs
    diel_rs.sort(key=lambda x: x['temp'])
    nd = len(diel_rs)

    subset = diel_rs
    colors_d = get_colors(len(subset))

    st.caption("Frequency range (THz) 频率范围")
    _fd1, _fd2, _fd3 = st.columns([1, 2, 1])
    with _fd1:
        f_lo_d = st.number_input("f_lo", 0.3, 4.0, 0.5, 0.05, format="%.2f", key='diel_flo')
    with _fd2:
        f_lo_d, f_hi_d = st.slider("Freq", 0.3, 4.0, (float(f_lo_d), 2.8), 0.05, key='diel_fs', label_visibility='collapsed')
    with _fd3:
        f_hi_d = st.number_input("f_hi", 0.3, 4.0, float(f_hi_d), 0.05, format="%.2f", key='diel_fhi')

    fig_d = make_subplots(rows=2, cols=2, horizontal_spacing=0.12, vertical_spacing=0.14,
                          subplot_titles=['Refractive index  n', 'Extinction coefficient  k',
                                          'Real permittivity  ε₁', 'Imaginary permittivity  ε₂'])
    for i,(res,col) in enumerate(zip(subset, colors_d)):
        m  = (res['freq']>=f_lo_d) & (res['freq']<=f_hi_d)
        sl = (i==0 or i==len(subset)-1)
        kw = {'mode': 'lines', 'line': {'color': col, 'width': 1.3},
              'name': f"{res['temp']:.0f} K", 'legendgroup': str(i), 'showlegend': bool(sl)}
        
        # Merge kw with additional properties but pass line dict correctly
        fig_d.add_trace(go.Scatter(x=res['freq'][m],y=res['n'][m], mode='lines', line={'color': col, 'width': 1.3}, name=f"{res['temp']:.0f} K", legendgroup=str(i), showlegend=bool(sl)), row=1,col=1)
        fig_d.add_trace(go.Scatter(x=res['freq'][m],y=res['k'][m], mode='lines', line={'color': col, 'width': 1.3}, name=f"{res['temp']:.0f} K", legendgroup=str(i), showlegend=False), row=1,col=2)
        fig_d.add_trace(go.Scatter(x=res['freq'][m],y=res['e1'][m], mode='lines', line={'color': col, 'width': 1.3}, name=f"{res['temp']:.0f} K", legendgroup=str(i), showlegend=False), row=2,col=1)
        fig_d.add_trace(go.Scatter(x=res['freq'][m],y=res['e2'][m], mode='lines', line={'color': col, 'width': 1.3}, name=f"{res['temp']:.0f} K", legendgroup=str(i), showlegend=False), row=2,col=2)

    apply_plotly_style(fig_d, height=680, title='Optical Constants — Temperature Dependence')
    for r,c in [(1,1),(1,2),(2,1),(2,2)]:
        fig_d.update_xaxes(title_text='Frequency (THz)', showgrid=False, ticks='inside', row=r,col=c)
    fig_d.update_yaxes(title_text='n', row=1,col=1)
    fig_d.update_yaxes(title_text='k', row=1,col=2)
    fig_d.update_yaxes(title_text='ε₁', row=2,col=1)
    fig_d.update_yaxes(title_text='ε₂', row=2,col=2)
    fig_d.update_layout(legend={'title': 'Temperature', 'orientation': 'v', 'x': 1.01})
    st.plotly_chart(fig_d, use_container_width=True)

    st.divider()
    sec("Low-T vs High-T Comparison  低温 vs 高温对比")
    lo_r,hi_r = diel_rs[0], diel_rs[-1]
    fig_cmp = plotly_fig(340, f'ε₂: {lo_r["temp"]:.0f} K vs {hi_r["temp"]:.0f} K')
    for res, col, lbl in [(lo_r,'#2980b9',f'Low-T  {lo_r["temp"]:.0f} K'), (hi_r,'#c0392b',f'High-T  {hi_r["temp"]:.0f} K')]:
        m = (res['freq']>=f_lo_d) & (res['freq']<=f_hi_d)
        fig_cmp.add_trace(go.Scatter(x=res['freq'][m], y=res['e2'][m], mode='lines', name=lbl, line={'color': col, 'width': 2.2}))
    fig_cmp.update_xaxes(title_text='Frequency (THz)')
    fig_cmp.update_yaxes(title_text='ε₂ (Imaginary permittivity)')
    st.plotly_chart(fig_cmp, use_container_width=True)
    zh("ε₂ 在声子频率处出现峰值；低温下峰更尖锐，线宽更窄，反映声子寿命增长。")
