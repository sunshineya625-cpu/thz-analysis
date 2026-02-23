import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ui_components.utils import sec, zh, plotly_fig, get_colors, downsample_data
from modules.formulas import (FANO_FORMULA, FANO_PARAMS, FANO_EXPLANATION,
                              DEPTH_DB_FORMULA, DEPTH_DB_EXPLANATION,
                              LINEAR_DEPTH_FORMULA, LINEAR_DEPTH_EXPLANATION,
                              FWHM_FORMULA, FWHM_EXPLANATION,
                              AREA_FORMULA, AREA_EXPLANATION,
                              R_SQUARED_FORMULA, R_SQUARED_EXPLANATION)
from modules.fano_fitter import FanoFitter

def render_tab_fano(smooth_w, rm_bad, amp_label):
    files = st.session_state.get('_active_files', st.session_state.averaged_files or st.session_state.files)
    sec("File Overview", "文件列表与频率范围")
    tbl = pd.DataFrame([{
        "Filename": d['filename'], "T (K)": d['temperature'],
        "f range (THz)": f"{float(d['freq'].min()):.3f} – {float(d['freq'].max()):.3f}" if len(d['freq']) else "—",
        "Points": len(d['freq']),
    } for d in files])
    st.dataframe(tbl, use_container_width=True, height=170, hide_index=True)

    st.divider()
    sec("ROI Selection", "感兴趣区域选择（将统一应用到所有文件）")

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

    with st.expander("⚙️ Advanced: Fano Fitting Bounds / 高级：拟合参数边界", expanded=False):
        st.caption("Adjust the parameter bounds for Fano fitting. 调整 Fano 拟合的参数边界约束。")
        adv_c1, adv_c2 = st.columns(2)
        with adv_c1:
            kappa_max = st.number_input("κ max", 0.1, 10.0, 2.0, 0.1, key="kappa_max")
            gamma_max = st.number_input("γ max", 0.1, 10.0, 2.0, 0.1, key="gamma_max")
        with adv_c2:
            phi_range = st.slider("φ range (rad)", -3.14, 3.14, (-3.14, 3.14), 0.01, key="phi_range")
            max_iter  = st.number_input("Max iterations / 最大迭代", 1000, 50000, 10000, 1000, key="max_iter")
        st.session_state['adv_fano'] = {
            'kappa_max': kappa_max, 'gamma_max': gamma_max,
            'phi_range': phi_range, 'max_iter': int(max_iter),
        }

    col_ctrl, col_plot = st.columns([1, 3])
    with col_ctrl:
        view_mode = st.radio("View mode / 查看模式", ["Single file 单文件", "All overlay 全部叠加"], key="roi_view_mode")
        idx = 0
        if "Single" in view_mode:
            idx = int(st.selectbox("Preview file  预览文件", range(len(files)), format_func=lambda i: f"{files[i]['filename']} ({files[i]['temperature']:.0f} K)"))
        
        sel = files[idx] if "Single" in view_mode else files[0]
        fa = sel['freq'].astype(float)
        flo, fhi = float(fa.min()), float(fa.max())

        st.caption("Left boundary (THz) 左边界")
        _rl1, _rl2 = st.columns([2, 1])
        with _rl1:
            roi_l = st.slider("Left THz", flo, fhi, float(np.clip(0.80, flo, fhi)), 0.005, key='roi_l_slider', label_visibility='collapsed')
        with _rl2:
            roi_l = st.number_input("Left", flo, fhi, roi_l, 0.005, format="%.3f", key='roi_l_num', label_visibility='collapsed')

        st.caption("Right boundary (THz) 右边界")
        _rr1, _rr2 = st.columns([2, 1])
        with _rr1:
            roi_r = st.slider("Right THz", flo, fhi, float(np.clip(1.30, flo, fhi)), 0.005, key='roi_r_slider', label_visibility='collapsed')
        with _rr2:
            roi_r = st.number_input("Right", flo, fhi, roi_r, 0.005, format="%.3f", key='roi_r_num', label_visibility='collapsed')

        if roi_l >= roi_r:
            st.error("Left boundary must be < right boundary")
        st.session_state.roi = (roi_l, roi_r)

        do_fit = st.button("▶  Run batch Fano fitting\n批量拟合", type="primary", use_container_width=True)

    with col_plot:
        if "Single" in view_mode:
            aa = sel['amp'].astype(float)
            fig = plotly_fig(380, f"{sel['filename']}  ·  {sel['temperature']:.0f} K")
            dx, dy = downsample_data(fa, aa)
            fig.add_trace(go.Scatter(x=dx, y=dy, mode='lines', name='Spectrum', line={'color': '#334466', 'width': 1.2}))
            
            mask = (fa >= roi_l) & (fa <= roi_r)
            fig.add_trace(go.Scatter(x=fa[mask], y=aa[mask], mode='lines', name='ROI', line={'color': '#c0392b', 'width': 2.2}))
            fig.add_vrect(x0=roi_l, x1=roi_r, fillcolor="#c0392b", opacity=0.07, line_width=0)
            fig.update_xaxes(title_text="Frequency (THz)")
            fig.update_yaxes(title_text=amp_label)
            st.plotly_chart(fig, use_container_width=True)
        else:
            n_files = len(files)
            colors_all = get_colors(n_files)
            fig = plotly_fig(480, f"All Spectra ({n_files} files)  ·  全部光谱叠加")
            for i, d in enumerate(files):
                fx = d['freq'].astype(float)
                fy = d['amp'].astype(float)
                dx, dy = downsample_data(fx, fy)
                show_leg = (i == 0 or i == n_files - 1 or n_files <= 8)
                fig.add_trace(go.Scatter(
                    x=dx, y=dy, mode='lines',
                    name=f"{d['temperature']:.0f} K",
                    line={'color': colors_all[i], 'width': 1.0},
                    showlegend=bool(show_leg),
                    legendgroup=str(i),
                    hovertemplate=(f"<b>{d['temperature']:.0f} K</b><br>f = %{{x:.3f}} THz<br>amp = %{{y:.4f}}<extra></extra>")
                ))
            fig.add_vrect(x0=roi_l, x1=roi_r, fillcolor="#c0392b", opacity=0.07, line_width=0, annotation_text="ROI", annotation_position="top left")
            fig.update_xaxes(title_text="Frequency (THz)")
            fig.update_yaxes(title_text=amp_label)
            fig.update_layout(legend={'title': "Temperature", 'orientation': 'v', 'x': 1.01})
            st.plotly_chart(fig, use_container_width=True)
            zh(f"颜色：蓝→低温，红→高温 · 共 {n_files} 条曲线 · 阴影区域为选定的 ROI 范围 · **可视化波形已压缩防显存卡顿**")

    if do_fit:
        fitter = FanoFitter(smooth_window=smooth_w, remove_outliers=rm_bad)
        roi = st.session_state.roi
        prog = st.progress(0)
        stat = st.empty()
        results = {}
        for i, d in enumerate(files):
            stat.text(f"Fitting {d['filename']}  ({i+1}/{len(files)}) …")
            try:
                r = fitter.fit(d['freq'].astype(float), d['amp'].astype(float), roi, d['temperature'], d['filename'])
                results[d['filename']] = r
            except Exception as e:
                st.warning(f"⚠️ {d['filename']}: {e}")
                results[d['filename']] = None
            prog.progress((i+1)/len(files))
        st.session_state.results = results
        ok = [r for r in results.values() if r]
        st.session_state.df = pd.DataFrame(ok) if ok else None
        st.session_state.step = 3
        prog.empty(); stat.empty()
        st.success(f"✅ Fitting complete · 拟合完成  —  {len(ok)}/{len(files)} successful")
        st.rerun()

    if st.session_state.df is not None:
        st.divider()
        sec("Fitting Results", "拟合结果汇总 · 绿色 R²>0.97 · 红色 R²<0.90")
        cols_show = ['Temperature_K','Peak_Freq_THz','Depth_dB','Linear_Depth','FWHM_THz','Area','R_squared']
        df_s = (st.session_state.df[cols_show]
                .sort_values('Temperature_K')
                .rename(columns={
                    'Temperature_K':'T (K)', 'Peak_Freq_THz':'f_r (THz)', 'Depth_dB':'h (dB)',
                    'Linear_Depth':'Depth (a.u.)', 'FWHM_THz':'FWHM (THz)', 'Area':'Area (a.u.·THz)', 'R_squared':'R²'
                }))

        def _r2_style(val):
            if val > 0.97: return 'background-color:#d4edda;color:#155724'
            if val < 0.90: return 'background-color:#f8d7da;color:#721c24'
            return 'background-color:#fff3cd;color:#856404'

        styled = (df_s.style.map(_r2_style, subset=['R²'])
                  .format({'T (K)':'{:.1f}','f_r (THz)':'{:.4f}','h (dB)':'{:.2f}','Depth (a.u.)':'{:.4f}',
                           'FWHM (THz)':'{:.4f}','Area (a.u.·THz)':'{:.5f}','R²':'{:.4f}'}))
        st.dataframe(styled, use_container_width=True, height=300, hide_index=True)

        df = st.session_state.df.sort_values('Temperature_K')
        T = df['Temperature_K'].values.astype(float)
        c1, c2, c3 = st.columns(3)
        for container, ycol, ylab, color in [
            (c1,'Peak_Freq_THz','f_r (THz)','#1a5f8a'),
            (c2,'Linear_Depth', 'Depth (a.u.)','#c0392b'),
            (c3,'FWHM_THz',     'FWHM (THz)','#27ae60'),
        ]:
            f2 = plotly_fig(230, ylab)
            f2.add_trace(go.Scatter(x=T, y=df[ycol].values, mode='markers+lines',
                marker={'size': 6, 'color': color, 'line': {'width': 1.0, 'color': '#111'}},
                line={'color': color, 'width': 1.0, 'dash': 'dot'}))
            f2.update_xaxes(title_text='Temperature (K)')
            f2.update_yaxes(title_text=ylab)
            container.plotly_chart(f2, use_container_width=True)
