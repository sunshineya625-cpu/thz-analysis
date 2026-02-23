import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ui_components.utils import sec, zh, plotly_fig, get_colors

def render_tab_averaging(amp_label):
    sec("Temperature Averaging", "按温度分组平均 · 同温度多次扫描取均值后用于后续分析")

    _raw = st.session_state.files
    _avg = st.session_state.averaged_files or _raw
    _grp = getattr(st.session_state, 'avg_group_info', None) or {}

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
    zh(f"共 {len(_raw)} 个原始文件 → 按温度分组平均后得到 {len(_avg)} 组数据")

    # ── Overlay: individual scans + average ──
    st.divider()
    sec("Averaging Detail  平均详情", "选择一个温度查看各扫描与平均结果")

    multi_groups = [d for d in _avg if d.get('n_averaged', 1) > 1]
    if multi_groups:
        sel_temp = st.selectbox(
            "Select temperature group / 选择温度组",
            range(len(multi_groups)),
            format_func=lambda i: (
                f"{multi_groups[i]['temperature']:.1f} K  "
                f"({multi_groups[i].get('n_averaged',1)} scans)")
        )
        grp = multi_groups[sel_temp]
        src_names = grp.get('source_files', [])

        fig_avg = plotly_fig(380, f"Averaging: {grp['temperature']:.1f} K  ({len(src_names)} scans)")

        # Plot individual scans (thin, grey)
        colors_ind = get_colors(len(src_names))
        for j, sname in enumerate(src_names):
            raw_d = next((f for f in _raw if f['filename'] == sname), None)
            if raw_d is not None:
                fig_avg.add_trace(go.Scatter(
                    x=raw_d['freq'], y=raw_d['amp'],
                    mode='lines', name=sname,
                    line=dict(color=colors_ind[j], width=0.8), opacity=0.5
                ))

        # Plot averaged curve (bold red)
        fig_avg.add_trace(go.Scatter(
            x=grp['freq'], y=grp['amp'],
            mode='lines', name=f'Average ({len(src_names)} scans)',
            line=dict(color='#c0392b', width=2.5)
        ))

        fig_avg.update_xaxes(title_text='Frequency (THz)')
        fig_avg.update_yaxes(title_text=amp_label)
        st.plotly_chart(fig_avg, use_container_width=True)
        zh("细线：各次扫描的原始数据 · 粗红线：平均后的数据 · 平均前插值到公共频率格点")
    else:
        st.info("No temperatures have multiple scans to average.  没有温度有多次扫描需要平均。每个温度只有一个文件。")
