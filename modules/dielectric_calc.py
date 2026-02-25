import numpy as np
from scipy.fft import fft, fftfreq
from scipy.signal import savgol_filter
from modules.logger import get_logger

log = get_logger("thz.dielectric")


class DielectricCalculator:
    def __init__(self, thickness=0.5):
        self.d = thickness  # mm
        self.c = 0.29979  # mm/ps

    def calculate_all(self, ref_data, sample_list, smooth=5):
        t_r = ref_data['time']
        E_r = ref_data['E_field']

        if len(t_r) < 2:
            log.error("Reference data 'time' array is too short.")
            return []

        dt = t_r[1] - t_r[0]
        if dt <= 0:
            log.error(f"Invalid time step '{dt}' in reference data.")
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
                    log.warning(
                        f"Skipping {fname}: insufficient time-domain data ({n_len} pts).")
                    continue

                E_s_arr = s['E_field'][:n_len]
                t_s_arr = s.get('time', [])

                # 1. To prevent phase unwrapping failure (phase jumps > pi),
                # we mathematically align the sample pulse to the reference pulse.
                idx_peak_r = np.argmax(np.abs(E_r))
                idx_peak_s = np.argmax(np.abs(E_s_arr))
                shift_idx = idx_peak_s - idx_peak_r
                
                # Shift sample array by shift_idx (pad with 0)
                E_s_aligned = np.zeros_like(E_s_arr)
                if shift_idx > 0:
                    E_s_aligned[:-shift_idx] = E_s_arr[shift_idx:]
                elif shift_idx < 0:
                    E_s_aligned[-shift_idx:] = E_s_arr[:shift_idx]
                else:
                    E_s_aligned[:] = E_s_arr[:]

                S_s_aligned = fft(E_s_aligned, n=npad)
                epsilon = 1e-15
                H_aligned = S_s_aligned[pos] / (S_r_pos + epsilon)

                amp_H = np.abs(H_aligned)
                freq_mask = (freq_pos >= 0.5) & (freq_pos <= 2.5)
                if freq_mask.any():
                    mx = np.percentile(amp_H[freq_mask], 99.9)
                    if mx > 0.95:
                        amp_H *= 0.95 / mx
                
                # 2. Extract safe unwrapped phase from aligned signals
                phi_aligned = np.unwrap(np.angle(H_aligned))
                
                # 3. Add back the mathematical array shift in frequency domain
                omega = 2 * np.pi * freq_pos
                tau_array_shift = shift_idx * dt
                phi_true = phi_aligned - omega * tau_array_shift

                # 4. Compensate for mechanical time delay stage (from data_loader)
                if len(t_s_arr) > 0 and len(t_r) > 0:
                    tau_stage = t_s_arr[0] - t_r[0]
                    phi_true = phi_true - omega * tau_stage
                    
                # Calculate optical constants using reconstructed phi_true and amp_H
                n, k, e1, e2 = self._params(freq_pos, amp_H, phi_true)

                if smooth > 1:
                    for arr in [n, k, e1, e2]:
                        if arr is not None and np.any(np.isfinite(arr)):
                            try:
                                arr[:] = savgol_filter(arr, int(smooth), 3)
                            except Exception as sav_e:
                                log.warning(f"savgol_filter failed for {fname}: {sav_e}")

                results.append({'temp': temp, 'freq': freq_pos, 'n': n, 'k': k, 'e1': e1, 'e2': e2})

            except Exception as e:
                log.error(f"Processing file {fname} at {temp}K failed: {repr(e)}")
                continue
        return results

    def _params(self, freq, amp, phi):
        omega = 2 * np.pi * freq
        omega[omega == 0] = 1e-12

        # -------------------------------------------------------------
        # CRUCIAL PHYSICS FIX: 
        # For a standard forward FFT (using e^{-i\omega t} convention), 
        # a time-delayed sample has a NEGATIVE phase relative to the reference.
        # Thus, phi = -\omega * (n - 1) * d / c.
        # Solving for n gives: n = 1 - c * phi / (\omega * d)
        # -------------------------------------------------------------
        n = 1 - self.c * phi / (omega * self.d)

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