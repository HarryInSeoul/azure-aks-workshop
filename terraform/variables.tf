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
