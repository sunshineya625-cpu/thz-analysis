import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from modules.science_plot import apply_plotly_style, temp_cmap

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

# We use hash_funcs to prevent hashing issues with dicts
@st.cache_data(hash_funcs={list: id})
def average_by_temperature(files, tol=1.0):
    """Group files by temperature (±tol K) and average within each group."""
    # ... Implementation goes here, identical to original but cached
    from collections import defaultdict

    sorted_files = sorted(files, key=lambda d: d['temperature'])
    groups = []
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
    group_info = {}
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

        f_min = max(m['freq'].min() for m in members)
        f_max = min(m['freq'].max() for m in members)
        steps = [np.median(np.diff(m['freq'])) for m in members if len(m['freq']) > 1]
        df = min(steps) if steps else 0.001
        f_common = np.arange(f_min, f_max, df)

        interp_amps = []
        interp_amps_db = []
        for m in members:
            interp_amps.append(np.interp(f_common, m['freq'], m['amp']))
            db_col = m.get('amp_db', m['amp'])
            interp_amps_db.append(np.interp(f_common, m['freq'], db_col))
        avg_amp = np.mean(interp_amps, axis=0)
        avg_amp_db = np.mean(interp_amps_db, axis=0)

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

def downsample_data(x, y, max_points=1000):
    """Simple linear step downsampling to avoid Plotly browser lag."""
    n = len(x)
    if n <= max_points:
        return x, y
    step = n // max_points
    return x[::step], y[::step]
