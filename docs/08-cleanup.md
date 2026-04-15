# 08. 정리 (리소스 삭제)

## 8-1. Kubernetes 리소스 삭제

배포된 애플리케이션을 먼저 정리합니다.

```bash
# pets 네임스페이스 전체 삭제
kubectl delete namespace pets

# 커스텀 NodePool 삭제
kubectl delete nodepool workshop-linux
```

확인:
```bash
kubectl get all -n pets
kubectl get nodepools.karpenter.sh
```

## 8-2. 워크샵 리소스 그룹 삭제

리소스 그룹을 삭제하면 AKS 클러스터를 포함한 **워크샵에서 생성한 모든 리소스**가 한 번에 정리됩니다.

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

> ⚠️ `WorkshopDemo-RG` 삭제 시 AKS 클러스터, 노드 VMSS, LoadBalancer, Public IP, NSG, VNET 등이 모두 제거됩니다.  
> ✅ ACR (`WorkshopACR-RG`)은 **삭제하지 않습니다** — 이미지가 보존되어 다음 워크샵에서 재사용할 수 있습니다.

## 8-3. kubeconfig 정리

```bash
kubectl config delete-context $CLUSTER_NAME
kubectl config delete-cluster $CLUSTER_NAME
```

## 8-4. 삭제 확인

```bash
az group show --name $RESOURCE_GROUP 2>/dev/null && echo "아직 삭제 중..." || echo "✅ 삭제 완료"
```

## 삭제 체크리스트

- [ ] pets 네임스페이스 삭제됨
- [ ] `WorkshopDemo-RG` 리소스 그룹 삭제 → AKS + 모든 워크샵 리소스 정리
- [ ] kubeconfig에서 컨텍스트/클러스터 제거
- [ ] ACR (`WorkshopACR-RG`)은 유지 확인

---

## 수고하셨습니다! 🎉

이 워크샵에서 다룬 내용:

1. **AKS 클러스터 생성** — NAP, KEDA, Azure CNI Overlay + Cilium
2. **컨테이너 빌드 & ACR 푸시** — 7개 마이크로서비스, 한국어 로컬라이징
3. **애플리케이션 배포** — StatefulSet, Deployment, Service (LoadBalancer)
4. **HPA 오토스케일링** — CPU 기반 Pod 수평 확장/축소
5. **NAP 노드 자동 확장** — Karpenter 기반 노드 프로비저닝/통합
6. **모니터링 & 트러블슈팅** — kubectl 진단, 일반적인 문제 해결

---

| | |
|:---|---:|
| [⬅️ 07. 모니터링 & 트러블슈팅](07-monitoring-troubleshooting.md) | [00. 워크샵 개요 🏠](00-overview.md) |
