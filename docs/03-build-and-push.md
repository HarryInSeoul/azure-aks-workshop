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

```bash
az acr repository list --name $ACR_NAME -o table
```

### 예상 출력

```
Result
----------------
makeline-service
order-service
product-service
store-admin
store-front
virtual-customer
virtual-worker
```

## 3-4. (선택) 로컬 Docker Compose 테스트

배포 전에 로컬에서 전체 스택을 실행해볼 수 있습니다.

```bash
cd aks-store-demo-ko
docker-compose -f docker-compose-local.yml up -d
```

- store-front: http://localhost:80
- store-admin: http://localhost:8081

```bash
# 정리
docker-compose -f docker-compose-local.yml down
```

## 3-5. 매니페스트 내 ACR 이름 수정

`workshop-manifests/aks-store-all-in-one-ko.yaml` 파일에서 ACR 이름을 본인의 ACR로 변경합니다.

```bash
cd /home/hyehunlim/projects/AKS-Worklshop

# 일괄 치환 (aksworkshopkoea6e → 본인 ACR 이름)
sed -i "s/aksworkshopkoea6e/$ACR_NAME/g" workshop-manifests/aks-store-all-in-one-ko.yaml
```

확인:
```bash
grep "azurecr.io" workshop-manifests/aks-store-all-in-one-ko.yaml
```

## 점검 체크리스트

- [ ] ACR에 7개 리포지터리 존재
- [ ] 매니페스트의 이미지 참조가 본인 ACR을 가리킴

---

| | |
|:---|---:|
| [⬅️ 02. 클러스터 생성](02-create-cluster.md) | [04. 앱 배포 ➡️](04-deploy-app.md) |
