# 远行商人 · 实时商品

洛克王国世界 — 远行商人每日商品实时查询 App

## 功能

- 📦 **实时商品数据** — 通过 GitHub Actions 每15分钟自动从 onebiji.com 抓取
- ⏱ **刷新倒计时** — 实时显示距下一轮结束的倒计时
- 🔄 **4轮切换** — 点击标签查看每轮商品（08:00 / 12:00 / 16:00 / 20:00）
- 📱 **手机适配** — 专为手机屏幕设计，单手可操作
- 🔁 **自动刷新** — 每60秒自动拉取最新数据
- 🖼 **商品图片** — 直接显示游戏内道具图标
- 🕐 **智能状态** — 自行判断北京时间，不依赖数据源的 status 字段

## 数据管道

```
onebiji.com（源头）
    ↓ GitHub Actions 每15分钟抓取
我们自己的 data/merchant.json
    ↓ 托管在 GitHub
App 直接读取（实时、可控）
```

- 数据抓取器：`fetch_merchant.py` — Python 脚本，从 onebiji.com 解析商品
- 定时任务：`.github/workflows/fetch-merchant.yml` — 每天 08:00-24:00 每15分钟运行
- 备用源：`rocokingdomworld.org/data/merchant.json`（当自有源不可用时自动切换）

## 使用前必须配置

### 1. 推送代码到 GitHub

```bash
cd E:\ai\luoke-merchant
git init
git add .
git commit -m "远行商人App v2.0"
git remote add origin https://github.com/你的用户名/luoke-merchant.git
git push -u origin main
```

### 2. 设置 GitHub Username（在 App 里）

App 安装到手机后，在浏览器打开一次，按 F12 → Console 输入：

```js
localStorage.setItem('gh_user', '你的GitHub用户名')
```

然后刷新页面，App 就会优先读取你自己维护的实时数据。

> 不设置也没关系，App 会自动降级使用 rocokingdomworld.org 的备用数据源。

## 打包 APK

### 方法一：Android Studio

1. 用 Android Studio 打开 `android/` 目录
2. Ctrl+F9 构建
3. APK 在 `android/app/build/outputs/apk/debug/app-debug.apk`

### 方法二：GitHub Actions 自动构建

推送代码后，到 GitHub 仓库 → Actions → 构建远行商人 APK → 下载 Artifacts

## 项目结构

```
luoke-merchant/
├── www/
│   └── index.html           ← 核心应用（单文件）
├── data/
│   └── merchant.json        ← GitHub Actions 自动更新
├── fetch_merchant.py        ← 数据抓取脚本
├── requirements.txt
├── android/                 ← Capacitor 安卓项目
├── .github/workflows/
│   ├── fetch-merchant.yml   ← 定时抓取数据
│   └── build-apk.yml        ← 在线构建 APK
├── build-apk.bat
└── package.json
```
