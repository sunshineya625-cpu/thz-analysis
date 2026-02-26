import os
import json
import datetime
import numpy as np
import pandas as pd

SESSION_DIR = "sessions"

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        return super().default(obj)

class SessionManager:
    @staticmethod
    def save_session(session_name, state_dict):
        os.makedirs(SESSION_DIR, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join([c if c.isalnum() else "_" for c in session_name])
        folder_name = f"{ts}_{safe_name}"
        run_dir = os.path.join(SESSION_DIR, folder_name)
        os.makedirs(run_dir, exist_ok=True)
        
        # Save JSON
        json_path = os.path.join(run_dir, "workspace.json")
        
        # Clean up data specifically for serialization to prevent giant files
        # We don't need to save raw 'files' if we save 'averaged_files', but let's save what we can
        clean_state = {}
        for k, v in state_dict.items():
            if k in ['files', 'averaged_files'] and v:
                # Store lightweight metadata instead of all raw sweeps
                clean_state[k] = [{'filename': d['filename'], 'temperature': d['temperature']} for d in v]
            else:
                clean_state[k] = v
                
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(clean_state, f, cls=NumpyEncoder, indent=2)
            
        # Generate Markdown Report
        md_path = os.path.join(run_dir, "report.md")
        SessionManager._generate_markdown_report(md_path, session_name, state_dict)
        
        return run_dir
        
    @staticmethod
    def _generate_markdown_report(filepath, session_name, state_dict):
        df = state_dict.get('df')
        roi = state_dict.get('roi', [0, 0])
        results = state_dict.get('results', {})
        tc_fixed = state_dict.get('tc_fixed_val')
        
        md = [
            f"# THz Analysis Report: {session_name}",
            f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 1. Parameters",
            f"- **Processing ROI:** {roi[0]:.3f} to {roi[1]:.3f} THz",
            f"- **BCS Fixed T_c:** {f'{tc_fixed} K' if tc_fixed else 'Floating'}",
            f"- **Excluded Scans:** {len(state_dict.get('excluded_scans', []))}",
            ""
        ]
        
        if df is not None and not df.empty:
            md.append("## 2. Key Findings (BCS Fitting)")
            try:
                # Do a quick text BCS fit if possible to get parameters
                # Since we don't want to import BCSAnalyzer here to avoid circular logic, we just dump raw
                t_min = df['Temperature_K'].min()
                t_max = df['Temperature_K'].max()
                md.append(f"- **Temperature Range Analyzed:** {t_min:.1f} K — {t_max:.1f} K")
                md.append("")
                md.append("### Fano Fit Results Overview")
                md.append("| Temp (K) | Res Freq (THz) | Linewidth (THz) | Area (a.u.) | R² |")
                md.append("|:---:|:---:|:---:|:---:|:---:|")
                for _, row in df.sort_values('Temperature_K').iterrows():
                    md.append(f"| {row['Temperature_K']:.1f} | {row['Peak_Freq_THz']:.4f} | {row['FWHM_THz']:.4f} | {row['Area']:.4f} | {row['R_squared']:.4f} |")
            except Exception as e:
                md.append(f"*(Could not generate table: {e})*")
                
        else:
            md.append("*No fitting data available in this session.*")
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(md))

    @staticmethod
    def list_sessions():
        if not os.path.exists(SESSION_DIR):
            return []
        dirs = [d for d in os.listdir(SESSION_DIR) if os.path.isdir(os.path.join(SESSION_DIR, d))]
        # Sort newest first
        dirs.sort(reverse=True)
        
        session_infos = []
        for d in dirs:
            info = {'dir': d, 'path': os.path.join(SESSION_DIR, d), 'date': d[:15]}
            json_path = os.path.join(SESSION_DIR, d, 'workspace.json')
            if os.path.exists(json_path):
                # We can load just the keys or basic info if needed
                pass
            session_infos.append(info)
        return session_infos
