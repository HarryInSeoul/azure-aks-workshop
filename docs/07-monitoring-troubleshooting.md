# 07. 모니터링 & 트러블슈팅

## 7-1. 클러스터 리소스 모니터링

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

## 7-2. 일반적인 트러블슈팅 시나리오

### 시나리오 1: Pod가 Pending 상태

**원인**: 노드에 CPU/메모리 여유가 없음

```bash
# Pending Pod 확인
kubectl get pods -n pets --field-selector=status.phase=Pending

# 이벤트에서 원인 확인
kubectl describe pod <POD_NAME> -n pets | grep -A5 Events

# NAP이 활성화되어 있으면 자동으로 노드 추가됨
kubectl get nodeclaims.karpenter.sh -w
```

### 시나리오 2: ImagePullBackOff

**원인**: ACR 인증 실패 또는 이미지 미존재

```bash
# Pod 이벤트 확인
kubectl describe pod <POD_NAME> -n pets | grep -A3 "Failed"

# ACR 이미지 확인
az acr repository list --name $ACR_NAME -o table
az acr repository show-tags --name $ACR_NAME --repository store-front -o table

# ACR 연결 재확인
az aks update --name $CLUSTER_NAME -g $RESOURCE_GROUP --attach-acr $ACR_NAME
```

### 시나리오 3: makeline-service CrashLoopBackOff

**원인**: MongoDB가 아직 Ready가 아님

```bash
# MongoDB 상태 확인
kubectl get pod mongodb-0 -n pets
kubectl logs mongodb-0 -n pets --tail=20

# makeline-service 로그 확인
kubectl logs -l app=makeline-service -n pets --tail=20

# MongoDB Ready 확인 후 재시작
kubectl rollout restart deployment/makeline-service -n pets
```

### 시나리오 4: HPA가 스케일링하지 않음

**원인**: metrics-server가 아직 값을 수집하지 못함

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

## 7-3. 유용한 디버깅 명령어 모음

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

## 7-4. Karpenter/NAP 관련 디버깅

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

## 7-5. Azure Portal에서 확인

1. **AKS > 워크로드**: 배포/Pod/ReplicaSet 상태
2. **AKS > 서비스 및 수신**: LoadBalancer IP 확인
3. **AKS > 노드 풀**: 시스템 노드풀 + NAP 노드 확인
4. **ACR > 리포지터리**: 이미지 태그/크기 확인

## 점검 체크리스트

- [ ] `kubectl top nodes` — 노드 리소스 사용량 확인
- [ ] `kubectl top pods -n pets` — Pod 리소스 사용량 확인
- [ ] 트러블슈팅 시나리오 1~2개 직접 재현해보기

---

| | |
|:---|---:|
| [⬅️ 06. NAP 노드 확장](06-nap-node-scaling.md) | [08. 정리 ➡️](08-cleanup.md) |
