<template>
  <div class="product-list">
    <ProductCard v-for="product in products" :key="product.id" :product="product" />
  </div>
  <AiRecommend />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useProductStore } from '@/stores'
import ProductCard from '@/components/ProductCard.vue'
import AiRecommend from '@/components/AiRecommend.vue'

const productStore = useProductStore()
const products = computed(() => productStore.products)
</script>
