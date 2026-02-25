import numpy as np
import sys
import copy

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
            })
            continue

        for m in members:
            sort_idx = np.argsort(m['freq'])
            m['freq'] = m['freq'][sort_idx]
            m['amp'] = m['amp'][sort_idx]

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
        for m in members:
            interp_amps.append(np.interp(f_common, m['freq'], m['amp']))
        
        avg_amp = np.mean(interp_amps, axis=0)

        averaged.append({
            'filename': f"avg_{mean_temp:.0f}K ({len(members)} scans)",
            'temperature': mean_temp,
            'freq': f_common,
            'amp': avg_amp,
        })

    averaged.sort(key=lambda x: x['temperature'])
    return averaged, group_info

freq1 = np.linspace(0.3, 2.0, 500)
amp1 = 0.50 - 0.15 * np.exp(-((freq1 - 1.0)**2) / (2 * 0.02**2))
freq2 = np.linspace(0.3, 2.0, 500)
amp2 = 0.48 - 0.14 * np.exp(-((freq2 - 1.0)**2) / (2 * 0.02**2))
freq3 = np.linspace(0.31, 1.99, 480) # different axis
amp3 = np.full_like(freq3, 0.52) # flat line, no dip!

files = [
    {'filename': 's1.txt', 'temperature': 70.0, 'freq': freq1.copy(), 'amp': amp1.copy()},
    {'filename': 's2.txt', 'temperature': 70.0, 'freq': freq2.copy(), 'amp': amp2.copy()},
    {'filename': 's3.txt', 'temperature': 70.0, 'freq': freq3.copy(), 'amp': amp3.copy()},
]

avg_all, _ = average_by_temperature(copy.deepcopy(files))
print("AVG OF OUTLIER + 2 GOOD SCANS:")
a_all = avg_all[0]
idx_1thz = np.argmin(np.abs(a_all['freq'] - 1.0))
print(f"  At 1 THz: {a_all['amp'][idx_1thz]:.6f}")

avg_good, _ = average_by_temperature(copy.deepcopy(files[:2]))
print("AVG OF 2 GOOD SCANS ONLY:")
a_g = avg_good[0]
idx_1thz = np.argmin(np.abs(a_g['freq'] - 1.0))
print(f"  At 1 THz: {a_g['amp'][idx_1thz]:.6f}")

# Check diff
print(f"Difference: {abs(a_all['amp'][idx_1thz] - a_g['amp'][idx_1thz]):.6f}")
