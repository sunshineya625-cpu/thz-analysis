import numpy as np
from scipy.fft import fft, fftfreq
from scipy.signal import savgol_filter


class DielectricCalculator:
    def __init__(self, thickness=0.5):
        self.d = thickness  # mm
        self.c = 0.29979  # mm/ps

    def calculate_all(self, ref_data, sample_list, smooth=5):
        t_r = ref_data['time']
        E_r = ref_data['E_field']

        if len(t_r) < 2:
            print("DIAGNOSTIC_ERROR: Reference data 'time' array is too short to process.")
            return []

        dt = t_r[1] - t_r[0]
        if dt == 0:
            print("DIAGNOSTIC_ERROR: Time step in reference data is zero.")
            return []

        npad = len(t_r) * 4
        freq = fftfreq(npad, d=dt)
        S_r = fft(E_r, n=npad)
        pos = freq > 0
        freq_pos = freq[pos]
        S_r_pos = S_r[pos]

        results = []
        for s in sample_list:
            if s['filename'] == ref_data['filename']:
                continue

            try:
                n_len = min(len(t_r), len(s.get('time', [])))
                if n_len < 2:
                    print(
                        f"DIAGNOSTIC_WARNING: Skipping {s.get('filename', 'N/A')} due to insufficient time-domain data (points: {n_len}).")
                    continue

                S_s = fft(s['E_field'][:n_len], n=npad)

                # Add a small epsilon to avoid division by zero
                epsilon = 1e-15
                H = S_s[pos] / (S_r_pos + epsilon)

                # Gain limit (using percentile for robustness)
                amp_H = np.abs(H)
                freq_mask = (freq_pos >= 0.5) & (freq_pos <= 2.5)
                if freq_mask.any():
                    mx = np.percentile(amp_H[freq_mask], 99.9)
                    if mx > 0.95:  # Loosened the threshold slightly
                        H *= 0.95 / mx

                n, k, e1, e2 = self._params(freq_pos, H)

                if smooth > 1:
                    for arr in [n, k, e1, e2]:
                        if np.any(np.isfinite(arr)):
                            try:
                                arr[:] = savgol_filter(arr, int(smooth), 3)
                            except Exception as sav_e:
                                print(
                                    f"DIAGNOSTIC_WARNING: savgol_filter failed for {s.get('filename', 'N/A')}: {sav_e}")

                results.append({'temp': s['temperature'], 'freq': freq_pos, 'n': n, 'k': k, 'e1': e1, 'e2': e2})

            except Exception as e:
                # KEY CHANGE: Expose the hidden error instead of silently ignoring it.
                print(
                    f"DIAGNOSTIC_ERROR processing file {s.get('filename', 'N/A')} at {s.get('temperature', 'N/A')}K: {repr(e)}")
                continue
        return results

    def _params(self, freq, H):
        omega = 2 * np.pi * freq
        # Avoid division by zero if freq contains 0
        omega[omega == 0] = 1e-12

        amp = np.abs(H)
        phi = np.unwrap(np.angle(H))

        # Disabled this unstable phase correction
        # mf    = (freq > 0.5) & (freq < 1.0)
        # if mf.any():
        #     poly = np.polyfit(freq[mf], phi[mf], 1)
        #     phi -= round(poly[1] / (2*np.pi)) * 2*np.pi

        n = 1 + self.c * phi / (omega * self.d)

        # Add a check for n = -1 to avoid division by zero in F
        n_plus_1_is_zero = (n == -1)
        n[n_plus_1_is_zero] = -1 + 1e-9

        F = (4 * n) / ((n + 1) ** 2)
        F_is_zero = (F == 0)
        F[F_is_zero] = 1e-9  # Avoid division by zero for t

        t = amp / F
        # Ensure t is not negative before log
        t = np.clip(t, 1e-10, 1.0)

        k = -(self.c / (omega * self.d)) * np.log(t)
        k = np.maximum(k, 0)  # k must be non-negative
        return n, k, n ** 2 - k ** 2, 2 * n * k