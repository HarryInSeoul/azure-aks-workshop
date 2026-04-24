"""
AI Pet Recommendation Agent

펫 스토어 상품 카탈로그를 조회(Tool)하고 Azure OpenAI로 맞춤 추천(LLM)을 생성하는
AI Agent 서비스입니다. DEMO_MODE=true 시 Azure OpenAI 없이도 동작합니다.
"""

import json
import os
import logging

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from openai import AzureOpenAI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Pet Recommendation Agent", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# --- 설정 ---
PRODUCT_SERVICE_URL = os.environ.get("PRODUCT_SERVICE_URL", "http://product-service:3002")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
DEMO_MODE = os.environ.get("DEMO_MODE", "false").lower() == "true"

SYSTEM_PROMPT = """당신은 Contoso 펫 스토어의 AI 상품 추천 에이전트입니다.
고객의 요청을 분석하고, 제공된 상품 목록에서 가장 적합한 상품을 1~3개 추천해주세요.
반드시 한국어로 답변하세요.

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{"recommendations": [{"productId": 1, "name": "상품명", "price": 9.99, "reason": "추천 이유"}], "message": "종합 안내 메시지"}
"""


# --- 모델 ---
class RecommendRequest(BaseModel):
    query: str


class Recommendation(BaseModel):
    productId: int
    name: str
    price: float
    reason: str


class RecommendResponse(BaseModel):
    recommendations: list[Recommendation]
    message: str
    mode: str


# --- 도구: 상품 카탈로그 조회 ---
async def fetch_products() -> list[dict]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{PRODUCT_SERVICE_URL}/")
        resp.raise_for_status()
        return resp.json()


# --- 데모 모드 폴백 ---
def demo_recommend(query: str, products: list[dict]) -> dict:
    selected = products[:3]
    return {
        "recommendations": [
            {
                "productId": p.get("id", i + 1),
                "name": p.get("name", "상품"),
                "price": p.get("price", 0),
                "reason": f"'{query}' 검색에 매칭된 인기 상품입니다.",
            }
            for i, p in enumerate(selected)
        ],
        "message": f"[데모 모드] '{query}' 관련 인기 상품 {len(selected)}개를 추천합니다.",
    }


# --- 엔드포인트 ---
@app.get("/health")
async def health():
    mode = "demo" if DEMO_MODE else "azure-openai"
    ready = True

    if not DEMO_MODE and (not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY):
        ready = False

    return {
        "status": "ok" if ready else "degraded",
        "service": "ai-agent",
        "mode": mode,
        "ready": ready,
    }


@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest):
    # Step 1: 상품 카탈로그 조회 (Tool Use)
    try:
        products = await fetch_products()
    except Exception as e:
        logger.error("상품 서비스 연결 실패: %s", e)
        raise HTTPException(status_code=502, detail=f"상품 서비스 연결 실패: {e}")

    # Step 2: 추천 생성
    if DEMO_MODE:
        logger.info("데모 모드로 추천 생성")
        result = demo_recommend(request.query, products)
        return RecommendResponse(**result, mode="demo")

    # Step 3: Azure OpenAI를 통한 AI 추천 (LLM Reasoning)
    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
        )

        product_list = json.dumps(
            [{"id": p.get("id"), "name": p.get("name"), "price": p.get("price"),
              "description": p.get("description", "")} for p in products],
            ensure_ascii=False,
        )

        user_prompt = f"상품 목록:\n{product_list}\n\n고객 요청: {request.query}"

        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        return RecommendResponse(**result, mode="azure-openai")

    except json.JSONDecodeError:
        logger.error("LLM 응답 파싱 실패: %s", content)
        raise HTTPException(status_code=500, detail="AI 응답 파싱 실패")
    except Exception as e:
        logger.error("Azure OpenAI 호출 실패: %s", e)
        raise HTTPException(status_code=500, detail=f"AI 서비스 오류: {e}")
