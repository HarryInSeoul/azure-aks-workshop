<template>
  <TopNav />
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useProductStore, useOrderStore } from '@/stores'
import type { Product, Order } from '@/types'
import TopNav from './components/TopNav.vue'

const productStore = useProductStore()
const orderStore = useOrderStore()

onMounted(() => {
  if (productStore.count === 0) {
    console.log('Fetching products')
    fetch('/api/products')
      .then((response) => response.json())
      .then((data: Product[]) => {
        productStore.addProducts(data)
        console.log(`Fetched ${data.length} products`)
      })
      .catch((error) => {
        console.log(error)
        alert('상품 정보를 불러오는 중 오류가 발생했습니다')
      })
  }
  if (orderStore.count === 0) {
    console.log('Fetching orders')
    fetch('/api/makeline/order/fetch')
      .then((response) => response.json())
      .then((data: Order[]) => {
        orderStore.addOrders(data)
        console.log(`Fetched ${data.length} orders`)
      })
      .catch((error) => {
        console.log(error)
        orderStore.initialized = true
        console.error(`Error occurred while fetching orders`, error)
      })
  }
})
</script>

<style scoped></style>
