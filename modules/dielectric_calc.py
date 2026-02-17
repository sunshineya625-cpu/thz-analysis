import numpy as np
from scipy.fft import fft, fftfreq
from scipy.signal import savgol_filter

class DielectricCalculator:
    def __init__(self, thickness=0.5):
        self.d = thickness          # mm
        self.c = 0.29979            # mm/ps

    def calculate_all(self, ref_data, sample_list, smooth=5):
        t_r  = ref_data['time']
        E_r  = ref_data['E_field']
        dt   = t_r[1] - t_r[0]
        npad = len(t_r) * 4
        freq = fftfreq(npad, d=dt)
        S_r  = fft(E_r, n=npad)
        pos  = freq > 0
        freq_pos = freq[pos]
        S_r_pos  = S_r[pos]

        results = []
        for s in sample_list:
            if s['filename'] == ref_data['filename']:
                continue
            try:
                n_len = min(len(t_r), len(s['time']))
                S_s   = fft(s['E_field'][:n_len], n=npad)
                H     = S_s[pos] / S_r_pos
                # gain limit
                amp_H = np.abs(H)
                mx    = np.max(amp_H[(freq_pos >= 0.5) & (freq_pos <= 2.5)])
                if mx > 0.85:
                    H *= 0.85 / mx

                n, k, e1, e2 = self._params(freq_pos, H)
                if smooth > 1:
                    for arr in [n, k, e1, e2]:
                        try:
                            arr[:] = savgol_filter(arr, smooth, 3)
                        except Exception:
                            pass
                results.append({'temp': s['temperature'],
                                'freq': freq_pos, 'n': n, 'k': k,
                                'e1': e1, 'e2': e2})
            except Exception:
                continue
        return results

    def _params(self, freq, H):
        omega = 2 * np.pi * freq
        amp   = np.abs(H)
        phi   = np.unwrap(np.angle(H))
        mf    = (freq > 0.5) & (freq < 1.0)
        if mf.any():
            poly = np.polyfit(freq[mf], phi[mf], 1)
            phi -= round(poly[1] / (2*np.pi)) * 2*np.pi
        n = 1 - self.c * phi / (omega * self.d)
        F = (4*n) / (n+1)**2
        t = amp / F
        t = np.clip(t, 1e-10, 1.0)
        k = -(self.c / (omega * self.d)) * np.log(t)
        k = np.maximum(k, 0)
        return n, k, n**2 - k**2, 2*n*k
