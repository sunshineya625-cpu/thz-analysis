import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ui_components.utils import sec, zh
from ui_components.tab_peak import _single_fig_export
from modules.science_plot import apply_nature_style, SINGLE_COL, DOUBLE_COL, format_ax, panel_label, temp_cmap
from modules.formulas import generate_formula_doc
from modules.bcs_analyzer import BCSAnalyzer
import numpy as np

def _make_excel(df, diel_rs):
    buf = io.BytesIO()
    drop = ['freq_roi','signal','fitted_signal','half_height','left_x','right_x','peak_x']
    df_out = (df.drop(columns=drop, errors='ignore').sort_values('Temperature_K'))
    with pd.ExcelWriter(buf, engine='openpyxl') as xw:
        df_out.to_excel(xw, sheet_name='Fano_Parameters', index=False)
        if diel_rs:
            rows = []
            for res in diel_rs:
                for j in range(len(res['freq'])):
                    rows.append({'T (K)': res['temp'], 'Freq (THz)': res['freq'][j],
                                 'n': res['n'][j], 'k': res['k'][j],
                                 'eps1': res['e1'][j], 'eps2': res['e2'][j]})
            pd.DataFrame(rows).to_excel(xw, sheet_name='Dielectric_Functions', index=False)
    buf.seek(0)
    return buf.getvalue()

def _make_pdf_report(df, results, tc_fixed_val, dpi):
    apply_nature_style()
    bcs = BCSAnalyzer(tc_fixed=tc_fixed_val)
    df  = df.sort_values('Temperature_K')
    T   = df['Temperature_K'].values.astype(float)
    T_s = np.linspace(T.min()*0.82, max(T.max()+15,360), 500)
    buf = io.BytesIO()

    with PdfPages(buf) as pdf:
        # Page 1: BCS fits
        fig, axes = plt.subplots(1, 2, figsize=DOUBLE_COL)
        for ax, col, lbl, color in [
            (axes[0],'Linear_Depth','Peak Depth (arb. u.)','#1a5f8a'),
            (axes[1],'Area',        'Integrated Area (arb. u.·THz)','#27ae60'),
        ]:
            y = df[col].values.astype(float)
            ax.scatter(T, y, s=22, color=color, edgecolors='#111', linewidths=0.6, zorder=5)
            p = bcs.fit(T, y)
            if p:
                ax.plot(T_s, bcs.bcs(T_s,*p), color='#c0392b', lw=1.4, label=f'BCS  T_c={p[1]:.1f} K  β={p[2]:.2f}')
                ax.axvline(p[1], color='#888', ls='--', lw=0.8)
            ax.set_xlabel('Temperature (K)')
            ax.set_ylabel(lbl)
            ax.set_ylim(bottom=0)
            ax.legend(fontsize=6.5)
            format_ax(ax)
        panel_label(axes[0],'a'); panel_label(axes[1],'b')
        plt.suptitle('BCS Order Parameter Fitting', fontsize=9, fontweight='bold', y=1.01)
        plt.tight_layout(pad=0.5)
        pdf.savefig(fig, dpi=dpi, bbox_inches='tight'); plt.close()

        # Page 2: freq + FWHM
        fig, axes = plt.subplots(1, 2, figsize=DOUBLE_COL)
        for ax, col, ylab, col2 in [
            (axes[0],'Peak_Freq_THz','Phonon Frequency (THz)','#b5860d'),
            (axes[1],'FWHM_THz',    'FWHM (THz)','#8e44ad'),
        ]:
            ax.plot(T, df[col].values, 'o--', color=col2, ms=3.5, lw=0.9, mec='#111', mew=0.5)
            ax.set_xlabel('Temperature (K)')
            ax.set_ylabel(ylab)
            ax.set_ylim(bottom=0)
            format_ax(ax)
        panel_label(axes[0],'c'); panel_label(axes[1],'d')
        plt.suptitle('Phonon Frequency and Linewidth', fontsize=9, fontweight='bold', y=1.01)
        plt.tight_layout(pad=0.5)
        pdf.savefig(fig, dpi=dpi, bbox_inches='tight'); plt.close()

        # Page 3+: waterfall
        ok_items = sorted([(k,v) for k,v in results.items() if v], key=lambda x: x[1]['Temperature_K'])
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
                ax.text(1.61, float(sy[m][-1])+off if m.any() else off, f'{r["Temperature_K"]:.0f} K', fontsize=5.5, color=c, va='center')
        ax.set_xlabel('Frequency (THz)')
        ax.set_ylabel('Intensity (arb. u., offset)')
        ax.set_xlim(0.60, 1.75)
        ax.set_yticks([])
        ax.set_title('Temperature Evolution of Phonon Mode', fontsize=8, pad=5)
        format_ax(ax, minor=False)
        panel_label(ax,'e')
        plt.tight_layout(pad=0.4)
        pdf.savefig(fig, dpi=dpi, bbox_inches='tight'); plt.close()

        # Page 4+: individual fits
        step_sel = max(1, n_c//12)
        sel_fits = ok_items[::step_sel][:12]
        n_sub    = len(sel_fits)
        ncols    = 3; nrows = (n_sub+ncols-1)//ncols
        fig, axes = plt.subplots(nrows, ncols, figsize=(7.0, nrows*2.4))
        axes = axes.flatten()
        for i,(_,r) in enumerate(sel_fits):
            ax = axes[i]
            ax.fill_between(r['freq_roi'],0,r['signal'], color='#2c6ea5',alpha=0.12)
            ax.plot(r['freq_roi'],r['signal'], color='#1a5f8a',lw=1.0,label='Signal')
            ax.plot(r['freq_roi'],r['fitted_signal'], color='#c0392b',lw=1.0,ls='--',label='Fano fit')
            ax.vlines(r['peak_x'],0,r['Linear_Depth'], colors='#27ae60',lw=0.9,ls=':')
            ax.hlines(r['half_height'],r['left_x'],r['right_x'], colors='#8e44ad',lw=0.9)
            ax.set_title(f"{r['Temperature_K']:.0f} K  R²={r['R_squared']:.3f}", fontsize=7, pad=3)
            ax.set_ylim(bottom=0)
            ax.set_xlabel('Frequency (THz)', fontsize=6)
            ax.set_ylabel('ΔAmpl. (arb. u.)', fontsize=6)
            format_ax(ax)
        for j in range(i+1, len(axes)):
            axes[j].axis('off')
        plt.suptitle('Representative Fano Fits', fontsize=9, fontweight='bold', y=1.01)
        plt.tight_layout(pad=0.4)
        pdf.savefig(fig, dpi=dpi, bbox_inches='tight'); plt.close()

        d = pdf.infodict()
        d['Title'] = 'THz Spectroscopy Analysis Report'
        d['Author'] = 'THz Analysis Studio v3.0'
        d['Subject'] = 'Fano resonance & BCS order parameter'

    buf.seek(0)
    return buf.read()

def _export_all_figs(results, dpi):
    apply_nature_style()
    buf = io.BytesIO()
    ok_items = sorted([(k,v) for k,v in results.items() if v], key=lambda x: x[1]['Temperature_K'])
    with PdfPages(buf) as pdf:
        for _, r in ok_items:
            fig, ax = plt.subplots(figsize=SINGLE_COL)
            ax.fill_between(r['freq_roi'],0,r['signal'], color='#2c6ea5',alpha=0.12)
            ax.plot(r['freq_roi'],r['signal'], color='#1a5f8a',lw=1.4,label='Signal')
            ax.plot(r['freq_roi'],r['fitted_signal'], color='#c0392b',lw=1.4,ls='--',label='Fano fit')
            ax.vlines(r['peak_x'],0,r['Linear_Depth'], colors='#27ae60',lw=1.1,ls=':')
            ax.hlines(r['half_height'],r['left_x'],r['right_x'], colors='#8e44ad',lw=1.1)
            ax.set_xlabel('Frequency (THz)')
            ax.set_ylabel('ΔAmplitude (arb. u.)')
            ax.set_title(f"T = {r['Temperature_K']:.0f} K  ·  $f_r$ = {r['Peak_Freq_THz']:.4f} THz  ·  R² = {r['R_squared']:.4f}", fontsize=7, pad=4)
            ax.set_ylim(bottom=0)
            ax.legend(fontsize=6.5)
            format_ax(ax)
            plt.tight_layout(pad=0.4)
            pdf.savefig(fig, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
    buf.seek(0)
    return buf.read()

def render_tab_export(tc_fixed, export_dpi, export_fmt, smooth_w, rm_bad, thickness, diel_on):
    sec("Export Results  导出结果", "Excel数据 · PDF报告 · 高分辨率图集 · 公式文档")

    col_e1, col_e2, col_e3, col_e4 = st.columns(4)

    with col_e1:
        st.markdown("### 📊 Excel data")
        zh("包含Fano参数、BCS参数、介电函数三个Sheet")
        if st.session_state.df is not None:
            buf_xl = _make_excel(st.session_state.df, getattr(st.session_state, 'diel', []))
            st.download_button("⬇️  Download Excel", data=buf_xl, use_container_width=True,
                               file_name="THz_Analysis_Results.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Complete fitting first.  请先完成拟合。")

    with col_e2:
        st.markdown("### 📄 PDF report")
        zh("包含BCS拟合图、瀑布图、单峰拟合图，按需懒加载")
        disabled_pdf = st.session_state.df is None
        # PDF is only generated IF the user clicks the explicit generate button
        if st.button("Generate PDF report  生成报告", use_container_width=True, disabled=disabled_pdf):
            with st.spinner("Generating publication-quality PDF …  生成中 …"):
                buf_pdf = _make_pdf_report(st.session_state.df, st.session_state.results, tc_fixed, export_dpi)
            st.download_button("⬇️  Ready to Download PDF", data=buf_pdf, use_container_width=True,
                               file_name="THz_Analysis_Report.pdf", mime="application/pdf")

    with col_e3:
        st.markdown("### 🖼️ Figure pack")
        zh("所有温度拟合图集PDF，异步按需生成以免界面阻塞")
        if st.button("Generate all fit figures  生成图集", use_container_width=True, disabled=(not st.session_state.results)):
            with st.spinner("Rendering all figures …"):
                buf_all = _export_all_figs(st.session_state.results, export_dpi)
            st.download_button("⬇️  Ready to Download Pack", data=buf_all, use_container_width=True,
                               file_name="THz_all_fits.pdf", mime="application/pdf")

    with col_e4:
        st.markdown("### 📐 Formula doc")
        zh("所有公式、参数说明、当前参数值的完整文档")
        current_params = {
            "Smoothing window": smooth_w, "Remove outliers": rm_bad, "Export DPI": export_dpi,
            "Export format": export_fmt, "Sample thickness (mm)": thickness, "Dielectric enabled": diel_on,
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
        st.download_button("⬇️  Download formula doc", data=formula_md.encode('utf-8'),
                           use_container_width=True, file_name="THz_Formula_Documentation.md", mime="text/markdown")
