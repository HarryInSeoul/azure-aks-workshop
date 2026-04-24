# 00. 워크샵 개요

## 목표

이 워크샵은 **AKS(Azure Kubernetes Service)** 위에 마이크로서비스 기반 펫 스토어 애플리케이션을 배포하고, 오토스케일링과 노드 자동 프로비저닝(NAP)을 직접 체험하는 핸즈온 과정입니다.

## 학습 내용

| 섹션 | 주제 | 예상 시간 |
|------|------|-----------|
| 01 | 사전 준비 — 구독, CLI, ACR | 10분 |
| 02 | AKS 클러스터 생성 (NAP + KEDA + Azure CNI Overlay) | 15분 |
| 03 | 애플리케이션 빌드 & ACR 푸시 | 15분 |
| 04 | 펫 스토어 배포 + Ingress 설정 | 15분 |
| 05 | HPA 오토스케일링 관찰 | 15분 |
| 06 | NAP(Karpenter) 노드 자동 확장 | 15분 |
| 07 | 모니터링 & 트러블슈팅 | 15분 |
| 08 | AI Agent 배포 (Azure OpenAI) | 15분 |
| 09 | 정리 (리소스 삭제) | 5분 |
| **합계** | | **~120분** |

## 아키텍처

![AKS 펫 스토어 아키텍처](images/architecture.png)

> 💡 [draw.io 원본 파일](architecture.drawio)을 열면 다이어그램을 직접 편집할 수 있습니다.

### 서비스 구성

| 서비스 | 언어 | 역할 |
|--------|------|------|
| **store-front** | Vue.js 3 + Nginx | 고객용 웹 프론트엔드 (한국어 UI) |
| **store-admin** | Vue.js 3 + Nginx | 관리자 대시보드 |
| **product-service** | Rust | 상품 카탈로그 API (한국어 상품 데이터) |
| **order-service** | Node.js / Fastify | 주문 접수 → RabbitMQ 큐 전달 |
| **makeline-service** | Go | 큐에서 주문 처리 → MongoDB 저장 |
| **MongoDB** | — | 주문 데이터 저장소 |
| **RabbitMQ** | — | 메시지 큐 |
| **virtual-customer** | Rust | 부하 생성 (자동 주문) |
| **virtual-worker** | Rust | 자동 주문 처리 |

### 클러스터 구성

| 항목 | 설정 |
|------|------|
| VM SKU | Standard_D2s_v3 (2 vCPU, 8 GiB) |
| 초기 노드 수 | 2 |
| 네트워크 | Azure CNI Overlay |
| 노드 오토스케일링 | NAP (Node Auto Provisioning / Karpenter) |
| 이벤트 기반 스케일링 | KEDA |
| Ingress 컨트롤러 | Web App Routing (관리형 NGINX Ingress) |
| 컨테이너 레지스트리 | Azure Container Registry (사전 제공) |

### 리소스 그룹 구성

| 리소스 그룹 | 포함 리소스 | 정리 정책 |
|-------------|-----------|-----------|
| `WorkshopDemo-RG` | AKS 클러스터, 노드 VMSS, LoadBalancer, Public IP 등 | 워크샵 종료 시 **삭제** |

> 워크샵 정리 시 `WorkshopDemo-RG`만 삭제하면 모든 워크샵 리소스가 한 번에 정리됩니다.  
> ACR은 워크샵 주최자가 사전 제공하는 공용 리소스이므로 참가자가 관리할 필요가 없습니다.

## 예상 비용

> 모든 비용은 Korea Central 리전, Linux, 종량제(Pay-As-You-Go) 기준 **추정치**입니다.  
> 실제 비용은 구독 유형, 예약 할인, 사용 패턴에 따라 달라질 수 있습니다.

### 워크샵 1회 실행 비용 (~2시간)

| 리소스 | 사양 | 시간당 비용 | 2시간 예상 |
|--------|------|-----------|-----------|
| AKS 컨트롤 플레인 | Free tier | $0 | $0 |
| 노드 VM × 2 | Standard_D2s_v3 (2 vCPU, 8 GiB) | ~$0.114 × 2 | ~$0.46 |
| NAP 자동 추가 노드 | Standard_D8als_v6 (일시적, ~15분) | ~$0.35 | ~$0.09 |
| Standard Load Balancer | 규칙 1개 (Ingress) | ~$0.025 | ~$0.05 |
| Public IP × 1 | Standard Static (Ingress) | ~$0.005 | ~$0.01 |
| OS 디스크 × 2 | 128GB (Ephemeral, 노드 포함) | — | $0 |
| **소계 (워크샵 1회)** | | | **~$0.61** |

### 상시 유지 비용

> ACR은 워크샵 주최자가 사전 제공하므로 참가자에게 추가 비용이 없습니다.

### 비용 요약

```
워크샵 1회 (2시간):  약 $0.61  (≈ ₩840)
```

> **💡 비용 절감 팁**
> - 워크샵 종료 후 반드시 `WorkshopDemo-RG`를 삭제하세요 (09-cleanup 참조)
> - NAP 노드는 부하 제거 시 자동으로 축소되므로 별도 조치 불필요

---

| | |
|:---|---:|
| | [01. 사전 준비 ➡️](01-prerequisites.md) |
