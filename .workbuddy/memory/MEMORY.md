# 长期记忆

## 环境配置
- Claude Code 使用 DeepSeek API（Anthropic 兼容端点）: `https://api.deepseek.com/anthropic`
- 默认模型: `deepseek-v4-flash`，复杂任务: `deepseek-v4-pro`
- API Key 存储在 `~\.claude\settings.json` 的 `ANTHROPIC_AUTH_TOKEN` 环境变量中

## 文件布局
- VS Code、Claude Code、CC Switch 已迁移到 `D:\AI助理\`（通过 Windows Junction 实现 C 盘透明重定向）
- 原有 C 盘路径通过 Junction 指向 D 盘，对应用程序透明
- `D:\AI助理\` 目录结构: Microsoft VS Code, Code, .vscode, .claude, .cc-switch, com.ccswitch.desktop

## 用户偏好
- 使用简体中文沟通
- 偏好简洁、行动导向的回复风格
- 需要逐步拆解的指导步骤
- 安全意识强，会主动轮换暴露的凭据
