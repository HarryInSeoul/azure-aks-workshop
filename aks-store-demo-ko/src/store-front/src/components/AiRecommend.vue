<template>
  <div class="ai-recommend-section">
    <button class="ai-recommend-btn" @click="togglePanel" :disabled="loading">
      🤖 AI 상품 추천
    </button>

    <div v-if="showPanel" class="ai-recommend-panel">
      <!-- AI Agent 미배포 상태 -->
      <div v-if="!agentAvailable" class="ai-unavailable">
        <p>⚠️ AI 추천 서비스가 아직 준비되지 않았습니다.</p>
        <p class="ai-guide-msg">
          <a href="https://github.com/bbiggum/azure-aks-workshop/blob/main/docs/06-ai-agent.md" target="_blank">
            05. AI Agent 배포
          </a> 섹션을 완료한 후 사용할 수 있습니다.
        </p>
        <button class="ai-close-btn" @click="showPanel = false">닫기</button>
      </div>

      <!-- AI Agent 사용 가능 -->
      <div v-else>
        <div class="ai-input-area">
          <input
            v-model="query"
            type="text"
            placeholder="어떤 상품을 찾고 계세요? (예: 활발한 고양이 장난감)"
            class="ai-input"
            @keyup.enter="getRecommendation"
          />
          <button class="ai-submit-btn" @click="getRecommendation" :disabled="loading || !query.trim()">
            {{ loading ? '추천 중...' : '추천받기' }}
          </button>
        </div>

        <div v-if="error" class="ai-error">
          <p>{{ error }}</p>
        </div>

        <div v-if="result" class="ai-results">
          <p class="ai-message">{{ result.message }}</p>
          <div class="ai-result-cards">
            <div v-for="rec in result.recommendations" :key="rec.productId" class="ai-result-card">
              <router-link :to="`/product/${rec.productId}`" class="ai-product-link">
                <strong>{{ rec.name }}</strong>
                <span class="ai-price">₩{{ rec.price }}</span>
              </router-link>
              <p class="ai-reason">{{ rec.reason }}</p>
            </div>
          </div>
          <p v-if="result.mode === 'demo'" class="ai-mode-badge">데모 모드</p>
        </div>

        <button class="ai-close-btn" @click="showPanel = false">닫기</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Recommendation {
  productId: number
  name: string
  price: number
  reason: string
}

interface RecommendResult {
  recommendations: Recommendation[]
  message: string
  mode: string
}

const showPanel = ref(false)
const agentAvailable = ref(false)
const query = ref('')
const loading = ref(false)
const error = ref('')
const result = ref<RecommendResult | null>(null)

const checkAgentHealth = async () => {
  try {
    const res = await fetch('/api/ai/health', { signal: AbortSignal.timeout(3000) })
    if (res.ok) {
      const data = await res.json()
      agentAvailable.value = data.status === 'ok'
    }
  } catch {
    agentAvailable.value = false
  }
}

const togglePanel = () => {
  showPanel.value = !showPanel.value
  if (showPanel.value) {
    checkAgentHealth()
  }
}

const getRecommendation = async () => {
  if (!query.value.trim()) return
  loading.value = true
  error.value = ''
  result.value = null

  try {
    const res = await fetch('/api/ai/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query.value }),
      signal: AbortSignal.timeout(30000)
    })
    if (!res.ok) throw new Error(`서버 오류 (${res.status})`)
    result.value = await res.json()
  } catch (e: any) {
    if (e.name === 'TimeoutError') {
      error.value = '요청 시간이 초과되었습니다. 다시 시도해 주세요.'
    } else {
      error.value = 'AI 추천을 가져오는 데 실패했습니다.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  checkAgentHealth()
})
</script>

<style scoped>
.ai-recommend-section {
  margin: 2rem auto;
  text-align: center;
  max-width: 700px;
}

.ai-recommend-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 28px;
  font-size: 16px;
  border-radius: 25px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.ai-recommend-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.ai-recommend-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ai-recommend-panel {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  text-align: left;
}

.ai-unavailable {
  text-align: center;
  color: #666;
}

.ai-unavailable p {
  margin: 0.5rem 0;
}

.ai-guide-msg {
  font-size: 0.9rem;
}

.ai-guide-msg a {
  color: var(--accent-color);
  text-decoration: underline;
}

.ai-input-area {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.ai-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.ai-submit-btn {
  background: var(--accent-color, #007bff);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
}

.ai-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ai-error {
  color: #dc3545;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
}

.ai-message {
  font-style: italic;
  color: #555;
  margin-bottom: 1rem;
}

.ai-result-cards {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.ai-result-card {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.ai-product-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-decoration: none;
  color: var(--primary-color, #2a2a2a);
  margin-bottom: 0.5rem;
}

.ai-product-link:hover {
  color: var(--accent-color, #007bff);
}

.ai-price {
  color: var(--accent-color, #007bff);
  font-weight: bold;
}

.ai-reason {
  font-size: 0.85rem;
  color: #777;
  margin: 0;
}

.ai-mode-badge {
  text-align: right;
  font-size: 0.75rem;
  color: #999;
  margin-top: 0.5rem;
}

.ai-close-btn {
  display: block;
  margin: 1rem auto 0;
  background: none;
  border: 1px solid #ccc;
  padding: 6px 16px;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
}
</style>
