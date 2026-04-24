# AKS 펫 스토어 워크샵

Azure Kubernetes Service(AKS) 핸즈온 워크샵 — 마이크로서비스 기반 펫 스토어 애플리케이션을 AKS에 배포하고, 오토스케일링과 노드 자동 프로비저닝(NAP)을 직접 체험합니다.

## 실습 환경

- **Azure Cloud Shell (Bash)** — 별도의 로컬 도구 설치 없이 브라우저에서 바로 실습
- 예상 소요 시간: **~120분**
- 예상 비용: **~$0.63 (≈ ₩870)** / 워크샵 1회 (2시간)

## 워크샵 가이드

| # | 섹션 | 설명 |
|---|------|------|
| 00 | [개요](docs/00-overview.md) | 아키텍처, 서비스 구성, 학습 목표 |
| 01 | [사전 준비](docs/01-prerequisites.md) | Cloud Shell, 구독 설정, ACR 생성 |
| 02 | [클러스터 생성](docs/02-create-cluster.md) | AKS + NAP + KEDA + Azure CNI Overlay |
| 03 | [빌드 & 푸시](docs/03-build-and-push.md) | 소스 클론, ACR Task로 이미지 빌드 |
| 04 | [앱 배포](docs/04-deploy-app.md) | K8s 매니페스트 배포, Ingress / AGC 설정 |
| 05 | [AI Agent 배포](docs/05-ai-agent.md) | Azure OpenAI + AI 상품 추천 에이전트 |
| 06 | [HPA 오토스케일링](docs/06-hpa-autoscaling.md) | CPU 기반 Pod 수평 확장 |
| 07 | [NAP 노드 확장](docs/07-nap-node-scaling.md) | Karpenter 기반 노드 자동 프로비저닝 |
| 08 | [모니터링 & 트러블슈팅](docs/08-monitoring-troubleshooting.md) | 진단 명령어, 문제 해결 |
| 09 | [정리](docs/09-cleanup.md) | 리소스 삭제 |

## 프로젝트 구조

```
azure-aks-workshop/
├── README.md
├── docs/                              # 워크샵 가이드 (섹션별)
│   ├── 00-overview.md ~ 09-cleanup.md
│   ├── architecture.drawio            # draw.io 아키텍처 다이어그램
│   └── images/                        # 스크린샷 및 다이어그램
├── aks-store-demo-ko/                 # 애플리케이션 소스
│   └── src/
│       ├── store-front/               # Vue.js 3 — 고객 웹 UI
│       ├── store-admin/               # Vue.js 3 — 관리자 대시보드
│       ├── ai-agent/                  # Python / FastAPI — AI 상품 추천
│       ├── product-service/           # Rust — 상품 카탈로그 API
│       ├── order-service/             # Node.js / Fastify — 주문 처리
│       ├── order-service-dotnet/      # .NET 8 — 주문 API (Windows 컨테이너)
│       ├── makeline-service/          # Go — 큐 소비 & DB 저장
│       ├── virtual-customer/          # Rust — 부하 생성기
│       └── virtual-worker/            # Rust — 자동 주문 처리기
└── workshop-manifests/                # Kubernetes 매니페스트
    ├── aks-store-all-in-one-ko.yaml   # 전체 스택 배포
    ├── 55-hpa-store.yaml              # HPA 설정
    ├── 60-ingress.yaml                # Ingress (Web App Routing)
    ├── 61-agc-gateway.yaml            # Gateway API (AGC)
    ├── 65-order-service-dotnet-windows.yaml  # .NET order-service (Windows)
    ├── 70-nap-nodepool.yaml           # NAP NodePool
    └── 90-ai-agent.yaml               # AI Agent (Azure OpenAI)
```

## 기술 스택

| 영역 | 기술 |
|------|------|
| **오케스트레이션** | AKS — NAP (Karpenter), KEDA, Azure CNI Overlay |
| **Ingress** | Web App Routing (관리형 NGINX) / AGC (Application Gateway for Containers) |
| **프론트엔드** | Vue.js 3 + Vite + Nginx |
| **백엔드** | Rust, Node.js/Fastify, Go, Python/FastAPI, .NET 8 |
| **AI** | Azure OpenAI (GPT-4o) |
| **인프라** | MongoDB, RabbitMQ |
| **컨테이너** | Azure Container Registry (공용 + 개인) |
| **리전** | Korea Central |

## 시작하기

1. [Azure Portal](https://portal.azure.com)에서 Cloud Shell을 엽니다.
2. [00. 워크샵 개요](docs/00-overview.md)부터 순서대로 진행합니다.

## 참고

이 워크샵은 [Azure-Samples/aks-store-demo](https://github.com/Azure-Samples/aks-store-demo)를 기반으로 워크샵 커리큘럼을 추가하여 작성되었습니다.
