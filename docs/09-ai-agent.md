# 09. AI Agent 배포 (Azure OpenAI)

> 이 섹션에서는 **Azure OpenAI**를 활용한 **AI 상품 추천 에이전트**를 AKS에 배포합니다.
> 기존 펫 스토어의 상품 카탈로그를 조회(Tool)하고, LLM으로 맞춤 추천(Reasoning)을 생성하는 패턴을 체험합니다.

## AI Agent 패턴

```
고객 질문                    AI Agent (Python/FastAPI)
"활발한 고양이 장난감 추천해줘"  ─▶  ┌──────────────────────┐
                                │ 1. Tool: 상품 조회    │──▶ product-service:3002
                                │ 2. LLM: 맞춤 추천    │──▶ Azure OpenAI (GPT-4o)
                                └──────────────────────┘
                                         │
                                         ▼
                                  구조화된 추천 결과 (JSON)
```

### 개요

| 항목 | 내용 |
|------|------|
| 서비스 | `ai-agent` (Python FastAPI) |
| 포트 | 5100 |
| 엔드포인트 | `POST /recommend`, `GET /health` |
| 외부 의존 | Azure OpenAI (GPT-4o), product-service |
| 폴백 | `DEMO_MODE=true` — Azure OpenAI 없이 데모 추천 |

---

## 9-1. Azure OpenAI 리소스 생성

> **💡 이미 Azure OpenAI 리소스가 있다면** 이 단계를 건너뛰고 9-2로 이동하세요.  
> **Azure OpenAI가 없거나 빠르게 테스트만 하려면** [9-1-B. 데모 모드](#9-1-b-데모-모드-azure-openai-없이-실습)로 이동하세요.

```bash
# Azure OpenAI 리소스 생성
az cognitiveservices account create \
  --name workshop-openai \
  --resource-group $RESOURCE_GROUP \
  --kind OpenAI \
  --sku S0 \
  --location eastus \
  -o table
```

> ⚠️ Azure OpenAI는 일부 리전에서만 사용 가능합니다. `koreacentral`에서 불가능하면 `eastus`를 사용하세요.

### GPT-4o 모델 배포

```bash
az cognitiveservices account deployment create \
  --name workshop-openai \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-08-06" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard \
  -o table
```

### 엔드포인트 & 키 확인

```bash
# 엔드포인트
AOAI_ENDPOINT=$(az cognitiveservices account show \
  --name workshop-openai -g $RESOURCE_GROUP \
  --query "properties.endpoint" -o tsv)
echo "엔드포인트: $AOAI_ENDPOINT"

# API 키
AOAI_KEY=$(az cognitiveservices account keys list \
  --name workshop-openai -g $RESOURCE_GROUP \
  --query "key1" -o tsv)
echo "API 키: ${AOAI_KEY:0:8}..."
```

### 9-1-B. 데모 모드 (Azure OpenAI 없이 실습)

Azure OpenAI 리소스 없이도 AI Agent의 동작 흐름을 체험할 수 있습니다.  
데모 모드에서는 LLM 대신 규칙 기반으로 인기 상품을 추천합니다.

```bash
# 데모 모드용 더미 값 설정
AOAI_ENDPOINT="https://demo.openai.azure.com"
AOAI_KEY="demo-key"
```

> 9-3에서 ConfigMap의 `DEMO_MODE`를 `"true"`로 변경하면 됩니다.

---

## 9-2. AI Agent 빌드 & ACR 푸시

```bash
cd aks-store-demo-ko/src/ai-agent

# ACR에서 원격 빌드 & 푸시
az acr build \
  --registry $ACR_NAME \
  --image ai-agent:v1 \
  .
```

> ⏱ 약 1~2분 소요됩니다.

빌드 확인:

```bash
az acr repository show-tags --name $ACR_NAME --repository ai-agent -o table
```

```
Result
--------
v1
```

---

## 9-3. Kubernetes Secret & ConfigMap 생성

AI Agent가 Azure OpenAI에 접근하기 위한 자격증명을 Secret으로 생성합니다.

```bash
cd /home/hyehunlim/projects/AKS-Workshop

# Secret 생성 (API 키, 엔드포인트, 배포 이름)
kubectl create secret generic ai-agent-secrets \
  --namespace pets \
  --from-literal=AZURE_OPENAI_API_KEY="$AOAI_KEY" \
  --from-literal=AZURE_OPENAI_ENDPOINT="$AOAI_ENDPOINT" \
  --from-literal=AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
```

> **데모 모드로 실습하는 경우**, ConfigMap에서 `DEMO_MODE`를 `"true"`로 변경하세요:
> ```bash
> # 매니페스트 내 DEMO_MODE를 true로 변경
> sed -i 's/DEMO_MODE: "false"/DEMO_MODE: "true"/' workshop-manifests/90-ai-agent.yaml
> ```

---

## 9-4. AI Agent 배포

```bash
kubectl apply -f workshop-manifests/90-ai-agent.yaml
```

배포 상태 확인:

```bash
kubectl get pods -n pets -l app=ai-agent -w
```

```
NAME                        READY   STATUS    RESTARTS   AGE
ai-agent-xxx                1/1     Running   0          30s
```

Health 확인:

```bash
kubectl exec -n pets deploy/ai-agent -- wget -qO- http://localhost:5100/health
```

```json
{"status":"ok","service":"ai-agent","mode":"azure-openai","ready":true}
```

> 데모 모드에서는 `"mode":"demo"`로 표시됩니다.

---

## 9-5. AI 추천 테스트

### Port-Forward로 접속

```bash
kubectl port-forward -n pets svc/ai-agent 5100:5100 &
```

### 추천 요청

```bash
# 테스트 1: 고양이 장난감 추천
curl -s http://localhost:5100/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "활발한 고양이를 위한 장난감 추천해줘"}' | python3 -m json.tool
```

### 예상 출력 (Azure OpenAI 모드)

```json
{
    "recommendations": [
        {
            "productId": 2,
            "name": "짭짤한 선원의 삑삑 오징어",
            "price": 6.99,
            "reason": "삑삑 소리가 나서 활발한 고양이의 사냥 본능을 자극합니다."
        },
        {
            "productId": 5,
            "name": "해적 앵무새 낚싯대",
            "price": 8.99,
            "reason": "낚싯대 형태로 고양이와 인터랙티브 놀이가 가능합니다."
        }
    ],
    "message": "활발한 고양이에게는 사냥 본능을 자극하는 인터랙티브 장난감이 좋습니다!",
    "mode": "azure-openai"
}
```

### 다양한 질문 테스트

```bash
# 테스트 2: 선물 추천
curl -s http://localhost:5100/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "강아지 생일 선물로 뭐가 좋을까?"}' | python3 -m json.tool

# 테스트 3: 예산 기반 추천
curl -s http://localhost:5100/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "1만원 이하로 살 수 있는 상품 추천해줘"}' | python3 -m json.tool
```

### Port-Forward 종료

```bash
# 백그라운드 port-forward 종료
kill %1 2>/dev/null
```

---

## 9-6. (선택) 정리

```bash
# AI Agent 리소스 삭제
kubectl delete -f workshop-manifests/90-ai-agent.yaml
kubectl delete secret ai-agent-secrets -n pets

# Azure OpenAI 리소스 삭제 (생성한 경우)
az cognitiveservices account delete \
  --name workshop-openai \
  --resource-group $RESOURCE_GROUP
```

---

## AI Agent 아키텍처 요약

```
┌─────────────────────────────────────────────────┐
│                AKS Cluster (pets)                │
│                                                  │
│   ┌──────────┐    Tool     ┌────────────────┐   │
│   │ ai-agent │────────────▶│ product-service│   │
│   │ (Python) │             │   (Rust)       │   │
│   └────┬─────┘             └────────────────┘   │
│        │ LLM                                    │
└────────┼────────────────────────────────────────┘
         │
         ▼
  ┌──────────────┐
  │ Azure OpenAI │
  │   (GPT-4o)   │
  └──────────────┘
```

| 구성 요소 | 역할 |
|-----------|------|
| **AI Agent** | 요청 수신 → 상품 조회 → LLM 호출 → 추천 응답 |
| **product-service** | 상품 카탈로그 제공 (Tool) |
| **Azure OpenAI** | 자연어 이해 + 추천 생성 (Reasoning) |
| **DEMO_MODE** | Azure OpenAI 없이 규칙 기반 폴백 |

## 점검 체크리스트

- [ ] `kubectl get pods -n pets -l app=ai-agent` — Pod 1/1 Running
- [ ] `/health` 응답에 `"ready": true` 포함
- [ ] `POST /recommend` — 한국어 추천 결과 반환
- [ ] (데모 모드) `"mode": "demo"` 확인

---

| | |
|:---|---:|
| [⬅️ 08. 정리](08-cleanup.md) | [00. 워크샵 개요 🏠](00-overview.md) |
