import numpy as np
import sys
import os

sys.path.insert(0, r"d:\Google Antigravity\work-place\thz-analysis")
from modules.data_loader import DataLoader
from modules.fano_fitter import FanoFitter
from test_avg_real import average_by_temperature, MockUpload

datadir = r"D:\Google Antigravity\work-place\Data test"
files = [
    "TNS 3_20260220183710_average.txt",
    "TNS 3_20260220183720_average.txt",
    "TNS 3_20260220183737_average.txt"
]

print("=== LOADING ===")
loader = DataLoader()
raw_dicts = []
for f in files:
    full = os.path.join(datadir, f)
    raw_dicts.append(loader.load_file(MockUpload(full)))

import copy
avg3, _ = average_by_temperature(copy.deepcopy(raw_dicts))
avg2, _ = average_by_temperature(copy.deepcopy(raw_dicts[:2]))

print("=== FITTING ===")
fitter = FanoFitter(smooth_window=5, remove_outliers=True)
roi = (0.8, 1.3)

import json
res = {}

try:
    r3 = fitter.fit(avg3[0]['freq'], avg3[0]['amp_db'], roi, 70.0, "Avg3")
    res["Avg3"] = {"f_r": r3['Peak_Freq_THz'], "depth": r3['Depth_dB'], "area": r3['Area']}
except Exception as e:
    res["Avg3"] = f"Error: {e}"

try:
    r2 = fitter.fit(avg2[0]['freq'], avg2[0]['amp_db'], roi, 70.0, "Avg2")
    res["Avg2"] = {"f_r": r2['Peak_Freq_THz'], "depth": r2['Depth_dB'], "area": r2['Area']}
except Exception as e:
    res["Avg2"] = f"Error: {e}"

with open("fano_out.json", "w") as f:
    json.dump(res, f, indent=2)

