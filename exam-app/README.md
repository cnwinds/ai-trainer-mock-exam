# 人工智能训练师（二级）刷题系统

## 启动
双击项目根目录 `启动刷题系统.bat`（或在 `exam-app` 目录运行 `python server.py`），浏览器打开 http://127.0.0.1:8848/ 。只依赖 Python 标准库。

## 功能
| 页面 | 用途 |
|---|---|
| 学习看板 | 倒计时、14 天计划、知识点掌握度、短板诊断 |
| 模拟考试 | 按评分框架随机组卷（判断 10/单选 40/多选 10/简答 40），限时，可按短板加权抽题 |
| 专项练习 | 选知识点/题型，逐题即时判分 + 解析 + 答题思路 |
| 错题本 | 错题自动收录，连续答对 2 次移出 |
| 实操 B/C | 2025 真题 B1.1~C + 新编案例，限时作答，checklist 自评 + 参考答案 |
| 2025 真题解析 | 83 道理论题完整答案 + 解析 + 答题思路，可遮挡答案自测；备考文档 |
| 评卷记录 | 主观题提交记录与 AI 评卷结果 |

## AI 评卷
- **服务端自动评卷**：交卷后答卷存到 `submissions/`，服务端调用 `config.json` 里配置的大模型（OpenAI 兼容接口），按评分要点逐项打分，写入 `feedback/`。页面自动轮询显示分数、逐项理由与改进写法，并修正知识点掌握度。评卷记录页可“重新评卷”。
- **Cursor 深度评卷**：在 Cursor 聊天里说 **“评卷”**，AI 会复核答卷，并按短板追加新题到 `data/bank/ai_round*.json`。

### 配置评卷模型
```bash
python tools/import_pi_model.py glm-5.3-flash   # 从 ~/.pi/agent/models.json 导入，生成 config.json
python grader.py --ping                         # 测试连通
```
也可以复制 `config.example.json` 为 `config.json` 手动填写，或用环境变量 `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` 覆盖。`config.json` 含密钥，已被 `.gitignore` 排除。

## 部署到公网服务器
1. 服务器安装 Python 3.8+，拉取代码：`git clone git@github.com:cnwinds/ai-trainer-mock-exam.git /opt/ai-trainer-mock-exam`
2. 在 `exam-app/` 下创建 `config.json`（参考 `config.example.json`）：
   - `host` 设为 `0.0.0.0`，`port` 按需；
   - **必须设置 `auth.password`**，否则任何人都能访问并消耗模型额度（浏览器会弹出账号密码框）；
   - `llm.base_url` 必须是**服务器能访问到的地址**。pi 里 `glm-5.3-flash` 的地址 `192.168.11.39` 是内网 IP，公网服务器访问不到，需要把该网关暴露到公网（如反向代理/内网穿透），或换成公网可达的模型接口。
3. 运行：`python3 server.py --no-browser`；长期运行可用 `deploy/ai-trainer-exam.service`（systemd，按实际路径和用户修改后 `systemctl enable --now ai-trainer-exam`）。
4. 建议用 Nginx/Caddy 反代并开启 HTTPS（Basic Auth 密码在 HTTP 下是明文传输）。
5. 数据都在 `exam-app/data/progress.json`、`submissions/`、`feedback/`，迁移时一起复制。系统按单用户设计，多人共用会共享同一份进度。

## 数据
- `data/bank/*.json`：题库（`y2025_*` 真题；`new_*` 新编；`ai_round*` AI 按短板追加）
- `data/progress.json`：做题进度（也存浏览器 localStorage）
- `tools/validate.py`：题库校验；`tools/build_y2025*.py`：从 `_text/` 重建真题数据
