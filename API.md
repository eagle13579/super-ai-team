# 超级AI团队 API 文档

## 1. 概述

超级AI团队是一个基于多Agent协作的智能系统，提供了完整的AI团队架构，包括接入与意图层、角色与编排层、技能与执行层、记忆与持久层、工作流与验证层和基础设施层。

## 2. 核心API

### 2.1 接入与意图层

#### 2.1.1 多平台适配器

- **Webhook适配器**
  - 路径: `/api/webhook`
  - 方法: `POST`
  - 描述: 接收来自Webhook的消息
  - 请求体: 
    ```json
    {
      "user_id": "user123",
      "content": "帮我搜索一下Python的列表推导式",
      "message_id": "msg123",
      "metadata": {}
    }
    ```
  - 响应: 
    ```json
    {
      "status": "success",
      "message": "消息已处理"
    }
    ```

### 2.2 技能与执行层

#### 2.2.1 技能管理

- **列出所有技能**
  - 路径: `/api/skills`
  - 方法: `GET`
  - 描述: 获取所有可用技能
  - 响应: 
    ```json
    {
      "skills": ["web_search", "file_operations"]
    }
    ```

- **获取技能信息**
  - 路径: `/api/skills/{skill_name}`
  - 方法: `GET`
  - 描述: 获取指定技能的详细信息
  - 响应: 
    ```json
    {
      "name": "web_search",
      "version": "1.0.0",
      "description": "执行网络搜索并返回结构化结果",
      "input_schema": {...},
      "output_schema": {...}
    }
    ```

#### 2.2.2 工具执行

- **执行工具**
  - 路径: `/api/tools/execute`
  - 方法: `POST`
  - 描述: 执行指定工具
  - 请求体: 
    ```json
    {
      "tool_name": "web_search",
      "parameters": {
        "query": "Python列表推导式",
        "limit": 5
      }
    }
    ```
  - 响应: 
    ```json
    {
      "success": true,
      "result": {
        "results": [
          {
            "title": "搜索结果 1: Python列表推导式",
            "url": "https://example.com/search?q=Python列表推导式&page=1",
            "snippet": "这是关于Python列表推导式的搜索结果摘要...",
            "source_id": "source_1"
          }
        ]
      }
    }
    ```

### 2.3 记忆与持久层

#### 2.3.1 上下文管理

- **获取上下文**
  - 路径: `/api/context/{session_id}`
  - 方法: `GET`
  - 描述: 获取指定会话的上下文
  - 响应: 
    ```json
    {
      "session_id": "session123",
      "user_id": "user123",
      "conversation_history": [...],
      "working_memory": {}
    }
    ```

- **更新上下文**
  - 路径: `/api/context/{session_id}`
  - 方法: `PUT`
  - 描述: 更新指定会话的上下文
  - 请求体: 
    ```json
    {
      "working_memory": {
        "key": "value"
      }
    }
    ```
  - 响应: 
    ```json
    {
      "status": "success"
    }
    ```

## 3. 错误响应

所有API错误都会返回标准的错误格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

## 4. 示例使用

### 4.1 搜索示例

```bash
curl -X POST http://localhost:8000/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "web_search",
    "parameters": {
      "query": "人工智能最新进展",
      "limit": 3
    }
  }'
```

### 4.2 文件操作示例

```bash
curl -X POST http://localhost:8000/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "file_operations",
    "parameters": {
      "operation": "write",
      "path": "./test.txt",
      "content": "Hello, Super AI Team!"
    }
  }'
```
