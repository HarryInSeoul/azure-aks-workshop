# 05. HPA 오토스케일링

## 개요

Horizontal Pod Autoscaler(HPA)는 CPU/메모리 사용률에 따라 Pod 수를 자동으로 조절합니다.  
이 섹션에서는 `store-front`와 `order-service`에 HPA를 적용하고, virtual-customer가 생성하는 부하에 따라 스케일링되는 과정을 관찰합니다.

## 5-1. HPA 배포

```bash
kubectl apply -f workshop-manifests/55-hpa-store.yaml
```

### HPA 설정 요약

| 대상 | 최소 | 최대 | CPU 임계치 |
|------|------|------|-----------|
| store-front | 2 | 10 | 60% |
| order-service | 1 | 8 | 60% |

## 5-2. HPA 상태 관찰

```bash
# HPA 현황 (TARGETS 컬럼에 현재 CPU% / 목표% 표시)
kubectl get hpa -n pets -w
```

### 예상 출력

```
NAME                REFERENCE                  TARGETS        MINPODS   MAXPODS   REPLICAS
store-front-hpa     Deployment/store-front     cpu: 85%/60%   2         10        5
order-service-hpa   Deployment/order-service   cpu: 120%/60%  1         8         4
```

> virtual-customer가 시간당 100건의 주문을 생성하므로, 배포 후 수 분 이내에 HPA가 스케일 아웃을 시작합니다.

## 5-3. 실시간 모니터링

### Pod 리소스 사용량

```bash
kubectl top pods -n pets
```

### Pod 수 변화 관찰

```bash
# 별도 터미널에서 실행
kubectl get pods -n pets -w
```

### Deployment 레플리카 변화

```bash
kubectl get deploy -n pets -w
```

## 5-4. 부하 조절 실험

### 부하 증가 — virtual-customer 주문 빈도 올리기

```bash
kubectl set env deployment/virtual-customer -n pets ORDERS_PER_HOUR=500
```

잠시 후 HPA가 더 많은 Pod를 추가하는 것을 관찰하세요.

### 부하 감소 — 주문 빈도 낮추기

```bash
kubectl set env deployment/virtual-customer -n pets ORDERS_PER_HOUR=10
```

약 5분 뒤 HPA가 스케일 다운을 시작합니다 (기본 쿨다운: 5분).

### 부하 중지 — virtual-customer 일시 중지

```bash
kubectl scale deployment/virtual-customer -n pets --replicas=0
```

## 5-5. HPA 상세 확인

```bash
kubectl describe hpa store-front-hpa -n pets
kubectl describe hpa order-service-hpa -n pets
```

주요 확인 포인트:
- `AbleToScale` 조건
- `ScalingActive` 조건
- 최근 스케일링 이벤트

## 핵심 개념 정리

```
트래픽 증가
    │
    ▼
CPU 사용률 상승 (> 60%)
    │
    ▼
HPA가 Deployment replica 수 증가
    │
    ▼
새 Pod 스케줄링 → 기존 노드에 배치
    │
    ▼
노드 리소스 부족 시 → Pending Pod 발생
    │
    ▼
NAP(Karpenter)가 노드 자동 추가  ← 다음 섹션에서 실습
```

## 점검 체크리스트

- [ ] `kubectl get hpa -n pets` — 두 HPA 모두 TARGETS 표시
- [ ] ORDERS_PER_HOUR=500 시 replica 수 증가 확인
- [ ] ORDERS_PER_HOUR=10 시 약 5분 뒤 스케일 다운 확인

---

| | |
|:---|---:|
| [⬅️ 04. 앱 배포](04-deploy-app.md) | [06. NAP 노드 확장 ➡️](06-nap-node-scaling.md) |
