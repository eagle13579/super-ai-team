import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="超级AI团队 - 高可用适配器", version="1.2.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 平台调用函数 (带超时控制) ---

def call_dify(query: str, user: str):
    """尝试调用 Dify"""
    url = f"{os.getenv('DIFY_API_URL')}/chat-messages"
    headers = {"Authorization": f"Bearer {os.getenv('DIFY_API_KEY')}"}
    payload = {"inputs": {}, "query": query, "response_mode": "blocking", "user": user}
    
    # 设置 10 秒超时，防止无限等待
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status() # 如果返回 4xx 或 5xx 错误，抛出异常
    return {"reply": response.json().get("answer"), "source": "Dify (Primary)"}

def call_openai_backup(query: str):
    """作为备份调用 OpenAI"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OpenAI API Key 未配置")
        
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": query}]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
    return {"reply": response.json()['choices'][0]['message']['content'], "source": "OpenAI (Backup)"}

# --- 核心调度逻辑 ---

@app.post("/chat")
async def chat(query: str, user: str = "ace_user"):
    """
    智能路由接口：优先使用 Dify，失败则自动切换到 OpenAI
    """
    errors = []

    # 第一步：尝试 Dify (主线路)
    try:
        print(f"[{os.environ.get('CURRENT_TIME', '00:51')}] 正在尝试主线路 (Dify)...")
        return {"status": "success", "data": call_dify(query, user)}
    except Exception as e:
        error_msg = f"Dify 线路异常: {str(e)}"
        print(f"⚠️ {error_msg}")
        errors.append(error_msg)

    # 第二步：如果第一步失败，自动尝试 OpenAI (备用线路)
    try:
        print(f"[{os.environ.get('CURRENT_TIME', '00:51')}] 正在切换至备用线路 (OpenAI)...")
        return {"status": "success", "data": call_openai_backup(query)}
    except Exception as e:
        error_msg = f"OpenAI 线路也异常: {str(e)}"
        print(f"❌ {error_msg}")
        errors.append(error_msg)

    # 如果所有线路都挂了，才返回错误
    raise HTTPException(
        status_code=503, 
        detail={"message": "所有 AI 服务暂时不可用", "errors": errors}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)