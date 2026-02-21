import numpy as np
from scipy.fft import fft, fftfreq
from scipy.signal import savgol_filter
import sys  # Using sys to print errors to stderr for better visibility in logs


class DielectricCalculator:
    def __init__(self, thickness=0.5):
        self.d = thickness  # mm
        self.c = 0.29979  # mm/ps

    def calculate_all(self, ref_data, sample_list, smooth=5):
        t_r = ref_data['time']
        E_r = ref_data['E_field']

        if len(t_r) < 2:
            print("DIAGNOSTIC_ERROR: Reference data 'time' array is too short.", file=sys.stderr)
            return []

        dt = t_r[1] - t_r[0]
        if dt <= 0:
            print(f"DIAGNOSTIC_ERROR: Invalid time step '{dt}' in reference data.", file=sys.stderr)
            return []

        npad = len(t_r) * 4
        freq = fftfreq(npad, d=dt)
        S_r = fft(E_r, n=npad)
        pos = freq > 0
        freq_pos = freq[pos]
        S_r_pos = S_r[pos]

        results = []
        for s in sample_list:
            fname = s.get('filename', 'N/A')
            temp = s.get('temperature', 'N/A')
            if fname == ref_data.get('filename'):
                continue

            try:
                n_len = min(len(t_r), len(s.get('time', [])))
                if n_len < 2:
                    print(
                        f"DIAGNOSTIC_WARNING: Skipping {fname} due to insufficient time-domain data (points: {n_len}).",
                        file=sys.stderr)
                    continue

                S_s = fft(s['E_field'][:n_len], n=npad)

                epsilon = 1e-15
                H = S_s[pos] / (S_r_pos + epsilon)

                amp_H = np.abs(H)
                freq_mask = (freq_pos >= 0.5) & (freq_pos <= 2.5)
                if freq_mask.any():
                    mx = np.percentile(amp_H[freq_mask], 99.9)
                    if mx > 0.95:
                        H *= 0.95 / mx

                n, k, e1, e2 = self._params(freq_pos, H)

                if smooth > 1:
                    for arr in [n, k, e1, e2]:
                        if arr is not None and np.any(np.isfinite(arr)):
                            try:
                                arr[:] = savgol_filter(arr, int(smooth), 3)
                            except Exception as sav_e:
                                print(f"DIAGNOSTIC_WARNING: savgol_filter failed for {fname}: {sav_e}", file=sys.stderr)

                results.append({'temp': temp, 'freq': freq_pos, 'n': n, 'k': k, 'e1': e1, 'e2': e2})

            except Exception as e:
                print(f"DIAGNOSTIC_ERROR: Processing file {fname} at {temp}K failed: {repr(e)}", file=sys.stderr)
                continue
        return results

    def _params(self, freq, H):
        omega = 2 * np.pi * freq
        omega[omega == 0] = 1e-12

        amp = np.abs(H)
        phi = np.unwrap(np.angle(H))

        n = 1 + self.c * phi / (omega * self.d)

        n_plus_1_is_zero = (n == -1)
        n[n_plus_1_is_zero] = -1 + 1e-9

        F = (4 * n) / ((n + 1) ** 2)
        F_is_zero = (F == 0)
        F[F_is_zero] = 1e-9

        t = amp / F
        t[t < 0] = 1e-10

        k = -(self.c / (omega * self.d)) * np.log(np.clip(t, 1e-10, 1.0))
        k[k < 0] = 0
        return n, k, n ** 2 - k ** 2, 2 * n * k