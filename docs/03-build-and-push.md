# 03. 애플리케이션 빌드 & ACR 푸시

이 섹션에서는 `store-admin` 서비스의 소스를 수정하고, 컨테이너 이미지를 빌드하여 개인 ACR에 푸시합니다.

> **참고**: `store-admin`을 제외한 나머지 서비스 이미지는 워크샵 주최자가 사전 빌드하여 공용 ACR에 준비해 두었습니다.  
> 참가자는 `store-admin`만 직접 빌드합니다.

## 3-1. 소스 클론

Cloud Shell에서 워크샵 리포지터리를 클론합니다.

```bash
git clone https://github.com/bbiggum/azure-aks-workshop.git
cd azure-aks-workshop
```

## 3-2. 소스 구조 확인

`aks-store-demo-ko/src/` 디렉터리에 소스가 있습니다.

```
aks-store-demo-ko/src/
├── store-front/        # Vue.js 3 — 고객 웹 UI
├── store-admin/        # Vue.js 3 — 관리자 대시보드  ← 직접 빌드
├── ai-agent/           # Python / FastAPI — AI 상품 추천
├── product-service/    # Rust — 상품 카탈로그
├── order-service/      # Node.js / Fastify — 주문 처리
├── makeline-service/   # Go — 큐 소비 & DB 저장
├── virtual-customer/   # Rust — 부하 생성기
└── virtual-worker/     # Rust — 자동 주문 처리기
```

## 3-3. store-admin 소스 수정

`aks-store-demo-ko/src/store-admin/` 디렉터리에서 원하는 부분을 자유롭게 수정하세요.

예시 — 페이지 타이틀 변경:

```bash
# index.html의 타이틀 확인
grep "<title>" aks-store-demo-ko/src/store-admin/index.html
```

원하는 텍스트로 수정한 뒤 다음 단계에서 개인 ACR에 빌드합니다.

## 3-4. 이미지 빌드 & ACR 푸시

ACR Task를 사용하여 **클라우드에서 원격 빌드** 후 개인 ACR에 푸시합니다.

```bash
cd aks-store-demo-ko/src

# 개인 ACR에 store-admin 빌드 (ACR Task — 원격 빌드)
az acr build \
  --registry $MY_ACR_NAME \
  --image store-admin:v1 \
  --file store-admin/Dockerfile \
  store-admin/
```

> **💡 ACR Task**: `az acr build`는 Docker 데몬 없이 Azure에서 직접 이미지를 빌드합니다.  
> Cloud Shell 환경에서도 별도의 Docker 설치 없이 사용할 수 있습니다.

빌드 확인:

```bash
az acr repository list --name $MY_ACR_NAME -o table
```

```
Result
-----------
store-admin
```

## 3-5. 매니페스트 내 ACR 이름 수정

`workshop-manifests/aks-store-all-in-one-ko.yaml` 파일에서 store-admin 이미지만 개인 ACR로 변경합니다.

```bash
cd /home/hyehunlim/projects/AKS-Workshop

# store-admin 이미지만 개인 ACR로 변경
sed -i "s|aksworkshopkoea6e.azurecr.io/store-admin:ko|$MY_ACR_NAME.azurecr.io/store-admin:v1|g" \
  workshop-manifests/aks-store-all-in-one-ko.yaml
```

확인:

```bash
grep "azurecr.io" workshop-manifests/aks-store-all-in-one-ko.yaml
```

```
# 예상 출력 — store-admin만 개인 ACR, 나머지는 공용 ACR
aksworkshopkoea6e.azurecr.io/order-service:ko
aksworkshopkoea6e.azurecr.io/makeline-service:ko
aksworkshopkoea6e.azurecr.io/product-service:ko
aksworkshopkoea6e.azurecr.io/store-front:ko
<MY_ACR>.azurecr.io/store-admin:v1            ← 개인 ACR
aksworkshopkoea6e.azurecr.io/virtual-customer:ko
aksworkshopkoea6e.azurecr.io/virtual-worker:ko
```

## 점검 체크리스트

- [ ] `az acr repository list --name $MY_ACR_NAME -o table` — 개인 ACR에 store-admin 이미지 존재
- [ ] `grep "azurecr.io" workshop-manifests/aks-store-all-in-one-ko.yaml` — store-admin만 개인 ACR을 가리킴

---

| | |
|:---|---:|
| [⬅️ 02. 클러스터 생성](02-create-cluster.md) | [04. 앱 배포 ➡️](04-deploy-app.md) |
