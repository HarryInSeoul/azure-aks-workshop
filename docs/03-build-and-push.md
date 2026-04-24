# 03. 애플리케이션 빌드 & ACR 푸시

이 섹션에서는 한국어로 로컬라이징된 펫 스토어 애플리케이션의 컨테이너 이미지를 빌드하고 ACR에 푸시합니다.

## 3-1. 소스 확인

`aks-store-demo-ko/src/` 디렉터리에 로컬라이징된 소스가 있습니다.

```
aks-store-demo-ko/src/
├── store-front/        # Vue.js 3 — 고객 웹 UI (한국어)
├── store-admin/        # Vue.js 3 — 관리자 대시보드
├── product-service/    # Rust — 상품 카탈로그 (한국어 상품명/설명)
├── order-service/      # Node.js / Fastify — 주문 처리
├── makeline-service/   # Go — 큐 소비 & DB 저장
├── virtual-customer/   # Rust — 부하 생성기
└── virtual-worker/     # Rust — 자동 주문 처리기
```

### 로컬라이징 포인트

| 파일 | 변경 내용 |
|------|-----------|
| `store-front/index.html` | `<title>Contoso 펫 스토어</title>`, `lang="ko"` |
| `store-front/src/components/TopNav.vue` | "Products" → "상품 목록", "Cart" → "장바구니" |
| `store-front/src/components/ProductCard.vue` | "Add to Cart" → "장바구니 담기" |
| `store-front/src/views/ProductDetailView.vue` | "Price:" → "가격:", "Product ID:" → "상품 ID:" |
| `store-front/src/views/ShoppingCartView.vue` | 장바구니 전체 UI 한국어화 |
| `product-service/src/data.rs` | 상품 10개 이름/설명 한국어 번역 |

## 3-2. 이미지 빌드 & 푸시

> **참고**: ACR은 워크샵 주최자가 사전 제공합니다. 이미지가 이미 푸시되어 있으면 이 단계를 건너뛰세요.

ACR 로그인 후 7개 서비스를 모두 빌드하고 `:ko` 태그로 푸시합니다.

```bash
az acr login --name $ACR_NAME

cd aks-store-demo-ko/src
```

### 각 서비스 빌드 & 푸시

```bash
# store-front
docker build -t $ACR_NAME.azurecr.io/store-front:ko store-front/
docker push $ACR_NAME.azurecr.io/store-front:ko

# store-admin
docker build -t $ACR_NAME.azurecr.io/store-admin:ko store-admin/
docker push $ACR_NAME.azurecr.io/store-admin:ko

# product-service
docker build -t $ACR_NAME.azurecr.io/product-service:ko product-service/
docker push $ACR_NAME.azurecr.io/product-service:ko

# order-service
docker build -t $ACR_NAME.azurecr.io/order-service:ko order-service/
docker push $ACR_NAME.azurecr.io/order-service:ko

# makeline-service
docker build -t $ACR_NAME.azurecr.io/makeline-service:ko makeline-service/
docker push $ACR_NAME.azurecr.io/makeline-service:ko

# virtual-customer
docker build -t $ACR_NAME.azurecr.io/virtual-customer:ko virtual-customer/
docker push $ACR_NAME.azurecr.io/virtual-customer:ko

# virtual-worker
docker build -t $ACR_NAME.azurecr.io/virtual-worker:ko virtual-worker/
docker push $ACR_NAME.azurecr.io/virtual-worker:ko
```

> ⏱ Rust 서비스(product-service, virtual-customer, virtual-worker)는 빌드에 3~5분 걸릴 수 있습니다.

## 3-3. 푸시 확인

대부분의 이미지는 공용 ACR(`aksworkshopkoea6e`)에 이미 존재합니다.

```bash
az acr repository list --name $ACR_NAME -o table
```

## 3-4. store-admin 소스 수정 & 개인 ACR에 빌드

> **핵심 핸즈온**: store-admin은 참가자가 직접 소스를 수정하고 **개인 ACR**에 이미지를 빌드합니다.

### store-admin 소스 수정 (한국어 UI 커스터마이징)

`aks-store-demo-ko/src/store-admin/` 디렉터리에서 원하는 부분을 자유롭게 수정하세요.

예시 — 페이지 타이틀 변경:

```bash
# index.html의 타이틀 확인
grep "<title>" aks-store-demo-ko/src/store-admin/index.html
```

원하는 텍스트로 수정한 뒤 개인 ACR에 빌드합니다.

### 개인 ACR에 이미지 빌드 & 푸시

```bash
cd aks-store-demo-ko/src

# 개인 ACR에 store-admin 빌드 (ACR Task — 원격 빌드)
az acr build \
  --registry $MY_ACR_NAME \
  --image store-admin:ko \
  --file store-admin/Dockerfile \
  store-admin/
```

확인:

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
sed -i "s|aksworkshopkoea6e.azurecr.io/store-admin:ko|$MY_ACR_NAME.azurecr.io/store-admin:ko|g" \
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
<MY_ACR>.azurecr.io/store-admin:ko            ← 개인 ACR
aksworkshopkoea6e.azurecr.io/virtual-customer:ko
aksworkshopkoea6e.azurecr.io/virtual-worker:ko
```

## 점검 체크리스트

- [ ] 공용 ACR에 6개 리포지터리 존재 (store-admin 제외)
- [ ] 개인 ACR에 store-admin 이미지 존재
- [ ] 매니페스트에서 store-admin만 개인 ACR을 가리킴, 나머지는 공용 ACR

---

| | |
|:---|---:|
| [⬅️ 02. 클러스터 생성](02-create-cluster.md) | [04. 앱 배포 ➡️](04-deploy-app.md) |
