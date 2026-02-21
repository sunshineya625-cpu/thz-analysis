import re
import numpy as np


class DataLoader:
    def load_file(self, file_obj):
        filename = file_obj.name
        raw = file_obj.read()
        # decode
        content = raw.decode('utf-8', errors='ignore')
        lines = content.splitlines()

        temperature = self._extract_temperature(content, filename)

        # Find the data block start
        header_row = 15  # default
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

        arr = np.array(rows)

        # --- CRITICAL FIX: SEPARATE DOMAIN PROCESSING ---

        # 1. Process Time-Domain data: Keep it complete and unfiltered
        time_full = arr[:, 1].astype(float)
        E_field_full = arr[:, 2].astype(float)

        # 2. Process Frequency-Domain data with filtering
        freq = arr[:, 3].astype(float)
        amp = arr[:, 4].astype(float)
        amp_db = arr[:, 5].astype(float) if arr.shape[1] >= 6 else amp.copy()

        # The mask should ONLY be applied to frequency-domain arrays
        mask = (freq > 0) & (amp > 1e-6)

        return {
            'filename': filename,
            'temperature': temperature,
            # Return complete, unfiltered time-domain data
            'time': time_full,
            'E_field': E_field_full,
            # Return filtered frequency-domain data
            'freq': freq[mask],
            'amp': amp[mask],
            'amp_db': amp_db[mask],
        }

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