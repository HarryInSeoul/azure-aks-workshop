# 02. AKS 클러스터 생성

<details>
<summary><strong>⚠️ Cloud Shell 세션이 만료된 경우 — 환경 변수 재설정</strong></summary>

```bash
export RESOURCE_GROUP="WorkshopDemo-RG"
export CLUSTER_NAME="workshop-demo"
export LOCATION="koreacentral"
export MY_ACR_NAME=$(az acr list --resource-group $RESOURCE_GROUP --query "[?starts_with(name,'workshop')].name" -o tsv)
```

</details>

AKS 클러스터는 워크샵의 모든 워크로드가 실행되는 기반 인프라입니다.  
이 섹션에서는 **NAP(Node Auto Provisioning)**, **KEDA**, **Azure CNI Overlay** 네트워크를 활성화한 AKS 클러스터를 생성하고 ACR을 연결합니다.

### 이 섹션에서 배우는 것

| 항목 | 설명 |
|------|------|
| **AKS 클러스터 생성** | CLI 또는 Terraform으로 프로덕션급 클러스터 구성 |
| **NAP (Karpenter)** | 워크로드에 맞춰 노드를 자동으로 생성/삭제하는 노드 오토스케일링 |
| **KEDA** | RabbitMQ 큐 길이 등 이벤트 기반으로 Pod을 스케일링하는 오토스케일러 |
| **Azure CNI Overlay** | Pod IP와 노드 IP를 분리하여 IP 주소 소모를 줄이는 네트워크 모드 |
| **ACR 연결** | AKS가 컨테이너 레지스트리에서 이미지를 풀(pull)할 수 있도록 권한 설정 |

---

## 2-1. Kubernetes 버전 확인

클러스터를 생성하기 전에 사용 가능한 Kubernetes 버전을 확인하고, 원하는 버전을 선택합니다.

```bash
# 사용 가능한 Kubernetes 버전 목록 확인
az aks get-versions --location $LOCATION -o table
```

원하는 버전을 환경 변수로 설정합니다.

```bash
# 최신 안정 버전 자동 선택
export K8S_VERSION=$(az aks get-versions --location $LOCATION \
  --query "values[?isDefault].version" -o tsv)
echo "Kubernetes 버전: $K8S_VERSION"
```

> [!TIP]
> 특정 버전을 사용하려면 직접 지정할 수 있습니다.
> ```bash
> export K8S_VERSION="1.35.1"
> ```

## 2-2. 클러스터 생성

NAP(Node Auto Provisioning), KEDA, Azure CNI Overlay를 활성화한 AKS 클러스터를 생성합니다.

> 아래 **Azure CLI** 또는 **Terraform** 탭 중 선호하는 방식을 선택하세요.

<details>
<summary><strong>옵션 A: Azure CLI로 생성</strong></summary>

```bash
az aks create \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --kubernetes-version $K8S_VERSION \
  --node-count 2 \
  --node-vm-size Standard_D2s_v3 \
  --enable-keda \
  --node-provisioning-mode Auto \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --generate-ssh-keys \
  -o table
```

> [!NOTE]
> ⏱ 클러스터 생성에 약 5~10분 소요됩니다.

### 주요 옵션 설명

| 옵션 | 설명 |
|------|------|
| `--kubernetes-version` | 사용할 Kubernetes 버전 (2-1에서 설정) |
| `--node-provisioning-mode Auto` | NAP(Karpenter 기반) 활성화 — 워크로드에 맞춰 노드를 자동 생성/삭제 |
| `--enable-keda` | KEDA(이벤트 기반 오토스케일러) 활성화 |
| `--network-plugin azure --network-plugin-mode overlay` | Azure CNI Overlay 네트워크 (Pod IP ↔ 노드 IP 분리) |
| `--generate-ssh-keys` | 노드 VM용 SSH 키 쌍을 `~/.ssh/id_rsa`에 자동 생성 (이미 있으면 기존 키 재사용) |

</details>

<details>
<summary><strong>옵션 B: Terraform으로 생성</strong></summary>

### 사전 준비

Terraform이 설치되어 있는지 확인합니다.

```bash
terraform --version
```

> Cloud Shell에는 Terraform이 기본 설치되어 있습니다. 로컬 환경이라면 [Terraform 설치 가이드](https://developer.hashicorp.com/terraform/install)를 참고하세요.

### Terraform 파일 작성

워크샵 디렉터리에 `terraform/` 폴더를 생성하고 구성 파일을 작성합니다.

```bash
mkdir -p terraform && cd terraform
```

**`terraform/main.tf`** — 아래 명령어를 복사하여 실행합니다:

```bash
cat > main.tf << 'EOF'
# ============================================================
# main.tf — AKS 워크샵 클러스터 메인 구성 파일
# 
# 이 파일은 워크샵에 필요한 Azure 리소스를 정의합니다:
#   - 리소스 그룹 (WorkshopDemo-RG)
#   - AKS 클러스터 (NAP, KEDA, Azure CNI Overlay 활성화)
#
# 사용법:
#   terraform init
#   terraform plan -var="subscription_id=<구독ID>"
#   terraform apply -var="subscription_id=<구독ID>" -auto-approve
# ============================================================

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0" # AzureRM 프로바이더 4.x 사용
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id # 대상 Azure 구독 ID
}

# ----------------------------------------------------------
# 리소스 그룹 — 워크샵 리소스를 하나의 그룹으로 관리
# 삭제 시 하위 리소스(AKS, VMSS, LB 등)가 모두 정리됨
# ----------------------------------------------------------
resource "azurerm_resource_group" "workshop" {
  name     = var.resource_group_name
  location = var.location
}

# ----------------------------------------------------------
# AKS 클러스터 정의
# ----------------------------------------------------------
resource "azurerm_kubernetes_cluster" "workshop" {
  name                = var.cluster_name
  location            = azurerm_resource_group.workshop.location
  resource_group_name = azurerm_resource_group.workshop.name
  dns_prefix          = var.cluster_name
  kubernetes_version  = var.kubernetes_version # 2-1절에서 확인한 K8s 버전

  # 기본 노드풀 — 시스템 워크로드용 Linux 노드
  default_node_pool {
    name                = "nodepool1"
    node_count          = 2                    # 초기 노드 수
    vm_size             = "Standard_D2s_v3"    # 2 vCPU, 8 GiB 메모리
    os_disk_type        = "Managed"
  }

  # 관리 ID — AKS가 Azure 리소스(LB, 디스크 등)를 제어할 때 사용
  identity {
    type = "SystemAssigned"
  }

  # 네트워크 — Azure CNI Overlay
  # Pod IP와 노드 IP를 분리하여 IP 주소 소모를 줄임
  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
  }

  # NAP (Node Auto Provisioning) — Karpenter 기반
  # 워크로드 요구사항에 맞춰 노드를 자동 생성/삭제
  node_provisioning_profile {
    mode = "Auto"
  }

  # KEDA (Kubernetes Event-Driven Autoscaling) 활성화
  # 이벤트 기반(RabbitMQ 큐 길이 등)으로 Pod 오토스케일링 가능
  workload_autoscaler_profile {
    keda_enabled = true
  }

  tags = {
    environment = "workshop" # 리소스 식별용 태그
  }
}
EOF
```

**`terraform/variables.tf`** — 아래 명령어를 복사하여 실행합니다:

```bash
cat > variables.tf << 'EOF'
# ============================================================
# variables.tf — 입력 변수 정의
#
# 클러스터 생성에 필요한 매개변수를 정의합니다.
# terraform plan/apply 시 -var 플래그 또는 terraform.tfvars 파일로 주입합니다.
#
# 예시:
#   terraform apply -var="subscription_id=$(az account show --query id -o tsv)"
# ============================================================

variable "subscription_id" {
  description = "Azure 구독 ID (필수 — az account show --query id -o tsv 로 확인)"
  type        = string
}

variable "resource_group_name" {
  description = "리소스 그룹 이름 — 워크샵 종료 시 이 그룹만 삭제하면 전체 정리"
  type        = string
  default     = "WorkshopDemo-RG"
}

variable "cluster_name" {
  description = "AKS 클러스터 이름"
  type        = string
  default     = "workshop-demo"
}

variable "location" {
  description = "Azure 리전 (ex: koreacentral, eastus)"
  type        = string
  default     = "koreacentral"
}

variable "kubernetes_version" {
  description = "Kubernetes 버전 — az aks get-versions --location <리전> -o table 으로 확인"
  type        = string
  default     = "1.31.7"
}
EOF
```

**`terraform/outputs.tf`** — 아래 명령어를 복사하여 실행합니다:

```bash
cat > outputs.tf << 'EOF'
# ============================================================
# outputs.tf — 출력값 정의
#
# terraform apply 완료 후 터미널에 표시되는 정보입니다.
# 클러스터 이름, 리소스 그룹 이름, kubeconfig 설정 명령어를
# 바로 복사하여 다음 단계(2-3. ACR 연결, 2-4. kubeconfig 설정)에
# 사용할 수 있습니다.
# ============================================================

# 생성된 AKS 클러스터 이름
output "cluster_name" {
  value = azurerm_kubernetes_cluster.workshop.name
}

# 리소스 그룹 이름 (정리 시 이 그룹만 삭제)
output "resource_group_name" {
  value = azurerm_resource_group.workshop.name
}

# kubeconfig 설정 명령어 — 복사해서 바로 실행 가능
output "kube_config_command" {
  value = "az aks get-credentials --name ${azurerm_kubernetes_cluster.workshop.name} --resource-group ${azurerm_resource_group.workshop.name} --overwrite-existing"
}
EOF
```

### Terraform 실행

```bash
# 초기화
terraform init

# 플랜 확인
terraform plan \
  -var="subscription_id=$(az account show --query id -o tsv)" \
  -var="kubernetes_version=$K8S_VERSION"

# 적용 (클러스터 생성)
terraform apply \
  -var="subscription_id=$(az account show --query id -o tsv)" \
  -var="kubernetes_version=$K8S_VERSION" \
  -auto-approve
```

> [!NOTE]
> ⏱ 클러스터 생성에 약 5~10분 소요됩니다.

> [!WARNING]
> 아래와 같은 에러가 발생하면, 01절(1-2)에서 이미 `WorkshopDemo-RG`를 CLI로 생성했기 때문입니다.
> ```
> Error: a resource with the ID "/subscriptions/.../resourceGroups/WorkshopDemo-RG"
>        already exists - to be managed via Terraform this resource needs to be
>        imported into the State.
> ```
> - **방법 1**: 기존 RG를 Terraform에 import 합니다.
>   ```bash
>   terraform import azurerm_resource_group.workshop \
>     /subscriptions/$(az account show --query id -o tsv)/resourceGroups/WorkshopDemo-RG
>   ```
>   import 후 `terraform apply` 명령을 다시 실행하세요.
> - **방법 2**: 처음부터 다시 시작하려면, 01절의 1-2 단계(RG 생성)를 건너뛰고 Terraform이 RG를 생성하도록 합니다.

### Terraform 출력값을 환경 변수로 설정

Terraform 경로를 선택한 경우, 이후 단계에서 사용할 환경 변수를 설정합니다.

```bash
export CLUSTER_NAME=$(terraform output -raw cluster_name)
export RESOURCE_GROUP=$(terraform output -raw resource_group_name)
echo "CLUSTER_NAME=$CLUSTER_NAME, RESOURCE_GROUP=$RESOURCE_GROUP"
```

```bash
# 워크샵 루트 디렉터리로 복귀
cd ..
```

</details>

## 2-3. ACR 연결

AKS 클러스터가 개인 ACR에서 이미지를 풀(pull) 할 수 있도록 연결합니다.

```bash
# 개인 ACR 연결 (store-admin 이미지)
az aks update \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --attach-acr $MY_ACR_NAME
```

## 2-4. kubeconfig 설정

> [!TIP]
> Terraform으로 생성한 경우, `terraform output`에 표시된 `kube_config_command` 값을 그대로 복사하여 실행해도 됩니다.

```bash
az aks get-credentials \
  --name $CLUSTER_NAME \
  --resource-group $RESOURCE_GROUP \
  --overwrite-existing
```

## 2-5. 클러스터 상태 확인

```bash
# 노드 상태
kubectl get nodes -o wide

# NAP/Karpenter NodePool 확인
kubectl get nodepools.karpenter.sh
kubectl get aksnodeclasses.karpenter.azure.com
```

> [!WARNING]
> **아래와 같은 에러가 나타나면** 2-4의 `az aks get-credentials` 가 정상 실행되지 않은 것입니다.  
> 2-4 단계를 다시 실행한 후 재시도하세요.
>
> ![kubeconfig 미설정 에러](images/kubeconfig-error.png)

### 예상 출력

```
NAME                                STATUS   ROLES    AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
aks-nodepool1-15072150-vmss000000   Ready    <none>   28m   v1.34.7   10.224.0.4    <none>        Ubuntu 22.04.5 LTS   5.15.0-1110-azure   containerd://1.7.31-1
aks-nodepool1-15072150-vmss000001   Ready    <none>   28m   v1.34.7   10.224.0.5    <none>        Ubuntu 22.04.5 LTS   5.15.0-1110-azure   containerd://1.7.31-1
```


```
NAME           NODECLASS      NODES   READY   AGE
default        default        0       True    12m
system-surge   system-surge   0       True    12m

NAME           READY   AGE
default        True    12m
system-surge   True    12m
```

> [!NOTE]
> NAP 모드에서 Karpenter 컨트롤러는 AKS 관리 컨트롤 플레인 내부에서 실행되므로 `kube-system` 네임스페이스에 Karpenter Pod가 보이지 않습니다. `kubectl get nodepools.karpenter.sh` 명령으로 동작을 확인하세요.

## 점검 체크리스트

- [ ] `kubectl get nodes` — 2개 노드 Ready
- [ ] `kubectl get nodepools.karpenter.sh` — default, system-surge NodePool 존재
- [ ] `az aks show -n $CLUSTER_NAME -g $RESOURCE_GROUP --query "nodeProvisioningProfile"` — mode: Auto 확인

---

| | |
|:---|---:|
| [⬅️ 01. 사전 준비](01-prerequisites.md) | [03. 빌드 & 푸시 ➡️](03-build-and-push.md) |
