# 08. 모니터링 & 트러블슈팅

<details>
<summary><strong>⚠️ Cloud Shell 세션이 만료된 경우 — 환경 변수 재설정</strong></summary>

```bash
export RESOURCE_GROUP="WorkshopDemo-RG"
export CLUSTER_NAME="workshop-demo"
export LOCATION="koreacentral"
az aks get-credentials --name $CLUSTER_NAME --resource-group $RESOURCE_GROUP --overwrite-existing
```

</details>

## 목차

- [8-1. Prometheus & Grafana 구성](#8-1-azure-매니지드-prometheus--grafana-구성)
- [8-2. 클러스터 리소스 모니터링](#8-2-클러스터-리소스-모니터링)
- [8-3. 트러블슈팅 실습](#8-3-트러블슈팅-실습) — 직접 해보기
- [8-4. 추가 트러블슈팅 시나리오](#8-4-트러블슈팅-참고--추가-시나리오)
- [8-5. 디버깅 명령어 모음](#8-5-유용한-디버깅-명령어-모음)
- [8-6. Karpenter/NAP 디버깅](#8-6-karpenternap-관련-디버깅)
- [8-7. Azure Portal에서 확인](#8-7-azure-portal에서-확인)

---

운영 환경에서는 클러스터와 애플리케이션의 상태를 지속적으로 모니터링하고, 문제 발생 시 신속하게 진단할 수 있어야 합니다.  
이 섹션에서는 **Azure 매니지드 Prometheus**로 메트릭을 수집하고, **매니지드 Grafana**로 시각화한 뒤,
실제 운영에서 자주 발생하는 트러블슈팅 시나리오를 직접 해결해 봅니다.

### 이 섹션에서 배우는 것

- **Azure Monitor Workspace** — 매니지드 Prometheus 메트릭 저장소 구성
- **매니지드 Grafana** — 사전 구성된 Kubernetes 대시보드와 커스텀 PromQL 패널
- **트러블슈팅 5대 시나리오** — Pending, ImagePullBackOff, CrashLoopBackOff, HPA 미동작, LB Pending
- **디버깅 명령어** — Pod 로그, 셋 접속, DNS 확인, 네트워크 테스트

---

AKS 클러스터의 메트릭을 **Azure Monitor 매니지드 Prometheus**로 수집하고, **Azure 매니지드 Grafana**로 시각화합니다.

### Azure Monitor Workspace 생성

```bash
# Azure Monitor Workspace 생성 (Prometheus 메트릭 저장소)
az monitor account create \
  --name workshop-monitor \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  -o table
```

### Azure 매니지드 Grafana 인스턴스 생성

```bash
# 매니지드 Grafana 생성
az grafana create \
  --name workshop-grafana \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  -o table
```

> [!NOTE]
> ⏱ Grafana 인스턴스 생성에 약 3~5분 소요됩니다.

### AKS에 Prometheus 메트릭 수집 활성화

```bash
# Azure Monitor Workspace ID 조회
MONITOR_ID=$(az monitor account show \
  --name workshop-monitor \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# Grafana ID 조회
GRAFANA_ID=$(az grafana show \
  --name workshop-grafana \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# AKS에 Prometheus + Grafana 연결
az aks update \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable-azure-monitor-metrics \
  --azure-monitor-workspace-resource-id $MONITOR_ID \
  --grafana-resource-id $GRAFANA_ID
```

> [!NOTE]
> ⏱ 약 2~3분 소요됩니다.

### 활성화 확인

```bash
# Prometheus 에이전트 Pod 확인
kubectl get pods -n kube-system | grep ama-metrics

# ConfigMap 확인
kubectl get configmap -n kube-system ama-metrics-settings-configmap
```

### 예상 출력

```
ama-metrics-xxxx-xxxxx              2/2     Running   0   2m
ama-metrics-node-xxxxx              2/2     Running   0   2m
ama-metrics-node-xxxxx              2/2     Running   0   2m
```

### Grafana 대시보드 접속

```bash
# Grafana 엔드포인트 확인
GRAFANA_URL=$(az grafana show \
  --name workshop-grafana \
  --resource-group $RESOURCE_GROUP \
  --query "properties.endpoint" -o tsv)
echo "Grafana URL: $GRAFANA_URL"
```

브라우저에서 Grafana URL에 접속합니다. Azure AD 인증으로 자동 로그인됩니다.

### 기본 제공 대시보드 확인

Grafana에 접속한 후 다음 기본 대시보드를 확인합니다:

1. **Dashboards > Browse** 메뉴 이동
2. **Azure Monitor** 폴더에서 사전 구성된 대시보드 확인:
   - **Kubernetes / Compute Resources / Cluster** — 클러스터 전체 CPU/메모리
   - **Kubernetes / Compute Resources / Namespace (Pods)** — 네임스페이스별 Pod 리소스
   - **Kubernetes / Compute Resources / Node (Pods)** — 노드별 리소스 사용량
   - **Kubernetes / Networking / Cluster** — 네트워크 트래픽

> 📸 **스크린샷**: Azure 매니지드 Grafana 대시보드
>
> 📸 *스크린샷 준비 중 — `images/grafana-cluster-dashboard.png`*

> 📸 **스크린샷**: Grafana Pod 리소스 모니터링
>
> 📸 *스크린샷 준비 중 — `images/grafana-pod-resources.png`*

### 커스텀 대시보드: pets 네임스페이스 모니터링

PromQL 쿼리로 pets 네임스페이스의 워크로드를 모니터링하는 패널을 추가해봅니다.

**Grafana > New Dashboard > Add Visualization**:

| 패널 제목 | PromQL 쿼리 |
|-----------|-------------|
| Pod CPU 사용률 | `sum(rate(container_cpu_usage_seconds_total{namespace="pets"}[5m])) by (pod)` |
| Pod 메모리 사용량 | `sum(container_memory_working_set_bytes{namespace="pets"}) by (pod)` |
| HTTP 요청 수 | `sum(rate(http_requests_total{namespace="pets"}[5m])) by (service)` |
| Pod 재시작 횟수 | `sum(kube_pod_container_status_restarts_total{namespace="pets"}) by (pod)` |

> 📸 **스크린샷**: Grafana 커스텀 대시보드 예시 (PromQL 패널)
>
> 📸 *스크린샷 준비 중 — `images/grafana-custom-dashboard.png`*

> [!TIP]
> Grafana에서 **Explore** 메뉴를 사용하면 PromQL 쿼리를 대화형으로 테스트할 수 있습니다.

### Prometheus Alert Rules 설정 (선택)

```bash
# Prometheus 알림 규칙 그룹 생성 예시
az monitor account alert-rule create \
  --account-name workshop-monitor \
  --resource-group $RESOURCE_GROUP \
  --rule-group-name workshop-alerts \
  --rules '[
    {
      "alert": "HighPodCPU",
      "expression": "sum(rate(container_cpu_usage_seconds_total{namespace=\"pets\"}[5m])) by (pod) > 0.8",
      "for": "PT5M",
      "severity": 3,
      "labels": {"team": "workshop"},
      "annotations": {"summary": "Pod CPU usage is above 80%"}
    }
  ]' 2>/dev/null || echo "💡 Alert Rules는 Azure Portal > Monitor > Alerts에서도 구성할 수 있습니다."
```

---

## 8-2. 클러스터 리소스 모니터링

### 노드 리소스 현황

```bash
kubectl top nodes
```

```
NAME                                CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
aks-nodepool1-xxxxx-vmss000000      245m         12%    1024Mi          14%
aks-nodepool1-xxxxx-vmss000001      180m         9%     890Mi           12%
```

### Pod 리소스 현황

```bash
kubectl top pods -n pets --sort-by=cpu
```

### 전체 서비스 상태 요약

```bash
kubectl get all -n pets
```

## 8-3. 트러블슈팅 실습

실제 운영에서 자주 발생하는 오류 상황을 **직접 만들고 해결**해 봅니다.

### 실습 A: CrashLoopBackOff 재현 & 해결

order-service Pod를 강제로 삭제하여 CrashLoopBackOff 상황을 관찰합니다.

```bash
# 1. 현재 정상 상태 확인
kubectl get pods -n pets -l app=order-service

# 2. Pod 강제 삭제 (Deployment가 자동 재생성)
kubectl delete pod -n pets -l app=order-service

# 3. Pod가 재시작되는 과정 관찰
kubectl get pods -n pets -l app=order-service -w
```

> [!NOTE]
> Deployment가 자동으로 새 Pod를 생성합니다. 이것이 Kubernetes의 **자가 치유(self-healing)** 기능입니다.

### 실습 B: Pending Pod 재현 & NAP 관찰

리소스 요청을 극단적으로 높여 Pending 상태를 만들고, NAP이 노드를 추가하는 과정을 확인합니다.

```bash
# 1. virtual-customer의 리소스 요청을 크게 설정 → Pending 발생
kubectl set resources deployment/virtual-customer -n pets \
  --requests=cpu=4,memory=8Gi

# 2. Pending 상태 확인
kubectl get pods -n pets -l app=virtual-customer

# 3. 이벤트에서 원인 확인
kubectl describe pod -n pets -l app=virtual-customer | grep -A5 Events

# 4. NAP이 노드를 추가하는 과정 관찰
kubectl get nodeclaims.karpenter.sh -w
```

```bash
# 5. 실습 후 원래 값으로 복구
kubectl set resources deployment/virtual-customer -n pets \
  --requests=cpu=1m,memory=1Mi
```

### 실습 C: ImagePullBackOff 재현 & 해결

존재하지 않는 이미지를 설정하여 ImagePullBackOff를 직접 체험합니다.

```bash
# 1. 존재하지 않는 이미지로 변경
kubectl set image deployment/virtual-worker -n pets \
  virtual-worker=aksworkshopkoea6e.azurecr.io/virtual-worker:nonexistent

# 2. ImagePullBackOff 확인
kubectl get pods -n pets -l app=virtual-worker -w

# 3. 이벤트에서 원인 확인
kubectl describe pod -n pets -l app=virtual-worker | grep -A3 "Failed"
```

```bash
# 4. 올바른 이미지로 복구
kubectl set image deployment/virtual-worker -n pets \
  virtual-worker=aksworkshopkoea6e.azurecr.io/virtual-worker:ko
```

### 실습 결과 정리

| 시나리오 | 증상 | 원인 | 해결 방법 |
|----------|------|------|-----------|
| **CrashLoopBackOff** | Pod 재시작 반복 | 앱 에러, 의존성 미준비 | 로그 확인 → 원인 해결 → rollout restart |
| **Pending** | Pod 스케줄링 안 됨 | 노드 리소스 부족 | NAP 자동 해결 또는 리소스 조정 |
| **ImagePullBackOff** | 이미지 풀 실패 | 잘못된 태그, ACR 인증 | 이미지 태그 확인 → ACR 연결 |

---

## 8-4. 트러블슈팅 참고 — 추가 시나리오

### HPA가 스케일링하지 않음

```bash
# HPA 상태 확인
kubectl describe hpa -n pets

# targets가 <unknown>/60% 이면 metrics-server 대기
kubectl top pods -n pets

# metrics-server Pod 확인
kubectl get pods -n kube-system -l k8s-app=metrics-server
```

### 시나리오 5: LoadBalancer EXTERNAL-IP가 `<pending>`

**원인**: Azure Load Balancer 프로비저닝 중 (보통 1~2분)

```bash
kubectl get svc -n pets -w
```

## 8-5. 유용한 디버깅 명령어 모음

```bash
# Pod 로그 (실시간)
kubectl logs -f <POD_NAME> -n pets

# 이전 크래시된 컨테이너 로그
kubectl logs <POD_NAME> -n pets --previous

# Pod 셸 접속
kubectl exec -it <POD_NAME> -n pets -- /bin/sh

# 서비스 엔드포인트 확인
kubectl get endpoints -n pets

# DNS 확인 (Pod 내부에서)
kubectl run -it --rm dns-test --image=busybox:1.37 --restart=Never -- nslookup mongodb.pets.svc.cluster.local

# 네트워크 연결 테스트
kubectl run -it --rm net-test --image=busybox:1.37 --restart=Never -- wget -qO- http://product-service.pets:3002/health
```

## 8-6. Karpenter/NAP 관련 디버깅

```bash
# NodePool 상태 및 제한 확인
kubectl describe nodepool workshop-linux

# NodeClaim 상태 (노드 프로비저닝 요청)
kubectl get nodeclaims.karpenter.sh -o wide

# 노드에 부여된 Karpenter 라벨/어노테이션
kubectl get nodes -o custom-columns=NAME:.metadata.name,SKU:.metadata.labels.karpenter\\.azure\\.com/sku-name,NODEPOOL:.metadata.labels.karpenter\\.sh/nodepool

# AKS NodeClass 확인
kubectl describe aksnodeclasses.karpenter.azure.com default
```

## 8-7. Azure Portal에서 확인

1. **AKS > 워크로드**: 배포/Pod/ReplicaSet 상태
2. **AKS > 서비스 및 수신**: LoadBalancer IP 확인
3. **AKS > 노드 풀**: 시스템 노드풀 + NAP 노드 확인
4. **ACR > 리포지터리**: 이미지 태그/크기 확인
5. **Azure Monitor > Metrics**: Prometheus 메트릭 쿼리
6. **Azure 매니지드 Grafana**: 대시보드에서 클러스터/Pod 메트릭 시각화

## 점검 체크리스트

- [ ] `kubectl get pods -n kube-system | grep ama-metrics` — Prometheus 에이전트 Running
- [ ] Grafana URL 접속 — 기본 Kubernetes 대시보드 확인
- [ ] `kubectl top nodes` — 노드 리소스 사용량 확인
- [ ] `kubectl top pods -n pets` — Pod 리소스 사용량 확인
- [ ] 트러블슈팅 시나리오 1~2개 직접 재현해보기

---

| | |
|:---|---:|
| [⬅️ 08. NAP 노드 확장](08-nap-node-scaling.md) | [10. GitOps ➡️](10-gitops-flux.md) |
