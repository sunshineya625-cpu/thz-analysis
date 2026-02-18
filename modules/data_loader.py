"""
DataLoader — mirrors the exact parsing logic in THzdata.py:
  np.genfromtxt(path, skip_header=15)  →  col3=freq, col4=amp
"""
import re
import numpy as np

class DataLoader:
    def load_file(self, file_obj):
        filename = file_obj.name
        raw = file_obj.read()
        # decode
        content = raw.decode('utf-8', errors='ignore')
        lines   = content.splitlines()

        temperature = self._extract_temperature(content, filename)

        # ── find the data block: skip_header=15 means skip first 15 lines ──
        # But some files may have more/fewer header lines; we detect the start
        # by finding "Pos. [um]" header or just using row 15 as fallback.
        header_row = 15          # default (matches original code)
        for i, ln in enumerate(lines):
            if 'Pos. [um]' in ln or ('Freq' in ln and 'Amp' in ln):
                header_row = i + 1
                break

        data_lines = lines[header_row:]
        rows = []
        for ln in data_lines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                vals = [float(x) for x in ln.split()]
                if len(vals) >= 5:
                    rows.append(vals)
            except ValueError:
                continue

        if not rows:
            raise ValueError(f"No data found in {filename} (tried skip_header={header_row})")

        arr     = np.array(rows)
        freq    = arr[:, 3].astype(float)
        amp     = arr[:, 4].astype(float)          # THz AMP FD
        amp_db  = arr[:, 5].astype(float) if arr.shape[1] >= 6 else amp.copy()  # THz AMP dB
        time    = arr[:, 1].astype(float)
        E_field = arr[:, 2].astype(float)

        # filter: freq>0, amp>1e-6  (same as original)
        mask    = (freq > 0) & (amp > 1e-6)
        return {
            'filename':    filename,
            'temperature': temperature,
            'freq':        freq[mask],
            'amp':         amp[mask],
            'amp_db':      amp_db[mask],
            'time':        time[mask],
            'E_field':     E_field[mask],
        }

    # ── temperature extraction (same priority as original) ────────────────
    def _extract_temperature(self, content, filename):
        for line in content.splitlines()[:15]:
            if 'description' in line.lower():
                m = re.search(r'(\d+(?:\.\d+)?)\s*[Kk]', line, re.IGNORECASE)
                if m:
                    return float(m.group(1))
        m = re.search(r'(\d+(?:\.\d+)?)\s*[Kk]', filename, re.IGNORECASE)
        if m:
            return float(m.group(1))
        return -1.0
