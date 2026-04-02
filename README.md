# super-ai-team
超级AI团队

## 项目概述

超级AI团队是一个基于多Agent协作的智能系统，整合了24个开源AI项目的核心结构模块，重新组合成一套**超级AI团队最佳实践架构**。

### 核心设计理念

- **意图驱动 (Intent-Driven)**
- **协议优先 (Protocol-First)**
- **角色分离 (Role-Separation)**
- **记忆融合 (Memory-Fusion)**
- **工具原子化 (Atomic-Tools)**
- **安全沙箱 (Secure-Sandbox)**
- **执行闭环 (Execution-Loop)**
- **多语言一致性 (Parity-Audit)**

## 系统架构

### 五层架构模型

1. **接入与意图层**：多平台适配器、意图识别引擎、任务路由器
2. **角色与编排层**：角色工厂、规划编排器、子Agent调度器、状态机管理
3. **技能与执行层**：技能注册中心、工具执行器、MCP适配器、安全沙箱
4. **记忆与持久层**：上下文管理器、记忆网格、向量数据库、知识库
5. **工作流与验证层**：执行反馈循环、多语言一致性审计、团队协作模式

## 技术栈

- **语言**：Python 3.9+
- **框架**：FastAPI
- **数据库**：PostgreSQL
- **缓存**：Redis
- **向量检索**：pgvector
- **容器**：Docker
- **监控**：Prometheus + Grafana
- **测试**：pytest

## 快速开始

### 安装依赖

```bash
# 使用Poetry管理依赖
poetry install

# 或使用pip
pip install -r requirements.txt
```

### 运行项目

```bash
# 开发模式
python main.py

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 测试

```bash
python -m pytest tests/ -v
```

## 核心功能

### 1. 意图识别
- 关键词匹配
- 语义向量检索
- Few-shot示例学习

### 2. 角色系统
- 可配置的角色定义
- 角色工厂模式
- 支持多种角色类型

### 3. 技能执行
- 标准化的技能注册
- 工具执行器
- 安全沙箱

### 4. 记忆管理
- 三级记忆架构（热记忆、温记忆、冷记忆）
- 上下文管理
- 记忆融合

### 5. 工作流
- 执行反馈循环
- 多语言一致性审计
- 团队协作模式

## API文档

详细的API文档请参考 [API.md](API.md) 文件。

## 目录结构

```
super-ai-team/
├── src/
│   ├── access_intent/          # 接入与意图层
│   ├── role_orchestration/      # 角色与编排层
│   ├── skill_execution/         # 技能与执行层
│   ├── memory_persistence/      # 记忆与持久层
│   ├── workflow_validation/     # 工作流与验证层
│   └── infrastructure/          # 基础设施层
├── tests/                       # 测试文件
├── main.py                      # 项目入口
├── pyproject.toml              # 项目配置
├── API.md                       # API文档
└── README.md                    # 项目说明
```

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 许可证

本项目使用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
