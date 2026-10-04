# 报考小助手 · 离线重构版 2.0

本工程根据原 Windows 离线包重建，不是原作者源码的逐字还原。原有 31 个业务模型的可编辑声明和原 SQLite 种子数据得到保留；业务接口、Vue 界面、测试与启动器为重新实现的源码。

## 客户运行

解压完整目录，双击交付目录的 `一键启动.cmd`。程序自动初始化数据、检查迁移、启动本机服务并打开默认浏览器。无需安装 Python、Node.js 或数据库，无需联网。关闭启动器会停止服务。不要只移动 exe；必须保留 `_internal` 和 `data`。

默认管理员：`admin / Admin@123456`。普通体验账号：`demo / Demo@123456`。正式使用前到个人中心修改默认密码。

## 源码结构

- `backend/core/models.py`：原有业务模型；`extensions.py`：公共服务与报考数据模型。
- `backend/core/accounts.py`：登录、注册、密码、档案与令牌版本。
- `backend/core/catalog.py`：招考查询、公告、题库与公共服务读取。
- `backend/core/personal.py`：个人报考、计划、收藏、比较、通知、咨询。
- `backend/core/administration.py`、`registry.py`：统一后台 CRUD、数据表单与权限。
- `backend/services/matching.py`：资格匹配与可解释推荐。
- `backend/services/exams.py`：服务器计时、持久化答题、判分、错题与薄弱分析。
- `backend/services/operations.py`：xlsx 导入导出、审计与 SQLite 备份恢复。
- `frontend/src/pages`、`components`：完整 Vue 3 页面与组件。
- `backend/launcher.py`：初始化、单实例、端口选择、启动界面与 Waitress 服务。
- `qa/`、`backend/core/tests.py`：自动测试和发布打包脚本。

## 开发环境

本次验证环境：Windows 11 x64、Python 3.12.10、Node.js、Django 5.2.17、Vue 3.5.43、Vite 7.3.6；依赖的实际版本固定在 requirements-lock.txt 与 frontend/pnpm-lock.yaml。

首次开发环境安装需要联网，客户运行包不需要。安装 Python 3.12，运行 `setup_source.cmd`，然后 `start_source.cmd`。源码已附带前端构建产物。

修改前端时，在 `frontend` 目录运行：

```powershell
pnpm install --frozen-lockfile
pnpm run dev
pnpm run build
```

前端开发代理默认连接 127.0.0.1:8765，后台启动后可用。生产构建输出到 backend/frontend_dist。

## 验证与再打包

```powershell
.venv\Scripts\python.exe backend\manage.py test core
.venv\Scripts\python.exe -m PyInstaller --noconfirm build_portable.spec
.venv\Scripts\python.exe qa\package_release.py
```

也可运行 `build_windows.cmd`。构建前关闭从 source/dist 启动的程序，避免 Windows 占用文件。发布脚本拒绝覆盖已有客户运行目录；再次发布请使用 `--output-root` 指定新的空输出目录。

`qa/runtime_smoke.py` 可以验证可执行文件的初次启动、重启持久化和备份恢复。必须指定独立测试 data 目录，不要使用真实业务 data。

`qa/browser_smoke.cjs` 为真实浏览器端到端测试。需自行安装 Playwright，使用 PLAYWRIGHT_MODULE 指向该模块路径；EXAM_QA_BROWSER 可指定已安装的 Edge。EXAM_QA_URL 指向测试实例。测试会创建报考记录、咨询、组卷和备份，仅应连接测试数据库。

## 数据兼容与边界

0001_initial 是基于原包最终结构重建的合并基线。原种子数据库中的旧迁移记录保留；启动时仅执行新增结构迁移，不清空用户数据。新应用恢复功能只接受完整且结构兼容的当前版本数据库备份；旧版数据库不能在恢复界面直接混用。

所有历史招考信息与题目仍保留原有演示标记，不是实时官方数据。公共服务的外部官方入口需要网络；本地咨询只给本机管理员处理。本应用没有真实官方报名接口、短信/邮件服务或云端数据同步。报考记录和后台审核不代替官方报名及官方资格审核。

个人记录页面一次最多读取 100 条；成绩页最多最近 300 次；推荐最多计算 1000 个目标、显示前 30 条。招考查询、公告、题库和后台数据使用分页。高数据量、多用户公网部署不属于此次离线验收范围。

导入请使用本版本后台生成的英文列名模板；JSON 列使用 JSON。旧版中文列名模板应先转换。逐行校验，部分失败不会伪报全部成功；错误行和原因会保存在导入日志中。

程序只监听本机地址，SQLite 未加密；备份含个人信息，请妥善保存。可执行文件未购买代码签名证书，Windows 可能显示来源提示；可核验交付清单的 SHA256。测试通过不等于所有未知环境都绝无问题。
