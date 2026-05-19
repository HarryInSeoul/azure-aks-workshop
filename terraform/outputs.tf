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
