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
```

## 1-3. Azure Container Registry (사전 구성)

> **참고**: ACR은 워크샵과 별도로 관리되는 **재사용 리소스**입니다.  
> 이미 생성된 ACR이 있으면 이 단계를 건너뛰고 기존 ACR 이름을 사용하세요.

```bash
# ACR 전용 리소스 그룹 (워크샵 정리 시 삭제하지 않음)
az group create --name WorkshopACR-RG --location koreacentral -o table

# ACR 이름은 글로벌 유일 (영소문자+숫자만)
ACR_NAME="aksworkshop$(openssl rand -hex 3)"
echo "ACR 이름: $ACR_NAME"

az acr create \
  --resource-group WorkshopACR-RG \
  --name $ACR_NAME \
  --sku Basic \
  --location koreacentral \
  -o table

# 로그인
az acr login --name $ACR_NAME
```

> **메모**: ACR은 `WorkshopACR-RG`에 별도로 유지되며, 워크샵 종료 후에도 삭제하지 않습니다.  
> 생성된 `$ACR_NAME` 값을 이후 섹션에서 계속 사용합니다. 터미널 세션이 끊기면 다시 설정하세요.

## 1-4. 환경 변수 설정 (이후 섹션에서 재사용)

```bash
export RESOURCE_GROUP="WorkshopDemo-RG"
export ACR_NAME="<ACR 이름 (예: aksworkshopkoea6e)>"
export CLUSTER_NAME="workshop-demo"
export LOCATION="koreacentral"
```

## 사전 점검 체크리스트

- [ ] `az account show` — 올바른 구독 선택
- [ ] `az group show -n WorkshopDemo-RG` — 워크샵 리소스 그룹 존재
- [ ] `az acr show -n $ACR_NAME` — ACR 정상 (재사용 또는 신규 생성)
- [ ] `docker info` — Docker 데몬 실행 중

---

| | |
|:---|---:|
| [⬅️ 00. 워크샵 개요](00-overview.md) | [02. 클러스터 생성 ➡️](02-create-cluster.md) |
