# AKS 펫 스토어 워크샵

Azure Kubernetes Service(AKS) 핸즈온 워크샵 — 한국어 로컬라이징된 마이크로서비스 펫 스토어 애플리케이션을 활용합니다.

## 워크샵 가이드

| # | 섹션 | 설명 |
|---|------|------|
| 00 | [개요](docs/00-overview.md) | 아키텍처, 서비스 구성, 학습 목표 |
| 01 | [사전 준비](docs/01-prerequisites.md) | Azure CLI, ACR 생성, 환경 변수 |
| 02 | [클러스터 생성](docs/02-create-cluster.md) | AKS + NAP + KEDA + Azure CNI Overlay |
| 03 | [빌드 & 푸시](docs/03-build-and-push.md) | Docker 빌드, ACR 푸시, 로컬 테스트 |
| 04 | [앱 배포](docs/04-deploy-app.md) | K8s 매니페스트 배포, Ingress / AGC 설정 |
| 05 | [HPA 오토스케일링](docs/05-hpa-autoscaling.md) | CPU 기반 Pod 수평 확장 |
| 06 | [NAP 노드 확장](docs/06-nap-node-scaling.md) | Karpenter 기반 노드 자동 프로비저닝 |
| 07 | [모니터링 & 트러블슈팅](docs/07-monitoring-troubleshooting.md) | 진단 명령어, 문제 해결 |
| 08 | [정리](docs/08-cleanup.md) | 리소스 삭제 |

## 프로젝트 구조

```
AKS-Workshop/
├── README.md                          # 이 파일
├── docs/                              # 워크샵 가이드 (섹션별)
│   ├── 00-overview.md
│   ├── 01-prerequisites.md
│   ├── 02-create-cluster.md
│   ├── 03-build-and-push.md
│   ├── 04-deploy-app.md
│   ├── 05-hpa-autoscaling.md
│   ├── 06-nap-node-scaling.md
│   ├── 07-monitoring-troubleshooting.md
│   ├── 08-cleanup.md
│   ├── architecture.drawio             # draw.io 아키텍처 다이어그램
│   └── images/
│       └── architecture.png            # 아키텍처 이미지
├── aks-store-demo-ko/                 # 한국어 로컬라이징 소스
│   ├── src/
│   │   ├── store-front/               # Vue.js — 고객 UI (한국어)
│   │   ├── store-admin/               # Vue.js — 관리자 UI
│   │   ├── product-service/           # Rust — 상품 API (한국어 데이터)
│   │   ├── order-service/             # Node.js — 주문 API
│   │   ├── order-service-dotnet/       # .NET 8 — 주문 API (Windows 컨테이너)
│   │   ├── makeline-service/          # Go — 주문 처리
│   │   ├── virtual-customer/          # Rust — 부하 생성
│   │   └── virtual-worker/            # Rust — 자동 처리
│   ├── docker-compose.yml
│   └── docker-compose-local.yml
└── workshop-manifests/                # Kubernetes 매니페스트
    ├── aks-store-all-in-one-ko.yaml   # 전체 스택 배포
    ├── 55-hpa-store.yaml              # HPA 설정
    ├── 60-ingress.yaml                # Ingress (Web App Routing)
    ├── 61-agc-gateway.yaml            # Gateway API (AGC)
    ├── 65-order-service-dotnet-windows.yaml  # .NET order-service (Windows 노드풀)
    └── 70-nap-nodepool.yaml           # NAP NodePool
```

## 기술 스택

- **AKS**: NAP (Karpenter), KEDA, Azure CNI Overlay (선택: Cilium)
- **Ingress**: Web App Routing (관리형 NGINX) / AGC (Application Gateway for Containers)
- **프론트엔드**: Vue.js 3.5 + Vite + Nginx
- **백엔드**: Rust, Node.js/Fastify, Go, .NET 8/C# (Windows)
- **인프라**: MongoDB, RabbitMQ
- **컨테이너**: Azure Container Registry (사전 제공)
- **리전**: Korea Central

## 시작하기

```bash
# 1. 워크샵 가이드 시작
open docs/00-overview.md
```

## 참고

이 워크샵은 [Azure-Samples/aks-store-demo](https://github.com/Azure-Samples/aks-store-demo)를 기반으로 한국어 로컬라이징 및 워크샵 커리큘럼을 추가하여 작성되었습니다.
