# 互联网共享指南

## 🌐 三种方式，按需选择

---

### 方案一：局域网共享（最简单）⭐⭐⭐

**适用场景**：你和导师在同一个WiFi下（实验室/办公室）

**步骤**：
```bash
cd D:\...\thz3
python -m streamlit run app.py --server.address 0.0.0.0
```

**看到这个**：
```
  Local URL:   http://localhost:8501         ← 你自己用
  Network URL: http://192.168.1.5:8501       ← 发给导师
```

**把 Network URL 发给导师，他在浏览器打开就行！**

⚠️ **重要**：
- 你的电脑必须保持开启
- CMD 窗口不能关
- 导师必须和你在同一WiFi

---

### 方案二：Streamlit Cloud（永久免费）⭐⭐⭐⭐⭐

**适用场景**：导师在外地，或需要长期分享

**步骤**：

#### 1. 注册 GitHub（如果没有账号）
去 https://github.com/signup 注册

#### 2. 创建仓库
1. 登录后，点右上角 **"+"** → **"New repository"**
2. 名字填：`thz-analysis`
3. 选 **Public**
4. 点 **"Create repository"**

#### 3. 上传代码
在仓库页面，点 **"uploading an existing file"**，拖拽这些文件/文件夹：
- `app.py`
- `requirements.txt`
- `modules` （整个文件夹）
- `README.md`

#### 4. 部署到 Streamlit Cloud
1. 去 https://streamlit.io/cloud
2. 用 GitHub 账号登录
3. 点 **"New app"**
4. 选择：
   - Repository: `你的用户名/thz-analysis`
   - Branch: `main`
   - Main file path: `app.py`
5. 点 **"Deploy"**

#### 5. 等待2-3分钟

你会得到一个**永久链接**：
```
https://你的应用名.streamlit.app
```

**把这个链接发给任何人，全世界都能访问！**

✅ **优点**：
- 完全免费
- 永久链接
- 你电脑可以关机
- 全球任何地方都能访问
- 代码更新后自动重新部署

❌ **缺点**：
- 需要有 GitHub 账号
- 首次部署稍微麻烦（但只需一次）

---

### 方案三：ngrok 临时隧道

**适用场景**：临时演示，不想注册 GitHub

**步骤**：

#### 1. 下载 ngrok
去 https://ngrok.com/download 下载 Windows 版

#### 2. 解压到任意文件夹

#### 3. 启动你的程序（正常方式）
```bash
cd D:\...\thz3
python -m streamlit run app.py
```

#### 4. 新开一个 CMD 窗口，运行 ngrok
```bash
cd 你解压ngrok的位置
ngrok http 8501
```

#### 5. 看到这个：
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8501
```

**把 `https://abc123.ngrok.io` 发给导师！**

⚠️ **注意**：
- 关闭 ngrok 窗口，链接立即失效
- 每次重启链接都会变
- 免费版有时间限制

---

## 🎯 推荐方案

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 实验室内演示 | 方案一（局域网） | 最快，0配置 |
| 长期与导师协作 | 方案二（Streamlit Cloud） | 永久链接，无需开机 |
| 快速临时分享 | 方案三（ngrok） | 不需要注册账号 |

---

## ❓ 常见问题

### Q: Streamlit Cloud 部署后报错？
**A**: 检查 `requirements.txt` 是否上传了。所有依赖必须在里面列出。

### Q: 局域网 URL 导师访问不了？
**A**: 确认：
1. 你们在同一个WiFi
2. 你的防火墙允许端口8501
3. CMD窗口保持运行

### Q: GitHub 上传文件夹怎么操作？
**A**: 
- 方法1：把 `modules` 文件夹压缩成 zip，上传后 GitHub 会自动解压
- 方法2：用 GitHub Desktop 软件，直接拖文件夹

### Q: Streamlit Cloud 免费版有限制吗？
**A**: 
- 资源限制：1 GB RAM（够用）
- 公开应用：无限制
- 私有应用：免费版只能1个

---

## 📞 需要帮助？

如果还有问题，告诉我：
1. 你选择哪个方案？
2. 卡在哪一步？
3. 看到什么错误信息？

我继续帮你！
