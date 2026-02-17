# 🚀 快速启动指南

## Windows 本地运行（3步）

### 第一步：解压
解压 `thz_studio_v3_final.tar.gz` 到任意文件夹

### 第二步：打开CMD
在解压后的 `thz3` 文件夹里，地址栏输入 `cmd` 按回车

### 第三步：运行
```bash
run.bat
```

浏览器自动打开 `http://localhost:8501`

---

## 互联网共享（局域网，推荐）

### 如果你和导师在同一WiFi：

**在CMD里改用这个命令**：
```bash
python -m streamlit run app.py --server.address 0.0.0.0
```

**看到的输出**：
```
  Local URL:   http://localhost:8501         ← 你用
  Network URL: http://192.168.1.5:8501       ← 发给导师
```

**把 Network URL 发给导师即可！**

---

## 全球互联网共享（Streamlit Cloud）

### 准备工作（5分钟，只需一次）：

1. **注册 GitHub**  
   去 https://github.com/signup

2. **创建仓库**  
   - 登录后点右上角 "+" → "New repository"
   - 名字：`thz-analysis`
   - 类型选 **Public**
   - 点 "Create repository"

3. **上传文件**  
   在仓库页面点 "uploading an existing file"，拖拽这些文件：
   - `app.py`
   - `requirements.txt`
   - `packages.txt`
   - `.streamlit/config.toml`
   - `modules/` 整个文件夹
   - `README.md`

4. **部署到云端**  
   - 去 https://streamlit.io/cloud
   - 用 GitHub 登录
   - 点 "New app"
   - Repository 选 `你的用户名/thz-analysis`
   - Main file: `app.py`
   - 点 "Deploy"

5. **等待2分钟**  
   完成后得到永久链接：
   ```
   https://你的应用名.streamlit.app
   ```

**分享这个链接，全世界任何人都能访问！**

---

## 使用流程

### 1. 上传数据
左侧边栏 → Upload THz data files → 选择 .txt 文件

### 2. ROI & 拟合
Tab ① → 拖动滑块选峰 → Run batch Fano fitting

### 3. 查看结果
- Tab ②：BCS 拟合，自动提取 Tc
- Tab ③：瀑布图，温度演化
- Tab ④：介电函数（可选）
- Tab ⑤：单峰详情 + 论文级图表下载

### 4. 导出
Tab ⑥ → Download Excel / Generate PDF report

---

## 📊 导出的图表已符合期刊标准

✅ **Nature / Science 投稿要求**：
- 字体：Helvetica 8 pt
- 线宽：1.0–1.4 pt
- DPI：300（可在侧边栏调 600）
- 格式：PDF / PNG / SVG
- 面板标签：a, b, c, d
- 颜色：色盲友好

**直接用于论文，无需额外处理！**

---

## ⚠️ 注意事项

### 数据文件要求
- 格式：.txt
- 文件名或表头**必须含温度**：`300K` 或 `300 K`
- 数据从第15行后开始
- 列顺序：Position | Time | E-field | Freq | Amp

### 运行要求
- Python 3.8 或更高
- Windows / Mac / Linux 均可
- 首次运行需联网下载依赖

### 局域网共享要求
- 你和导师在同一WiFi
- 你的电脑保持开启
- CMD 窗口不能关

---

## 🆘 遇到问题？

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Port 8501 already in use"
```bash
python -m streamlit run app.py --server.port 8502
```

### 图表不显示
- 清除浏览器缓存
- 换 Chrome 浏览器试试

---

**版本**: v3.0 Final  
**更新**: 2026-02-17  
**支持**: 见 README.md 和 DEPLOY_CN.md
