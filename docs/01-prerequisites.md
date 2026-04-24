# 01. 사전 준비

## 필수 도구

| 도구 | 최소 버전 | 설치 확인 |
|------|-----------|-----------|
| Azure CLI | 2.61+ | `az version` |
| kubectl | 1.28+ | `kubectl version --client` |
| Docker | 24+ | `docker --version` |
| aks-preview 확장 | 최신 | `az extension show --name aks-preview` |

## 1-1. Azure CLI 확장 설치

```bash
az extension add --name aks-preview --upgrade
az provider register --namespace Microsoft.ContainerService
```

## 1-2. 구독 확인 & 리소스 그룹 생성

```bash
# 사용할 구독 설정
az account set --subscription "<구독 ID>"
az account show -o table

# 워크샵 리소스 그룹 생성 (AKS 클러스터 등 모든 워크샵 리소스가 여기에 생성됩니다)
az group create --name WorkshopDemo-RG --location koreacentral -o table

# 리소스 그룹 이름을 환경 변수로 설정 (이후 명령에서 사용)
export RESOURCE_GROUP="WorkshopDemo-RG"
```

## 1-3. Azure Container Registry (사전 제공)

> **참고**: 대부분의 컨테이너 이미지는 워크샵 주최자가 사전 구성한 **공용 ACR**에서 제공됩니다.  
> `store-admin`은 참가자가 직접 소스를 수정하고 빌드하기 위해 **개인 ACR**을 사용합니다.

### 공용 ACR (주최자 제공 — 이미지 Pull 전용)

```bash
# 공용 ACR 접근 확인
az acr show --name aksworkshopkoea6e -o table
```

### 참가자 개인 ACR 생성

```bash
# 고유한 ACR 이름 생성 (영소문자+숫자만, 글로벌 유일)
MY_ACR_NAME="workshop$(whoami | tr -d '.-_')$(openssl rand -hex 2)"
echo "내 ACR 이름: $MY_ACR_NAME"

# ACR 생성 (WorkshopDemo-RG에 함께 생성 — 워크샵 종료 시 자동 삭제)
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $MY_ACR_NAME \
  --sku Basic \
  --location koreacentral \
  -o table
```

> **참고**: 개인 ACR은 `WorkshopDemo-RG`에 생성하므로, 워크샵 종료 시 리소스 그룹 삭제와 함께 자동 정리됩니다.

## 1-4. 환경 변수 설정 (이후 섹션에서 재사용)

```bash
# RESOURCE_GROUP은 1-2에서 이미 설정했으므로 새 터미널에서만 다시 실행하세요
export RESOURCE_GROUP="WorkshopDemo-RG"
export ACR_NAME="aksworkshopkoea6e"
export MY_ACR_NAME="<위에서 생성한 개인 ACR 이름>"
export CLUSTER_NAME="workshop-demo"
export LOCATION="koreacentral"
```

> **참고**:
> - `ACR_NAME` — 공용 ACR (주최자 제공, 대부분의 이미지 소스)
> - `MY_ACR_NAME` — 참가자 개인 ACR (store-admin 이미지 빌드/푸시용)

## 사전 점검 체크리스트

- [ ] `az account show` — 올바른 구독 선택
- [ ] `az group show -n WorkshopDemo-RG` — 워크샵 리소스 그룹 존재
- [ ] `az acr show -n $ACR_NAME` — ACR 접근 가능
- [ ] `docker info` — Docker 데몬 실행 중

---

| | |
|:---|---:|
| [⬅️ 00. 워크샵 개요](00-overview.md) | [02. 클러스터 생성 ➡️](02-create-cluster.md) |
