import re
import numpy as np

class DataLoader:
    def load_file(self, file_obj):
        filename = file_obj.name
        try:
            content = file_obj.read().decode('utf-8', errors='ignore')
        except Exception as e:
             raise ValueError(f"Could not read or decode file {filename}: {e}")

        lines = content.splitlines()
        temperature = self._extract_temperature(content, filename)

        header_row = 15
        for i, ln in enumerate(lines):
            if 'Pos. [um]' in ln or ('Freq' in ln and 'Amp' in ln):
                header_row = i + 1
                break

        data_lines = lines[header_row:]
        rows = []
        for ln in data_lines:
            ln = ln.strip()
            if not ln: continue
            try:
                vals = [float(x) for x in ln.split()]
                if len(vals) >= 5:
                    rows.append(vals)
            except ValueError:
                continue

        if not rows:
            raise ValueError(f"No valid data rows found in {filename}")

        arr = np.array(rows)
        
        # Extract start position for delay stage correction
        start_pos = 0.0
        for line in lines[:15]:
            if line.startswith('Start Position'):
                try: 
                    start_pos = float(line.split('Position')[1].strip())
                except: pass

        time_full    = arr[:, 1].astype(float)
        
        # Compensate for delay stage mechanical shift if present
        # Δtime = Δpos / c. Using c = 299.79 um/ps. addition aligns the data in absolute time
        if start_pos != 0.0:
            time_full = time_full + (start_pos / 299.792458)
            
        E_field_full = arr[:, 2].astype(float)
        freq         = arr[:, 3].astype(float)
        amp          = arr[:, 4].astype(float)
        amp_db       = arr[:, 5].astype(float) if arr.shape[1] >= 6 else amp.copy()

        mask = (freq > 0)
        
        # Ensure all arrays have consistent lengths after masking
        freq_masked = freq[mask]
        amp_masked = amp[mask]
        amp_db_masked = amp_db[mask]

        return {
            'filename':    filename,
            'temperature': temperature,
            'start_pos':   start_pos,
            'time':        time_full,
            'E_field':     E_field_full,
            'freq':        freq_masked,
            'amp':         amp_masked,
            'amp_db':      amp_db_masked,
        }

    def _extract_temperature(self, content, filename):
        for line in content.splitlines()[:15]:
            if 'description' in line.lower():
                m = re.search(r'(\d+(?:\.\d+)?)\s*[Kk]', line, re.IGNORECASE)
                if m: return float(m.group(1))
        m = re.search(r'(\d+(?:\.\d+)?)\s*[Kk]', filename, re.IGNORECASE)
        if m: return float(m.group(1))
        return -1.0