import streamlit as st
from modules.data_loader import DataLoader

def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-section">📁 Data Input · 数据输入</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload THz data files (.txt)", type=["txt"], accept_multiple_files=True,
            help="Filename or header must contain temperature, e.g. '300K'\n文件名或表头需含温度，如 300K"
        )

        st.markdown('<div class="sidebar-section">⚙️ Processing · 处理参数</div>', unsafe_allow_html=True)
        amp_col_choice = st.radio(
            "Amplitude column / 振幅列", ["AMP FD (col 5)", "AMP dB (col 6)"], index=0,
            help="Choose which amplitude column to use for analysis.\n选择用于分析的振幅列：FD（线性）或 dB（对数）"
        )
        use_db = "dB" in amp_col_choice
        smooth_w = st.slider("Smoothing window 平滑窗口", 1, 15, 5, 2)
        rm_bad   = st.checkbox("Remove outliers 去除坏点", True)

        st.markdown('<div class="sidebar-section">📈 BCS Fitting · BCS拟合</div>', unsafe_allow_html=True)
        tc_mode = st.radio("T_c mode  临界温度模式", ["Auto-optimize 自动", "Fixed 手动固定"])
        tc_fixed = None
        if "Fixed" in tc_mode:
            _tc_c1, _tc_c2 = st.columns([2, 1])
            with _tc_c1:
                tc_fixed = st.slider("T_c (K)", 280.0, 380.0, st.session_state.get('_tc_val', 328.0), 0.5, key='_tc_slider')
            with _tc_c2:
                tc_fixed = st.number_input("T_c", 280.0, 380.0, tc_fixed, 0.5, key='_tc_num', label_visibility='collapsed')

        st.markdown('<div class="sidebar-section">📎 Reference / Substrate · 参考基底</div>', unsafe_allow_html=True)
        ref_uploaded = st.file_uploader(
            "Upload reference file (.txt)  上传参考(基底)文件", type=["txt"], accept_multiple_files=False,
            help="Reference/substrate measurement for dielectric calculation.\n介电计算所需的参考/基底测量数据。此文件不会参与Fano/BCS分析。",
            key="ref_uploader"
        )

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
            st.caption(f"📌 Ref: **{st.session_state.ref_name}** · T={st.session_state.ref_data['temperature']:.0f} K")

        st.markdown('<div class="sidebar-section">⚡ Dielectric · 介电函数</div>', unsafe_allow_html=True)
        diel_on = st.checkbox("Enable dielectric calculation 启用介电计算")
        thickness = 0.5
        if diel_on:
            thickness = st.number_input("Sample thickness (mm) 样品厚度", 0.01, 20.0, 0.5, 0.01)
            if not st.session_state.ref_data:
                st.warning("⚠️ Upload a reference file above for dielectric.\n请在上方上传参考文件以启用介电计算。")

        st.markdown('<div class="sidebar-section">🖼️ Figure Export · 图片导出</div>', unsafe_allow_html=True)
        export_dpi = st.selectbox("Export DPI", [150, 300, 600], index=1)
        export_fmt = st.selectbox("Format 格式", ["pdf", "png", "svg"], index=0)

        st.divider()
        if st.button("↺  Reset all · 重置", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    return uploaded, use_db, smooth_w, rm_bad, tc_fixed, diel_on, thickness, export_dpi, export_fmt
