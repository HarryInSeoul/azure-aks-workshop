# 04. 펫 스토어 배포

## 4-1. 전체 스택 배포

모든 서비스를 한 번에 배포합니다.

```bash
kubectl apply -f workshop-manifests/aks-store-all-in-one-ko.yaml
```

### 생성되는 리소스

| 리소스 | 이름 | 네임스페이스 | 비고 |
|--------|------|-------------|------|
| Namespace | `pets` | — | 모든 리소스의 네임스페이스 |
| StatefulSet | `mongodb` | pets | 주문 DB (MongoDB 4.2) |
| StatefulSet | `rabbitmq` | pets | 메시지 큐 (RabbitMQ 3.13) |
| Deployment | `order-service` | pets | 주문 접수 API |
| Deployment | `makeline-service` | pets | 주문 처리 워커 |
| Deployment | `product-service` | pets | 상품 카탈로그 API |
| Deployment | `store-front` | pets | 고객 웹 UI (replicas: 2) |
| Deployment | `store-admin` | pets | 관리자 UI |
| Deployment | `virtual-customer` | pets | 부하 생성기 |
| Deployment | `virtual-worker` | pets | 자동 주문 처리 |
| Service | `store-front` | pets | **LoadBalancer** (포트 80) |
| Service | `store-admin` | pets | **LoadBalancer** (포트 80) |
| Service | 나머지 | pets | ClusterIP (내부 전용) |

## 4-2. 배포 상태 확인

```bash
# Pod 상태 확인 (모두 Running / 1/1 Ready 확인)
kubectl get pods -n pets -w
```

> ⏱ 모든 Pod가 Ready가 되기까지 약 2~3분 소요됩니다.  
> MongoDB가 먼저 Ready가 되어야 makeline-service가 정상 기동합니다.

### 예상 출력

```
NAME                                READY   STATUS    RESTARTS   AGE
makeline-service-xxx                1/1     Running   0          2m
mongodb-0                           1/1     Running   0          2m
order-service-xxx                   1/1     Running   0          2m
product-service-xxx                 1/1     Running   0          2m
rabbitmq-0                          1/1     Running   0          2m
store-admin-xxx                     1/1     Running   0          2m
store-front-xxx                     1/1     Running   0          2m
store-front-xxx                     1/1     Running   0          2m
virtual-customer-xxx                1/1     Running   0          2m
virtual-worker-xxx                  1/1     Running   0          2m
```

## 4-3. 외부 접속 확인

```bash
kubectl get svc -n pets
```

```
NAME               TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)
store-front        LoadBalancer   10.0.x.x       <EXTERNAL-IP>    80:xxxxx/TCP
store-admin        LoadBalancer   10.0.x.x       <EXTERNAL-IP>    80:xxxxx/TCP
```

### 브라우저 접속

1. **고객 스토어**: `http://<store-front EXTERNAL-IP>`
   - 제목: "Contoso 펫 스토어"
   - 상품 목록이 한국어로 표시 (예: "짭짤한 선원의 삑삑 오징어")

2. **관리자 대시보드**: `http://<store-admin EXTERNAL-IP>`
   - 주문 목록 확인 (virtual-customer가 자동 주문 생성 중)

### CLI로 한국어 상품 확인

```bash
STORE_IP=$(kubectl get svc store-front -n pets -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -s http://$STORE_IP/api/products | python3 -c "
import sys, json
for p in json.load(sys.stdin):
    print(f\"{p['id']}. {p['name']} — ₩{p['price']}\")
"
```

### 예상 출력

```
1. 콘토소 캣닢 친구 — ₩9.99
2. 짭짤한 선원의 삑삑 오징어 — ₩6.99
3. 인어공주 쥐돌이 3형제 — ₩12.99
4. 바다 탐험가 퍼즐볼 — ₩10.99
5. 해적 앵무새 낚싯대 — ₩8.99
...
```

## 트러블슈팅

### MongoDB가 CrashLoop 또는 Readiness 실패

MongoDB는 저사양에서 초기 기동이 느릴 수 있습니다. 매니페스트에서 리소스를 충분히 설정했는지 확인하세요.

```yaml
resources:
  requests:
    cpu: 50m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 1024Mi
```

### makeline-service CrashLoopBackOff

MongoDB가 아직 Ready가 아니면 발생합니다. MongoDB가 Ready가 된 뒤 자동 복구되거나, 수동으로 재시작합니다.

```bash
kubectl rollout restart deployment/makeline-service -n pets
```

### ImagePullBackOff

ACR 연결이 안 된 경우입니다.

```bash
az aks update --name $CLUSTER_NAME -g $RESOURCE_GROUP --attach-acr $ACR_NAME
```

## 점검 체크리스트

- [ ] `kubectl get pods -n pets` — 모든 Pod 1/1 Running
- [ ] 브라우저에서 store-front 한국어 UI 확인
- [ ] 상품 목록이 한국어로 표시됨

---

| | |
|:---|---:|
| [⬅️ 03. 빌드 & 푸시](03-build-and-push.md) | [05. HPA 오토스케일링 ➡️](05-hpa-autoscaling.md) |
