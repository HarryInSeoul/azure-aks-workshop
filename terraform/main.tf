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
