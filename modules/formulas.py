"""
formulas.py — Centralized formula documentation for THz Analysis Studio v3.1
Contains LaTeX expressions, parameter descriptions, and physical explanations.
"""


# ═══════════════════════════════════════════════════════════════
# FANO RESONANCE
# ═══════════════════════════════════════════════════════════════

FANO_FORMULA = r"""
$$
T(f) = \bigl(k \cdot f + b\bigr)\,
\left|1 - \frac{\kappa\, e^{i\varphi}}{-i\,(f - f_r) + \frac{\gamma+\kappa}{2}}\right|^2
$$
"""

FANO_PARAMS = {
    "f_r": {
        "name": "Resonance frequency / 共振频率",
        "unit": "THz",
        "desc": (
            "**EN**: The center frequency of the phonon mode. "
            "A downshift (softening) upon cooling often indicates "
            "coupling to an electronic order parameter.\n\n"
            "**中文**: 声子模式的中心频率。降温时频率下移（软化）"
            "通常表明声子与电子序参量耦合。"
        ),
    },
    "κ (kappa)": {
        "name": "Coupling strength / 耦合强度",
        "unit": "THz",
        "desc": (
            "**EN**: Measures the coupling between the discrete phonon "
            "and the electronic continuum. Larger κ → stronger "
            "Fano asymmetry.\n\n"
            "**中文**: 描述离散声子态与电子连续谱之间的耦合强度。"
            "κ 越大，Fano 不对称性越强。"
        ),
    },
    "γ (gamma)": {
        "name": "Intrinsic linewidth / 本征线宽",
        "unit": "THz",
        "desc": (
            "**EN**: Natural damping rate of the phonon. "
            "Broader linewidth means shorter phonon lifetime "
            "(τ ≈ 1/(πγ)).\n\n"
            "**中文**: 声子的本征阻尼率。线宽越大，声子寿命越短 "
            "(τ ≈ 1/(πγ))。"
        ),
    },
    "φ (phi)": {
        "name": "Fano phase / Fano 相位",
        "unit": "rad",
        "desc": (
            "**EN**: Phase angle controlling the asymmetric line shape. "
            "φ = 0 gives a symmetric Lorentzian dip; "
            "φ ≠ 0 produces the characteristic Fano asymmetry.\n\n"
            "**中文**: 控制不对称线型的相位角。φ=0 为对称 Lorentzian 谷，"
            "φ≠0 产生 Fano 不对称特征。"
        ),
    },
    "k (slope)": {
        "name": "Baseline slope / 基线斜率",
        "unit": "a.u./THz",
        "desc": (
            "**EN**: Linear baseline slope. The baseline `k·f + b` "
            "accounts for the broadband background transmission.\n\n"
            "**中文**: 线性基线斜率。基线 `k·f + b` 用于拟合宽带背景透射。"
        ),
    },
    "b (intercept)": {
        "name": "Baseline intercept / 基线截距",
        "unit": "a.u.",
        "desc": (
            "**EN**: Linear baseline intercept.\n\n"
            "**中文**: 线性基线截距。"
        ),
    },
}

FANO_EXPLANATION = (
    "**EN**: The Fano resonance model describes interference between a "
    "discrete phonon mode and an electronic continuum. "
    "In THz spectroscopy of correlated materials like Ta₂NiSe₅, "
    "the Fano line shape reflects the electron–phonon coupling strength. "
    "The fit is performed via `scipy.optimize.curve_fit` with bounded parameters.\n\n"
    "**中文**: Fano 共振模型描述离散声子模式与电子连续谱之间的干涉效应。"
    "在 Ta₂NiSe₅ 等关联材料的 THz 光谱中，Fano 线型反映了电声耦合强度。"
    "拟合使用 `scipy.optimize.curve_fit` 并带参数边界约束。"
)


# ═══════════════════════════════════════════════════════════════
# DERIVED QUANTITIES (from Fano fit)
# ═══════════════════════════════════════════════════════════════

DEPTH_DB_FORMULA = r"""
$$
h_{\mathrm{dB}} = 10\,\log_{10}\!\left|1 - \frac{\kappa\, e^{i\varphi}}{(\gamma+\kappa)/2}\right|^2
$$
"""

DEPTH_DB_EXPLANATION = (
    "**EN**: Peak depth in decibels. Measures the maximum attenuation "
    "of the phonon dip relative to the baseline. "
    "Larger |h| indicates a deeper phonon absorption.\n\n"
    "**中文**: 以分贝为单位的峰深度。衡量声子谷相对于基线的最大衰减，"
    "|h| 越大表示声子吸收越深。"
)

LINEAR_DEPTH_FORMULA = r"""
$$
\mathrm{Depth} = \mathrm{baseline}(f_{\mathrm{peak}}) - \mathrm{signal}(f_{\mathrm{peak}})
$$
"""

LINEAR_DEPTH_EXPLANATION = (
    "**EN**: Linear (non-logarithmic) depth: the vertical distance from "
    "the baseline to the bottom of the phonon dip in amplitude units. "
    "Used as a proxy for the order parameter strength.\n\n"
    "**中文**: 线性深度：基线到声子谷底的振幅距离。"
    "常作为序参量强度的替代指标。"
)

FWHM_FORMULA = r"""
$$
\mathrm{FWHM} = f_{\mathrm{right}} - f_{\mathrm{left}}
\quad \text{where}\;\; \mathrm{signal}(f) \ge \frac{\mathrm{Depth}}{2}
$$
"""

FWHM_EXPLANATION = (
    "**EN**: Full Width at Half Maximum — the frequency range over which "
    "the signal exceeds half of the peak depth. "
    "Proportional to phonon damping rate. Broadening near T_c indicates "
    "enhanced scattering.\n\n"
    "**中文**: 半高全宽 — 信号超过峰深度一半的频率范围。"
    "与声子阻尼率成正比，在 T_c 附近展宽说明散射增强。"
)

AREA_FORMULA = r"""
$$
\mathrm{Area} = \int_{f_1}^{f_2} \bigl[\mathrm{baseline}(f) - \mathrm{signal}(f)\bigr]\, df
\approx \sum_{i}\frac{(s_i + s_{i+1})}{2}\,\Delta f_i
$$
"""

AREA_EXPLANATION = (
    "**EN**: Integrated spectral weight (oscillator strength) of the phonon "
    "mode, computed via trapezoidal rule. "
    "More robust against noise than peak depth alone.\n\n"
    "**中文**: 声子模式的积分光谱权重（振子强度），用梯形法则计算。"
    "对噪声的鲁棒性优于单纯的峰深度。"
)

R_SQUARED_FORMULA = r"""
$$
R^2 = 1 - \frac{SS_{\mathrm{res}}}{SS_{\mathrm{tot}}}
= 1 - \frac{\sum(y_i - \hat{y}_i)^2}{\sum(y_i - \bar{y})^2}
$$
"""

R_SQUARED_EXPLANATION = (
    "**EN**: Coefficient of determination. R² > 0.97 indicates excellent fit; "
    "R² < 0.90 suggests the model may not adequately describe the data.\n\n"
    "**中文**: 决定系数。R² > 0.97 表示拟合优秀；R² < 0.90 表明模型可能不够充分。"
)


# ═══════════════════════════════════════════════════════════════
# BCS ORDER PARAMETER
# ═══════════════════════════════════════════════════════════════

BCS_FORMULA = r"""
$$
\Delta(T) = A \cdot \tanh\!\left(\beta\,\sqrt{\frac{T_c}{T} - 1}\right),
\quad T < T_c
$$
"""

BCS_PARAMS = {
    "A (Amplitude)": {
        "name": "Amplitude / 振幅",
        "unit": "a.u.",
        "desc": (
            "**EN**: Zero-temperature value of the order parameter. "
            "In our case, this is the saturated depth or area at low T.\n\n"
            "**中文**: 序参量的零温值。对应低温下饱和的深度或面积。"
        ),
    },
    "T_c": {
        "name": "Critical temperature / 临界温度",
        "unit": "K",
        "desc": (
            "**EN**: Phase transition temperature. Above T_c, the order "
            "parameter vanishes. For Ta₂NiSe₅, typically ~326–328 K.\n\n"
            "**中文**: 相变温度。高于 T_c 时序参量消失。"
            "Ta₂NiSe₅ 通常 ~326–328 K。"
        ),
    },
    "β (beta)": {
        "name": "Coupling exponent / 耦合指数",
        "unit": "dimensionless / 无量纲",
        "desc": (
            "**EN**: Controls the sharpness of the transition. "
            "BCS weak-coupling gives β ≈ 1.76. Deviations suggest "
            "strong coupling or unconventional order.\n\n"
            "**中文**: 控制相变的陡峭程度。BCS 弱耦合理论给出 β ≈ 1.76，"
            "偏离提示强耦合或非常规序。"
        ),
    },
}

BCS_EXPLANATION = (
    "**EN**: The BCS-type order parameter function is borrowed from "
    "superconductivity theory and widely used to characterize "
    "CDW / excitonic-insulator phase transitions. "
    "The hyperbolic tangent form approximately captures the mean-field "
    "temperature dependence near T_c.\n\n"
    "**中文**: BCS 型序参量函数源自超导理论，广泛用于 CDW / 激子绝缘体相变的表征。"
    "双曲正切形式近似捕捉了 T_c 附近的平均场温度依赖关系。"
)


# ═══════════════════════════════════════════════════════════════
# DIELECTRIC / OPTICAL CONSTANTS
# ═══════════════════════════════════════════════════════════════

TRANSFER_FUNC_FORMULA = r"""
$$
H(\omega) = \frac{S_{\mathrm{sample}}(\omega)}{S_{\mathrm{ref}}(\omega)}
= |H|\, e^{i\phi(\omega)}
$$
"""

REFRACTIVE_INDEX_FORMULA = r"""
$$
n(\omega) = 1 - \frac{c \cdot \phi(\omega)}{\omega \cdot d}
$$
"""

EXTINCTION_FORMULA = r"""
$$
k(\omega) = -\frac{c}{\omega \cdot d}\,\ln\!\left(\frac{|H|}{F(n)}\right),
\quad F(n) = \frac{4n}{(n+1)^2}
$$
"""

DIELECTRIC_FORMULA = r"""
$$
\varepsilon_1 = n^2 - k^2, \qquad
\varepsilon_2 = 2nk
$$
"""

DIELECTRIC_PARAMS = {
    "d (thickness)": {
        "name": "Sample thickness / 样品厚度",
        "unit": "mm",
        "desc": (
            "**EN**: Thickness of the sample used in the transmission "
            "measurement. Critical for accurate extraction of n and k.\n\n"
            "**中文**: 透射测量中使用的样品厚度，是准确提取 n 和 k 的关键参数。"
        ),
    },
    "c (speed)": {
        "name": "Speed of light in vacuum / 真空光速",
        "unit": "mm/ps (0.29979)",
        "desc": (
            "**EN**: Speed of light in convenient THz units: "
            "c = 0.29979 mm/ps.\n\n"
            "**中文**: THz 便利单位下的真空光速：c = 0.29979 mm/ps。"
        ),
    },
    "F(n)": {
        "name": "Fresnel transmission factor / 菲涅耳透射因子",
        "unit": "dimensionless / 无量纲",
        "desc": (
            "**EN**: Accounts for reflection losses at the sample surfaces. "
            "Assumes normal incidence on a slab with refractive index n.\n\n"
            "**中文**: 补偿样品表面的反射损失。假设折射率为 n 的薄片正入射。"
        ),
    },
}

DIELECTRIC_EXPLANATION = (
    "**EN**: The optical constants are extracted from the THz time-domain "
    "transmission. The complex transfer function H(ω) is obtained by FFT, "
    "then decomposed into phase → n(ω) and amplitude → k(ω). "
    "The dielectric function ε = ε₁ + iε₂ follows from ε = (n + ik)².\n\n"
    "**中文**: 光学常数从 THz 时域透射中提取。"
    "复传输函数 H(ω) 由 FFT 获得，然后分解为相位 → n(ω) 和振幅 → k(ω)。"
    "介电函数 ε = ε₁ + iε₂ 由 ε = (n + ik)² 得出。"
)


# ═══════════════════════════════════════════════════════════════
# WATERFALL OFFSET
# ═══════════════════════════════════════════════════════════════

WATERFALL_FORMULA = r"""
$$
y_i^{\prime}(f) = \mathrm{signal}_i(f) + i \times
\mathrm{median}(\text{peak heights}) \times m
$$
"""

WATERFALL_EXPLANATION = (
    "**EN**: Each spectrum is vertically shifted by an offset proportional "
    "to its index. The offset step is set by the median peak height "
    "multiplied by a user-defined factor *m*, ensuring curves do not overlap "
    "while preserving relative intensity information.\n\n"
    "**中文**: 每条光谱按其索引进行垂直偏移。偏移步长由中位峰高乘以"
    "用户定义的因子 *m* 决定，确保曲线不重叠同时保留相对强度信息。"
)


# ═══════════════════════════════════════════════════════════════
# EXPORT HELPER — Generate Markdown documentation
# ═══════════════════════════════════════════════════════════════

def generate_formula_doc(params_dict=None):
    """Generate a complete Markdown document of all formulas and current parameters."""
    doc = []
    doc.append("# THz Spectroscopy Analysis — Formula Documentation\n")
    doc.append("*Auto-generated by THz Analysis Studio v3.1*\n\n---\n")

    # 1) Fano
    doc.append("## 1. Fano Resonance / Fano 共振\n")
    doc.append(FANO_FORMULA.replace("$$", "$"))
    doc.append("\n" + FANO_EXPLANATION + "\n")
    doc.append("\n### Parameters / 参数\n")
    for k, v in FANO_PARAMS.items():
        doc.append(f"- **{k}** ({v['unit']}): {v['name']}\n")
        doc.append(f"  {v['desc']}\n")

    # 2) Derived
    doc.append("\n---\n## 2. Derived Quantities / 导出量\n")
    for title, formula, expl in [
        ("Peak Depth (dB) / 峰深度", DEPTH_DB_FORMULA, DEPTH_DB_EXPLANATION),
        ("Linear Depth / 线性深度", LINEAR_DEPTH_FORMULA, LINEAR_DEPTH_EXPLANATION),
        ("FWHM / 半高全宽", FWHM_FORMULA, FWHM_EXPLANATION),
        ("Integrated Area / 积分面积", AREA_FORMULA, AREA_EXPLANATION),
        ("R² / 决定系数", R_SQUARED_FORMULA, R_SQUARED_EXPLANATION),
    ]:
        doc.append(f"\n### {title}\n")
        doc.append(formula.replace("$$", "$"))
        doc.append("\n" + expl + "\n")

    # 3) BCS
    doc.append("\n---\n## 3. BCS Order Parameter / BCS 序参量\n")
    doc.append(BCS_FORMULA.replace("$$", "$"))
    doc.append("\n" + BCS_EXPLANATION + "\n")
    doc.append("\n### Parameters / 参数\n")
    for k, v in BCS_PARAMS.items():
        doc.append(f"- **{k}** ({v['unit']}): {v['name']}\n")
        doc.append(f"  {v['desc']}\n")

    # 4) Dielectric
    doc.append("\n---\n## 4. Optical Constants & Dielectric Functions / 光学常数与介电函数\n")
    doc.append("### Transfer Function / 传输函数\n")
    doc.append(TRANSFER_FUNC_FORMULA.replace("$$", "$"))
    doc.append("\n### Refractive Index / 折射率\n")
    doc.append(REFRACTIVE_INDEX_FORMULA.replace("$$", "$"))
    doc.append("\n### Extinction Coefficient / 消光系数\n")
    doc.append(EXTINCTION_FORMULA.replace("$$", "$"))
    doc.append("\n### Dielectric Function / 介电函数\n")
    doc.append(DIELECTRIC_FORMULA.replace("$$", "$"))
    doc.append("\n" + DIELECTRIC_EXPLANATION + "\n")
    doc.append("\n### Parameters / 参数\n")
    for k, v in DIELECTRIC_PARAMS.items():
        doc.append(f"- **{k}** ({v['unit']}): {v['name']}\n")
        doc.append(f"  {v['desc']}\n")

    # 5) Waterfall
    doc.append("\n---\n## 5. Waterfall Offset / 瀑布图偏移\n")
    doc.append(WATERFALL_FORMULA.replace("$$", "$"))
    doc.append("\n" + WATERFALL_EXPLANATION + "\n")

    # 6) Current parameter values
    if params_dict:
        doc.append("\n---\n## 6. Current Session Parameters / 当前会话参数\n")
        doc.append("| Parameter | Value |\n|---|---|\n")
        for k, v in params_dict.items():
            doc.append(f"| {k} | {v} |\n")

    return "\n".join(doc)
