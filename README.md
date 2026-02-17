# THz Spectroscopy Analysis Studio v3.0

**Publication-quality THz data analysis · Science/Nature figure standards**

中文版说明：太赫兹光谱分析工作站，符合 Science/Nature 期刊投稿图表标准

---

## 📦 Installation / 安装

### Local use / 本地使用

**Windows:**
```bash
# Extract thz3.tar.gz to a folder
cd path\to\thz3
run.bat
```

**Mac/Linux:**
```bash
tar -xzf thz_studio_v3.tar.gz
cd thz3
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open browser at `http://localhost:8501`

---

## 🌐 Internet Sharing / 互联网共享

### Option 1: LAN sharing (same WiFi) / 局域网共享（同一WiFi）

**Easiest for supervisor in same lab / 适合实验室内与导师共享**

```bash
streamlit run app.py --server.address 0.0.0.0
```

CMD will show:
```
  Local URL:   http://localhost:8501         (你自己用)
  Network URL: http://192.168.1.5:8501       (发给导师)
```

Share the **Network URL** with your supervisor. They just open it in browser.  
把 Network URL 发给导师，他在浏览器打开即可。

⚠️ **Important**: Keep CMD window running / CMD窗口必须保持开启

---

### Option 2: Streamlit Cloud (free, global access) / 云端部署（免费，全球访问）

**Best for remote collaboration / 适合远程协作**

#### Step 1: Create GitHub repository / 创建 GitHub 仓库

1. Go to https://github.com/new
2. Create a new repository (name: `thz-analysis`)
3. Upload these files:
   - `app.py`
   - `requirements.txt`
   - `modules/` (entire folder)

#### Step 2: Deploy to Streamlit Cloud / 部署到云端

1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repository: `your-username/thz-analysis`
5. Main file path: `app.py`
6. Click **Deploy**

Wait 2-3 minutes. You'll get a permanent URL like:
```
https://your-app-name.streamlit.app
```

Share this URL with anyone worldwide!  
将此链接分享给全世界任何人！

---

### Option 3: ngrok (temporary tunnel) / ngrok 临时通道

**Quick demo without GitHub / 无需 GitHub 的快速演示**

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8501
```

You'll get a temporary URL like:
```
https://abc123.ngrok.io
```

⚠️ URL expires when you close ngrok / 关闭 ngrok 后链接失效

---

## 🎨 Features / 功能特性

### Publication-quality figures / 论文级图表
- Nature/Science journal standards
- Helvetica font, 8 pt text, 1.2 pt lines
- Colorblind-safe palettes
- 300 DPI PDF/PNG/SVG export
- Panel labels (a, b, c, d)

### Analysis workflow / 分析流程
1. **ROI & Fitting** — Fano resonance analysis
2. **BCS Analysis** — Order parameter Δ(T)
3. **Waterfall** — Temperature evolution
4. **Dielectric** — n, k, ε₁, ε₂
5. **Peak Detail** — Single-temperature view
6. **Export** — Excel, PDF report, figure pack

### Bilingual UI / 双语界面
- English primary interface
- Chinese annotations below each section
- 英文主界面 + 中文注释

---

## 📊 Usage / 使用方法

### 1. Upload data / 上传数据
- Upload `.txt` files (sidebar)
- Filename must contain temperature: `sample_300K.txt`

### 2. Select ROI / 选择感兴趣区域
- Use sliders to select peak region
- Click **"Run batch Fano fitting"**

### 3. View results / 查看结果
- BCS fit extracts T_c (critical temperature)
- Waterfall plot shows temperature evolution
- Single peak view shows detailed fit

### 4. Export / 导出
- Excel: all parameters
- PDF report: BCS + waterfall + fits
- Figure pack: all individual fits

---

## 🔧 Configuration / 配置

### Sidebar settings / 侧边栏设置
- **Smoothing window** — Savitzky-Golay filter width (1-15)
- **T_c mode** — Auto-optimize or manually fix
- **Export DPI** — 150 (screen) / 300 (print) / 600 (high-res)
- **Format** — PDF / PNG / SVG

---

## 📚 Citation / 引用

If you use this software in your research, please cite:

```
THz Spectroscopy Analysis Studio v3.0
https://github.com/[your-username]/thz-analysis
```

---

## 🐛 Troubleshooting / 故障排查

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### "Port 8501 is already in use"
```bash
streamlit run app.py --server.port 8502
```

### Plots not showing / 图表不显示
- Check browser console (F12)
- Try different browser (Chrome recommended)
- Clear browser cache

### Data loading failed / 数据加载失败
- Check file encoding (UTF-8)
- Ensure filename contains temperature: `300K` or `300 K`
- Verify data starts after line 15

---

## 📧 Contact / 联系方式

For bugs or feature requests, open an issue on GitHub:  
https://github.com/[your-username]/thz-analysis/issues

---

**Version**: 3.0  
**Last updated**: 2026-02-17  
**License**: MIT
