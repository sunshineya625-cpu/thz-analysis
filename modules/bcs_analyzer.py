import numpy as np
from scipy.optimize import curve_fit

class BCSAnalyzer:
    def __init__(self, tc_fixed=None):
        self.tc_fixed = tc_fixed

    def bcs(self, T, amp, Tc, beta=1.76):
        val = np.zeros_like(T, dtype=float)
        m   = T < Tc
        if m.any():
            val[m] = amp * np.tanh(beta * np.sqrt(np.maximum(0, Tc/T[m] - 1)))
        return val

    def fit(self, temps, values):
        mask = ~np.isnan(values) & (values > 0)
        T, y = temps[mask], values[mask]
        if len(T) < 4:
            return None
        A0 = float(np.max(y))
        try:
            if self.tc_fixed is None:
                popt, _ = curve_fit(self.bcs, T, y,
                    p0=[A0, 330., 1.76],
                    bounds=([0, 290, 0.3], [np.inf, 360, 8.]),
                    maxfev=8000)
                return tuple(popt)
            else:
                def f(T, amp, beta):
                    return self.bcs(T, amp, self.tc_fixed, beta)
                popt, _ = curve_fit(f, T, y, p0=[A0, 1.76],
                    bounds=([0, 0.3], [np.inf, 8.]), maxfev=8000)
                return (popt[0], self.tc_fixed, popt[1])
        except Exception:
            return None
