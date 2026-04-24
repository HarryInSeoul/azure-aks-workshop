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

> ⚠️ **보안 참고**: 이 매니페스트에는 RabbitMQ 기본 자격증명(`username`/`password`)이 포함되어 있습니다.
> 워크샵 데모 전용이며, **프로덕션 환경에서는 반드시 강력한 비밀번호로 변경**하고 Azure Key Vault 등과 연동하세요.

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
   - 상품 목록이 표시됨 (예: "짭짤한 선원의 샑샑 오징어")

2. **관리자 대시보드**: `http://<store-admin EXTERNAL-IP>`
   - 주문 목록 확인 (virtual-customer가 자동 주문 생성 중)

### CLI로 상품 확인

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

## 4-4. Ingress로 단일 IP 노출 (핸즈온)

현재 store-front과 store-admin이 각각 별도의 LoadBalancer IP를 가지고 있습니다.  
**Ingress**를 사용하면 하나의 IP로 경로 기반 라우팅이 가능합니다.

### LoadBalancer vs Ingress 비교

| 항목 | LoadBalancer (현재) | Ingress (이번 실습) |
|------|-------------------|-------------------|
| 외부 IP 수 | 서비스당 1개 (2개) | **1개로 통합** |
| 비용 | Public IP × 2 + LB 규칙 × 2 | Public IP × 1 + LB 규칙 × 1 |
| 경로 기반 라우팅 | ❌ | ✅ (path-based routing) |
| TLS 종료 | 각 서비스에서 처리 | Ingress에서 중앙 처리 |

### Step 1: Web App Routing 애드온 활성화

AKS의 관리형 NGINX Ingress 컨트롤러를 활성화합니다.

```bash
az aks approuting enable \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP
```

> ⏱ 약 1~2분 소요됩니다.

활성화 확인:

```bash
# Ingress 컨트롤러 Pod 확인
kubectl get pods -n app-routing-system

# IngressClass 확인
kubectl get ingressclass
```

### 예상 출력

```
NAME                                   READY   STATUS    RESTARTS   AGE
nginx-0                                1/1     Running   0          1m
```

```
NAME                                    CONTROLLER                            PARAMETERS   AGE
webapprouting.kubernetes.azure.com      k8s.io/ingress-nginx                  <none>       1m
```

### Step 2: Service 타입을 ClusterIP로 변경

Ingress가 트래픽을 라우팅하므로 store-front, store-admin의 Service를 ClusterIP로 변경합니다.

```bash
kubectl patch svc store-front -n pets -p '{"spec": {"type": "ClusterIP"}}'
kubectl patch svc store-admin -n pets -p '{"spec": {"type": "ClusterIP"}}'
```

변경 확인:

```bash
kubectl get svc -n pets store-front store-admin
```

```
NAME          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
store-front   ClusterIP   10.0.x.x       <none>        80/TCP    10m
store-admin   ClusterIP   10.0.x.x       <none>        80/TCP    10m
```

> 기존 LoadBalancer External IP는 더 이상 접근되지 않습니다.

### Step 3: Ingress 리소스 배포

```bash
kubectl apply -f workshop-manifests/60-ingress.yaml
```

매니페스트 내용 (`workshop-manifests/60-ingress.yaml`):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pets-ingress
  namespace: pets
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/use-regex: "true"
spec:
  ingressClassName: webapprouting.kubernetes.azure.com
  rules:
    - http:
        paths:
          - path: /admin(/|$)(.*)
            pathType: ImplementationSpecific
            backend:
              service:
                name: store-admin
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: store-front
                port:
                  number: 80
```

### Step 4: Ingress IP 확인 & 접속

```bash
# IP 할당 대기 (최대 2분)
kubectl get ingress -n pets -w
```

```
NAME           CLASS                                   HOSTS   ADDRESS          PORTS   AGE
pets-ingress   webapprouting.kubernetes.azure.com       *       <INGRESS-IP>    80      1m
```

```bash
INGRESS_IP=$(kubectl get ingress pets-ingress -n pets -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Ingress IP: $INGRESS_IP"
```

### 브라우저 접속

| URL | 서비스 | 설명 |
|-----|--------|------|
| `http://<INGRESS-IP>/` | store-front | 고객 펫 스토어 |
| `http://<INGRESS-IP>/admin` | store-admin | 관리자 대시보드 |

### CLI 검증

```bash
# 고객 스토어 — 상품 확인
curl -s http://$INGRESS_IP/api/products | python3 -c "
import sys, json
for p in json.load(sys.stdin):
    print(f\"{p['id']}. {p['name']} — ₩{p['price']}\")
"

# 관리자 대시보드 — 페이지 확인
curl -s -o /dev/null -w '%{http_code}' http://$INGRESS_IP/admin
# → 200
```

### (선택) 되돌리기 — LoadBalancer로 복원

Ingress 실습 후 원래 상태로 되돌리려면:

```bash
kubectl delete -f workshop-manifests/60-ingress.yaml
kubectl patch svc store-front -n pets -p '{"spec": {"type": "LoadBalancer"}}'
kubectl patch svc store-admin -n pets -p '{"spec": {"type": "LoadBalancer"}}'
```

> **💡 참고**: Ingress 매니페스트에서는 NGINX 컨트롤러에서 `/admin` 경로의 trailing slash를 올바르게 처리하기 위해
> 정규식(`/admin(/|$)(.*)`)을 사용합니다. 4-5절의 AGC Gateway API에서는 `PathPrefix: /admin`으로 동일한 동작을 달성합니다.
> 두 방식 모두 `/admin`, `/admin/`, `/admin/anything` 경로를 매칭합니다.

### Ingress 점검 체크리스트

- [ ] `kubectl get ingressclass` — `webapprouting.kubernetes.azure.com` 존재
- [ ] `kubectl get ingress -n pets` — ADDRESS에 IP 할당됨
- [ ] `http://<INGRESS-IP>/` — 고객 스토어 표시
- [ ] `http://<INGRESS-IP>/admin` — 관리자 대시보드 표시
- [ ] 기존 LoadBalancer IP 2개 → Ingress IP 1개로 통합 확인

---

## 4-5. (옵션 B) AGC — Application Gateway for Containers

> 이 섹션은 4-4의 Web App Routing 대신 **AGC**를 사용하는 **대안 방식**입니다.  
> 4-4를 이미 완료했다면, 먼저 되돌린 후 진행하세요.

### Web App Routing vs AGC 비교

| 항목 | Web App Routing (4-4) | AGC (이번 섹션) |
|------|----------------------|-----------------|
| **Ingress 컨트롤러** | NGINX (클러스터 내부) | Azure ALB Controller (Azure 네트워크) |
| **API** | Ingress API | **Gateway API** (K8s 표준) |
| **L7 기능** | NGINX 기반 | Azure 네이티브 (자동 스케일링, 트래픽 분할) |
| **스케일링** | 노드 리소스에 의존 | Azure 인프라 레벨 자동 스케일링 |
| **비용** | 추가 비용 없음 | AGC 리소스 별도 과금 |
| **적합한 경우** | 간단한 라우팅, 비용 절약 | 프로덕션 L7, 트래픽 분할, 고가용성 |

### Step 1: ALB Controller 애드온 활성화

```bash
az aks update \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable-alb-controller
```

> ⏱ 약 2~3분 소요됩니다.

활성화 확인:

```bash
# ALB Controller Pod 확인
kubectl get pods -n azure-alb-system

# GatewayClass 확인
kubectl get gatewayclass
```

### 예상 출력

```
NAME                                    READY   STATUS    RESTARTS   AGE
alb-controller-xxxx                     1/1     Running   0          2m
alb-controller-bootstrap-xxxx           1/1     Running   0          2m
```

```
NAME                 CONTROLLER                                   ACCEPTED   AGE
azure-alb-external   alb.networking.azure.io/alb-controller       True       2m
```

### Step 2: ALB 인프라 네임스페이스 & 리소스 생성

AGC는 Azure에서 관리되는 ALB 리소스가 필요합니다.

```bash
# ALB 인프라 네임스페이스 생성
kubectl create namespace alb-infra

# AKS 클러스터의 관리 ID에 필요한 권한 부여
MC_RG=$(az aks show -n $CLUSTER_NAME -g $RESOURCE_GROUP --query "nodeResourceGroup" -o tsv)
MC_RG_ID=$(az group show -n $MC_RG --query "id" -o tsv)

ALB_IDENTITY=$(az aks show -n $CLUSTER_NAME -g $RESOURCE_GROUP \
  --query "ingressProfile.webAppRouting.identity.objectId" -o tsv 2>/dev/null || \
  az aks show -n $CLUSTER_NAME -g $RESOURCE_GROUP \
  --query "identity.principalId" -o tsv)

# ApplicationLoadBalancer 리소스 생성
kubectl apply -f - <<EOF
apiVersion: alb.networking.azure.io/v1
kind: ApplicationLoadBalancer
metadata:
  name: pets-alb
  namespace: alb-infra
spec:
  associations:
    - $MC_RG_ID/providers/Microsoft.Network/virtualNetworks/$(az network vnet list -g $MC_RG --query "[0].name" -o tsv)/subnets/$(az network vnet subnet list -g $MC_RG --vnet-name $(az network vnet list -g $MC_RG --query "[0].name" -o tsv) --query "[?contains(name,'alb')].name | [0]" -o tsv 2>/dev/null || echo "aks-subnet")
EOF
```

> ⚠️ AGC는 전용 서브넷이 필요할 수 있습니다. 기본 AKS 서브넷으로 동작하지 않으면
> [공식 문서](https://learn.microsoft.com/ko-kr/azure/application-gateway/for-containers/quickstart-deploy-application-gateway-for-containers-alb-controller)를 참고하여 서브넷을 구성하세요.

### Step 3: Service 타입을 ClusterIP로 변경

> 4-4에서 이미 변경했다면 이 단계를 건너뛰세요.

```bash
kubectl patch svc store-front -n pets -p '{"spec": {"type": "ClusterIP"}}'
kubectl patch svc store-admin -n pets -p '{"spec": {"type": "ClusterIP"}}'
```

### Step 4: Gateway & HTTPRoute 배포

```bash
kubectl apply -f workshop-manifests/61-agc-gateway.yaml
```

매니페스트 내용 (`workshop-manifests/61-agc-gateway.yaml`):

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: pets-gateway
  namespace: pets
  annotations:
    alb.networking.azure.io/alb-namespace: alb-infra
    alb.networking.azure.io/alb-name: pets-alb
spec:
  gatewayClassName: azure-alb-external
  listeners:
    - name: http
      protocol: HTTP
      port: 80
      allowedRoutes:
        namespaces:
          from: Same
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: pets-store-front-route
  namespace: pets
spec:
  parentRefs:
    - name: pets-gateway
      namespace: pets
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /admin
      backendRefs:
        - name: store-admin
          port: 80
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: store-front
          port: 80
```

> **Ingress API vs Gateway API**: AGC는 Kubernetes **Gateway API** 표준을 사용합니다.
> - `Gateway` = 인프라 (리스너, 포트, 프로토콜)
> - `HTTPRoute` = 라우팅 규칙 (경로 → 서비스 매핑)

### Step 5: Gateway IP 확인 & 접속

```bash
# Gateway 상태 확인 (Programmed=True 대기)
kubectl get gateway pets-gateway -n pets -w
```

> ⏱ AGC 리소스가 Azure에서 프로비저닝되므로 **3~5분** 소요될 수 있습니다.

```
NAME           CLASS                ADDRESSES        PROGRAMMED   AGE
pets-gateway   azure-alb-external   <AGC-FQDN>       True         5m
```

```bash
AGC_FQDN=$(kubectl get gateway pets-gateway -n pets \
  -o jsonpath='{.status.addresses[0].value}')
echo "AGC 주소: http://$AGC_FQDN"
```

### 브라우저 접속

| URL | 서비스 | 설명 |
|-----|--------|------|
| `http://<AGC-FQDN>/` | store-front | 고객 펫 스토어 |
| `http://<AGC-FQDN>/admin` | store-admin | 관리자 대시보드 |

> **참고**: AGC는 IP 대신 FQDN(도메인)으로 접근합니다.

### CLI 검증

```bash
# 상품 확인
curl -s http://$AGC_FQDN/api/products | python3 -c "
import sys, json
for p in json.load(sys.stdin):
    print(f\"{p['id']}. {p['name']} — ₩{p['price']}\")
"

# 관리자 페이지 확인
curl -s -o /dev/null -w '%{http_code}' http://$AGC_FQDN/admin
# → 200
```

### (선택) 되돌리기 — AGC 정리

```bash
kubectl delete -f workshop-manifests/61-agc-gateway.yaml
kubectl delete ApplicationLoadBalancer pets-alb -n alb-infra
kubectl delete namespace alb-infra
kubectl patch svc store-front -n pets -p '{"spec": {"type": "LoadBalancer"}}'
kubectl patch svc store-admin -n pets -p '{"spec": {"type": "LoadBalancer"}}'
```

### AGC 점검 체크리스트

- [ ] `kubectl get gatewayclass` — `azure-alb-external` 존재
- [ ] `kubectl get gateway -n pets` — Programmed=True, ADDRESSES 할당
- [ ] `kubectl get httproute -n pets` — Accepted=True
- [ ] `http://<AGC-FQDN>/` — 고객 스토어 표시
- [ ] `http://<AGC-FQDN>/admin` — 관리자 대시보드 표시

---

## 4-6. (옵션 C) Windows 노드풀 + .NET order-service

> 이 섹션에서는 order-service를 **.NET 8 (C#)** 로 재작성하여 **Windows 노드풀**에 배포합니다.  
> Linux/Windows 혼합 AKS 클러스터 운영과 마이크로서비스 런타임 교체를 직접 체험합니다.

### 개요

| 항목 | Node.js 버전 (현재) | .NET 8 버전 (이번 실습) |
|------|---------------------|----------------------|
| 프레임워크 | Fastify | ASP.NET Minimal API |
| 런타임 | Node.js 24 (Linux) | .NET 8 (**Windows**) |
| 코드량 | ~267줄 (JS) | ~55줄 (C#) |
| 컨테이너 OS | Linux | Windows Server 2022 |
| 엔드포인트 | POST /, GET /health | 동일 |

### 혼합 클러스터 개념

```
AKS Cluster (Azure CNI Overlay)
├── nodepool1 (Linux)     ← store-front, product-service, MongoDB, RabbitMQ 등
└── npwin (Windows)       ← order-service-dotnet (.NET 8)
```

- `nodeSelector`와 `tolerations`로 Pod를 특정 OS 노드에 스케줄링합니다
- Linux 서비스와 Windows 서비스는 ClusterIP로 자유롭게 통신합니다

### Step 1: Windows 노드풀 추가

```bash
az aks nodepool add \
  --resource-group $RESOURCE_GROUP \
  --cluster-name $CLUSTER_NAME \
  --name npwin \
  --os-type Windows \
  --os-sku Windows2022 \
  --node-count 1 \
  --node-vm-size Standard_D2s_v3 \
  -o table
```

> ⏱ Windows 노드풀 추가에 약 5~8분 소요됩니다.

확인:

```bash
kubectl get nodes -o wide
```

```
NAME                                STATUS   ROLES   AGE   VERSION   OS-IMAGE
aks-nodepool1-xxxxx-vmss000000      Ready    <none>  30m   v1.34.x   Ubuntu 22.04.5 LTS
aks-nodepool1-xxxxx-vmss000001      Ready    <none>  30m   v1.34.x   Ubuntu 22.04.5 LTS
aksnpwin000000                      Ready    <none>  2m    v1.34.x   Windows Server 2022 Datacenter
```

### Step 2: Windows .NET 이미지 빌드 (ACR Task)

```bash
cd aks-store-demo-ko/src/order-service-dotnet

# Windows 컨테이너 이미지 빌드 (ACR에서 원격 빌드 — 로컬 Docker 불필요)
az acr build \
  --registry $ACR_NAME \
  --image order-service-dotnet:win \
  --platform windows \
  --file Dockerfile.windows \
  .
```

> **참고**: Windows 컨테이너 이미지는 로컬 Linux Docker에서 빌드할 수 없습니다.  
> `az acr build --platform windows`를 사용하면 ACR에서 원격 빌드됩니다.

### Step 3: 매니페스트 ACR 이름 수정 & 배포

```bash
cd /home/hyehunlim/projects/AKS-Workshop

# 매니페스트 내 ACR 이름 치환
sed -i "s/__ACR_NAME__/$ACR_NAME/g" workshop-manifests/65-order-service-dotnet-windows.yaml

# 배포
kubectl apply -f workshop-manifests/65-order-service-dotnet-windows.yaml
```

매니페스트의 핵심 부분:

```yaml
spec:
  nodeSelector:
    "kubernetes.io/os": windows       # Windows 노드에만 스케줄링
  tolerations:
    - key: "os"
      operator: "Equal"
      value: "windows"
      effect: "NoSchedule"
  containers:
    - name: order-service-dotnet
      image: <ACR>.azurecr.io/order-service-dotnet:win
      ports:
        - containerPort: 3000
```

### Step 4: 배포 확인

```bash
# Windows 노드에서 실행 중인지 확인
kubectl get pods -n pets -o wide | grep dotnet
```

```
order-service-dotnet-xxx    1/1   Running   0   1m   10.244.2.x   aksnpwin000000
```

```bash
# Health 엔드포인트로 .NET 런타임 확인
kubectl exec -n pets deploy/order-service-dotnet -- curl -s http://localhost:3000/health
```

```json
{"status":"ok","version":"1.0.0-dotnet","runtime":".NET 8"}
```

### Step 5: 트래픽 전환 (Node.js → .NET)

기존 Node.js order-service 대신 Windows .NET 버전으로 전환합니다.

```bash
# 기존 order-service 스케일 다운
kubectl scale deployment/order-service -n pets --replicas=0

# Service selector를 .NET 버전으로 전환
kubectl patch svc order-service -n pets \
  -p '{"spec": {"selector": {"app": "order-service-dotnet"}}}'
```

브라우저에서 store-front에 접속하여 주문을 생성하면, Windows .NET 서비스가 RabbitMQ에 메시지를 발행합니다.

```bash
# .NET 서비스 로그 확인
kubectl logs -n pets deploy/order-service-dotnet --tail=10
```

```
[.NET] Order published to queue 'orders'
[.NET] Order published to queue 'orders'
```

### (선택) 되돌리기

```bash
# Node.js order-service 복원
kubectl patch svc order-service -n pets \
  -p '{"spec": {"selector": {"app": "order-service"}}}'
kubectl scale deployment/order-service -n pets --replicas=1

# .NET 버전 정리
kubectl delete -f workshop-manifests/65-order-service-dotnet-windows.yaml

# Windows 노드풀 삭제
az aks nodepool delete \
  --resource-group $RESOURCE_GROUP \
  --cluster-name $CLUSTER_NAME \
  --name npwin --yes
```

### Windows 노드풀 점검 체크리스트

- [ ] `kubectl get nodes` — Windows 노드(aksnpwin) Ready
- [ ] `kubectl get pods -n pets -o wide` — dotnet Pod가 Windows 노드에서 실행
- [ ] `/health` 응답에 `"runtime":".NET 8"` 포함
- [ ] store-front에서 주문 시 `.NET` 로그 출력 확인

---

## 트러블슈팅

### Windows Pod가 Pending 상태

Windows 노드풀이 없거나 `nodeSelector`가 올바르지 않은 경우입니다.

```bash
kubectl describe pod -n pets -l app=order-service-dotnet
kubectl get nodes -l "kubernetes.io/os=windows"
```

> **참고**: Cilium 데이터플레인(`--network-dataplane cilium`)을 사용하는 클러스터에서는 Windows 노드를 추가할 수 없습니다. Cilium 없이 클러스터를 생성하세요.

```bash
kubectl describe pod -n pets -l app=order-service-dotnet
kubectl get nodes -l "kubernetes.io/os=windows"
```

### Ingress ADDRESS가 비어있음

Web App Routing 애드온이 정상 활성화되지 않은 경우입니다.

```bash
# 애드온 상태 확인
az aks show -n $CLUSTER_NAME -g $RESOURCE_GROUP \
  --query "ingressProfile.webAppRouting.enabled"

# app-routing-system 네임스페이스에 nginx Pod 확인
kubectl get pods -n app-routing-system
kubectl logs -n app-routing-system -l app=nginx --tail=20
```

### Ingress 404 에러

경로가 매칭되지 않는 경우입니다. Ingress 리소스가 올바른 네임스페이스(`pets`)에 생성되었는지 확인하세요.

```bash
kubectl describe ingress pets-ingress -n pets
```

### AGC Gateway가 Programmed=False

ALB Controller가 정상 동작하지 않거나 서브넷 연결이 잘못된 경우입니다.

```bash
# ALB Controller 로그 확인
kubectl logs -n azure-alb-system -l app=alb-controller --tail=30

# Gateway 이벤트 확인
kubectl describe gateway pets-gateway -n pets

# ApplicationLoadBalancer 상태 확인
kubectl get ApplicationLoadBalancer -n alb-infra -o yaml
```

> AGC 전용 서브넷이 없으면 프로비저닝이 실패합니다.  
> [공식 가이드](https://learn.microsoft.com/ko-kr/azure/application-gateway/for-containers/quickstart-deploy-application-gateway-for-containers-alb-controller)를 참고하여 서브넷을 생성하세요.

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
- [ ] 브라우저에서 store-front UI 확인
- [ ] 상품 목록이 정상 표시됨

---

| | |
|:---|---:|
| [⬅️ 03. 빌드 & 푸시](03-build-and-push.md) | [05. AI Agent 배포 ➡️](05-ai-agent.md) |
