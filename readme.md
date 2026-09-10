# 第一步：安装 Python 依赖
pip install -r requirements.txt
# 第二步：下载 Chromium 浏览器内核（必须单独执行，只跑一次）
playwright install chromium

# === 终端1：启动后端 ===
cd D:\myCode\hobby\bili\backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# === 终端2：启动前端（需要 src 源码） ===
cd D:\myCode\hobby\bili\frontend
npm run dev
