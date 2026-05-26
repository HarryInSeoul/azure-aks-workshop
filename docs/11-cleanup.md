# 11. 정리 (리소스 삭제)

워크샵이 종료되면 불필요한 비용 발생을 막기 위해 생성한 리소스를 정리해야 합니다.  
`WorkshopDemo-RG` 리소스 그룹을 삭제하면 AKS 클러스터, 노드, 네트워크, 개인 ACR 등 워크샵에서 생성한 **모든 리소스가 한 번에 정리**됩니다.

### 정리 순서

1. Kubernetes 리소스 삭제 (pets 네임스페이스, NodePool, Flux)
2. 리소스 그룹 삭제 (WorkshopDemo-RG)
3. kubeconfig 정리

## 11-1. Kubernetes 리소스 삭제

배포된 애플리케이션을 먼저 정리합니다.

```bash
# pets 네임스페이스 전체 삭제
kubectl delete namespace pets

# 커스텀 NodePool 삭제
kubectl delete nodepool workshop-linux

# GitOps Flux 구성 삭제 (10절 진행 시)
az k8s-configuration flux delete \
  --name workshop-gitops \
  --cluster-name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --cluster-type managedClusters \
  --yes 2>/dev/null || true
```

확인:
```bash
kubectl get all -n pets
kubectl get nodepools.karpenter.sh
```

## 11-2. 워크샵 리소스 그룹 삭제

리소스 그룹을 삭제하면 AKS 클러스터를 포함한 **워크샵에서 생성한 모든 리소스**가 한 번에 정리됩니다.

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

> [!WARNING]
> `WorkshopDemo-RG` 삭제 시 AKS 클러스터, 노드 VMSS, LoadBalancer, Public IP, NSG, VNET 등이 모두 제거됩니다.  
> ✅ ACR은 워크샵 주최자가 관리하는 공용 리소스이므로 참가자가 삭제할 필요가 없습니다.

## 11-3. kubeconfig 정리

```bash
kubectl config delete-context $CLUSTER_NAME
kubectl config delete-cluster $CLUSTER_NAME
```

## 11-4. 삭제 확인

```bash
az group show --name $RESOURCE_GROUP 2>/dev/null && echo "아직 삭제 중..." || echo "✅ 삭제 완료"
```

## 삭제 체크리스트

- [ ] pets 네임스페이스 삭제됨
- [ ] GitOps Flux 구성 삭제됨 (10절 진행 시)
- [ ] `WorkshopDemo-RG` 리소스 그룹 삭제 → AKS + Prometheus/Grafana + 모든 워크샵 리소스 정리
- [ ] kubeconfig에서 컨텍스트/클러스터 제거
- [ ] (Terraform 사용 시) `terraform destroy` 실행 또는 리소스 그룹 삭제로 대체

---

## 수고하셨습니다! 🎉

이 워크샵에서 다룬 내용:

1. **AKS 클러스터 생성** — NAP, KEDA, Azure CNI Overlay (CLI / Terraform)
2. **컨테이너 빌드 & ACR 푸시** — store-admin 커스터마이징
3. **애플리케이션 배포** — StatefulSet, Deployment, Service, Ingress
4. **AI Agent 배포** — Azure OpenAI 활용 AI 상품 추천 에이전트
5. **HPA 오토스케일링** — CPU 기반 Pod 수평 확장/축소
6. **NAP 노드 자동 확장** — Karpenter 기반 노드 프로비저닝/통합
7. **모니터링** — 매니지드 Prometheus + Grafana, 트러블슈팅
8. **GitOps** — Flux v2 기반 선언적 배포 자동화 & 드리프트 복구

---

| | |
|:---|---:|
| [⬅️ 10. GitOps](10-gitops-flux.md) | [00. 워크샵 개요 🏠](00-overview.md) |
