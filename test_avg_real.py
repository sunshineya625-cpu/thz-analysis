import numpy as np
import sys
import os
import traceback

sys.path.insert(0, r"d:\Google Antigravity\work-place\thz-analysis")
from modules.data_loader import DataLoader
from collections import defaultdict

def average_by_temperature(files, tol=1.0):
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
                'time': m.get('time', np.array([])),
                'E_field': m.get('E_field', np.array([])),
                'n_averaged': 1,
                'source_files': fnames,
            })
            continue

        for m in members:
            sort_idx = np.argsort(m['freq'])
            m['freq'] = m['freq'][sort_idx]
            m['amp'] = m['amp'][sort_idx]
            if 'amp_db' in m: m['amp_db'] = m['amp_db'][sort_idx]

        ref = members[0]
        f_min = max(m['freq'].min() for m in members)
        f_max = min(m['freq'].max() for m in members)

        if f_min >= f_max:
            m = members[0]
            averaged.append({
                'filename': f"avg_{mean_temp:.0f}K (NO OVERLAP)",
                'temperature': mean_temp,
                'freq': m['freq'].copy(),
                'amp': m['amp'].copy(),
                'amp_db': m.get('amp_db', m['amp']).copy(),
                'time': m.get('time', np.array([])),
                'E_field': m.get('E_field', np.array([])),
                'n_averaged': len(members),
                'source_files': fnames,
            })
            continue

        ref_mask = (ref['freq'] >= f_min) & (ref['freq'] <= f_max)
        f_common = ref['freq'][ref_mask]

        if len(f_common) < 2:
            steps = [np.median(np.abs(np.diff(m['freq']))) for m in members if len(m['freq']) > 1]
            df = min(steps) if steps else 0.001
            n_pts = max(2, int(round((f_max - f_min) / df)))
            f_common = np.linspace(f_min, f_max, n_pts)

        interp_amps = []
        interp_amps_db = []
        for m in members:
            interp_amps.append(np.interp(f_common, m['freq'], m['amp']))
            adb = m.get('amp_db', m['amp'])
            interp_amps_db.append(np.interp(f_common, m['freq'], adb))
        
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


datadir = r"D:\Google Antigravity\work-place\Data test"
files = [
    "TNS 3_20260220183710_average.txt",
    "TNS 3_20260220183720_average.txt",
    "TNS 3_20260220183737_average.txt"
]

class MockUpload:
    def __init__(self, p):
        self.name = os.path.basename(p)
        self.data = open(p, "rb").read()
    def read(self):
        return self.data

print("=== LOADING ===")
try:
    loader = DataLoader()
    raw_dicts = []
    for f in files:
        full = os.path.join(datadir, f)
        raw_dicts.append(loader.load_file(MockUpload(full)))

    import json
    res = {}
    for i, d in enumerate(raw_dicts):
        f = d['freq']
        a = d['amp']
        adb = d.get('amp_db', d['amp'])
        idxtest = np.argmin(np.abs(f - 1.0))
        res[f"Scan_{i}"] = {"amp": float(a[idxtest]), "db": float(adb[idxtest])}

    import copy
    avg3, _ = average_by_temperature(copy.deepcopy(raw_dicts))
    a3 = avg3[0]
    idx3 = np.argmin(np.abs(a3['freq'] - 1.0))
    res["Avg3"] = {"amp": float(a3['amp'][idx3]), "db": float(a3.get('amp_db', a3['amp'])[idx3])}

    avg2, _ = average_by_temperature(copy.deepcopy(raw_dicts[:2]))
    a2 = avg2[0]
    idx2 = np.argmin(np.abs(a2['freq'] - 1.0))
    res["Avg2"] = {"amp": float(a2['amp'][idx2]), "db": float(a2.get('amp_db', a2['amp'])[idx2])}

    with open("test_out.json", "w") as f:
        json.dump(res, f, indent=2)
except Exception as e:
    import traceback
    with open("test_out.json", "w") as f:
        f.write(traceback.format_exc())
