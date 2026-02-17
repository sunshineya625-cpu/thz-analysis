"""
FanoFitter — replicates THzdata.py fitting logic exactly
"""
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter


class FanoFitter:
    def __init__(self, smooth_window=5, remove_outliers=True):
        self.smooth_window   = smooth_window if smooth_window % 2 == 1 else smooth_window + 1
        self.remove_outliers = remove_outliers

    # ── public ──────────────────────────────────────────────────────────────
    def fit(self, freq, amp, roi, temperature, filename):
        f1, f2 = roi
        mask = (freq >= f1) & (freq <= f2)
        f_roi = freq[mask]
        a_roi = amp[mask].copy()

        if len(f_roi) < 10:
            raise ValueError("ROI too narrow (<10 pts)")

        # outlier removal
        if self.remove_outliers:
            a_roi = self._remove_outliers(a_roi)

        # smoothing
        if self.smooth_window > 1 and len(a_roi) > self.smooth_window:
            try:
                a_roi = savgol_filter(a_roi, self.smooth_window, 3)
            except Exception:
                pass

        # initial guesses
        k_g = (a_roi[-1] - a_roi[0]) / (f_roi[-1] - f_roi[0])
        b_g = a_roi[0] - k_g * f_roi[0]
        fr_g = f_roi[np.argmin(a_roi)]

        p0     = [fr_g, 0.1, 0.1, 0.0, k_g, b_g]
        bounds = ([f_roi[0], 0, 0, -np.pi, -np.inf, -np.inf],
                  [f_roi[-1], np.inf, np.inf,  np.pi,  np.inf,  np.inf])

        popt, _ = curve_fit(self._fano, f_roi, a_roi, p0=p0,
                            bounds=bounds, maxfev=10000)
        fr, kappa, gamma, phi, k_b, b_b = popt

        # ── derived quantities ────────────────────────────────────────────
        h_dB   = self._depth_dB(kappa, gamma, phi)

        baseline      = k_b * f_roi + b_b
        signal        = baseline - a_roi          # flip to positive peak
        peak_idx      = np.argmax(signal)
        peak_x        = f_roi[peak_idx]
        linear_depth  = float(signal[peak_idx])

        half = linear_depth / 2.0
        above = np.where(signal >= half)[0]
        if len(above) > 1:
            left_x  = f_roi[above[0]]
            right_x = f_roi[above[-1]]
            fwhm    = float(right_x - left_x)
        else:
            left_x  = peak_x - gamma / 2
            right_x = peak_x + gamma / 2
            fwhm    = float(gamma)

        try:
            area = float(np.trapezoid(signal, f_roi))
        except AttributeError:
            area = float(np.trapz(signal, f_roi))

        # fitted curve over roi
        fitted = self._fano(f_roi, *popt)
        ss_res = np.sum((a_roi - fitted) ** 2)
        ss_tot = np.sum((a_roi - a_roi.mean()) ** 2)
        r2     = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        return {
            'Temperature_K': temperature,
            'Filename':       filename,
            'Peak_Freq_THz':  float(fr),
            'Fano_Kappa':     float(kappa),
            'Fano_Gamma':     float(gamma),
            'Fano_Phi':       float(phi),
            'Depth_dB':       float(h_dB),
            'Linear_Depth':   linear_depth,
            'FWHM_THz':       fwhm,
            'Area':           area,
            'Baseline_k':     float(k_b),
            'Baseline_b':     float(b_b),
            'R_squared':      r2,
            # arrays for plotting
            'freq_roi':       f_roi,
            'signal':         signal,
            'fitted_signal':  baseline - fitted,   # fitted signal (same space)
            'half_height':    half,
            'left_x':         float(left_x),
            'right_x':        float(right_x),
            'peak_x':         float(peak_x),
        }

    # ── private ─────────────────────────────────────────────────────────────
    @staticmethod
    def _fano(f, fr, kappa, gamma, phi, k_b, b_b):
        denom = -1j * (f - fr) + (gamma + kappa) / 2.0
        term  = 1.0 - kappa * np.exp(1j * phi) / denom
        return (k_b * f + b_b) * np.abs(term) ** 2

    @staticmethod
    def _depth_dB(kappa, gamma, phi):
        denom = (gamma + kappa) / 2.0
        term  = 1.0 - kappa * np.exp(1j * phi) / denom
        return float(10 * np.log10(np.abs(term) ** 2))

    @staticmethod
    def _remove_outliers(data, thr=5.0):
        out = data.copy()
        diff = np.abs(np.diff(out))
        med  = np.median(diff)
        for idx in np.where(diff > med * thr)[0]:
            if 0 < idx < len(out) - 1:
                out[idx] = (out[idx-1] + out[idx+1]) / 2.0
        return out
