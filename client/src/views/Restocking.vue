<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-controls">
          <input
            type="range"
            class="budget-slider"
            v-model.number="budget"
            :min="0"
            :max="maxBudget"
            :step="sliderStep"
          />
          <div class="budget-input-wrap">
            <span class="currency-prefix">{{ currencySymbol }}</span>
            <input
              type="number"
              class="budget-number"
              v-model.number="budget"
              :min="0"
              :max="maxBudget"
              :step="sliderStep"
            />
          </div>
        </div>

        <div v-if="orderSuccessMessage" class="success-message">{{ orderSuccessMessage }}</div>
        <div v-if="orderErrorMessage" class="error">{{ orderErrorMessage }}</div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budgetSelected') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.budgetUsed') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budgetUsed.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budgetRemaining.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || budget <= 0 || placingOrder"
            @click="placeOrder"
          >
            {{ placingOrder ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>
        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
                <th>{{ t('restocking.table.urgency') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ translateProductName(rec.name) }}</td>
                <td>{{ rec.quantity }}</td>
                <td>{{ currencySymbol }}{{ rec.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ rec.line_total.toLocaleString() }}</strong></td>
                <td>{{ rec.lead_time_days }}</td>
                <td>
                  <span :class="['badge', rec.trend]">{{ t(`trends.${rec.trend}`) }}</span>
                  <span v-if="rec.shortfall_ratio < 0" class="badge danger below-reorder-badge">
                    {{ t('restocking.belowReorderPoint') }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const inventoryItems = ref([])

    const budget = ref(0)
    const placingOrder = ref(false)
    const orderSuccessMessage = ref(null)
    const orderErrorMessage = ref(null)

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        forecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Join demand forecasts with inventory to determine restocking candidates.
    // NOTE: quantity and priority are two independent signals here:
    //   - recommended_qty comes from the forecast gap (how much to top up on-hand
    //     stock to meet forecasted demand)
    //   - shortfall_ratio comes from the reorder point (how urgently the item
    //     needs restocking, i.e. how far below its reorder point it currently is)
    // A high-quantity item is not necessarily an urgent one, and vice versa.
    const candidates = computed(() => {
      const inventoryBySku = new Map(inventoryItems.value.map(item => [item.sku, item]))
      const trendRank = { increasing: 0, stable: 1, decreasing: 2 }

      const result = []
      for (const forecast of forecasts.value) {
        const item = inventoryBySku.get(forecast.item_sku)
        if (!item) continue

        const recommended_qty = Math.max(forecast.forecasted_demand - item.quantity_on_hand, 0)
        if (recommended_qty === 0) continue

        const shortfall_ratio = (item.quantity_on_hand - item.reorder_point) / Math.max(item.reorder_point, 1)

        result.push({
          sku: item.sku,
          name: item.name,
          quantity: recommended_qty,
          unit_cost: item.unit_cost,
          lead_time_days: item.lead_time_days,
          line_total: recommended_qty * item.unit_cost,
          shortfall_ratio,
          trend: forecast.trend
        })
      }

      // Most urgent (lowest/most-negative shortfall_ratio) first, then by trend
      // (increasing demand breaks ties before stable/decreasing), then SKU for
      // a fully deterministic order.
      result.sort((a, b) => {
        if (a.shortfall_ratio !== b.shortfall_ratio) return a.shortfall_ratio - b.shortfall_ratio
        const trendDiff = (trendRank[a.trend] ?? 1) - (trendRank[b.trend] ?? 1)
        if (trendDiff !== 0) return trendDiff
        return a.sku.localeCompare(b.sku)
      })

      return result
    })

    const maxBudget = computed(() => {
      const total = candidates.value.reduce((sum, c) => sum + c.line_total, 0)
      return Math.ceil(total)
    })

    const sliderStep = computed(() => {
      return Math.max(Math.round(maxBudget.value / 100), 50)
    })

    // Greedily fill the budget in priority order. We `continue` (not `break`)
    // past items we can't afford, so a cheaper, lower-priority item further
    // down the list can still use leftover budget that a pricier, higher-
    // priority item earlier in the list couldn't fully consume. This
    // maximizes budget utilization at the cost of strict priority ordering.
    const recommendations = computed(() => {
      let remaining = budget.value
      const picked = []

      for (const candidate of candidates.value) {
        const affordableQty = Math.min(candidate.quantity, Math.floor(remaining / candidate.unit_cost))
        if (affordableQty < 1) continue

        const line_total = affordableQty * candidate.unit_cost
        picked.push({
          ...candidate,
          quantity: affordableQty,
          line_total
        })
        remaining -= line_total
      }

      return picked
    })

    const budgetUsed = computed(() => {
      return recommendations.value.reduce((sum, r) => sum + r.line_total, 0)
    })

    const budgetRemaining = computed(() => {
      return budget.value - budgetUsed.value
    })

    const formatDate = (dateString) => {
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return new Date(dateString).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const placeOrder = async () => {
      orderSuccessMessage.value = null
      orderErrorMessage.value = null
      placingOrder.value = true
      try {
        const payload = {
          budget: budget.value,
          items: recommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.quantity,
            unit_cost: r.unit_cost,
            lead_time_days: r.lead_time_days
          }))
        }
        const created = await api.createRestockingOrder(payload)
        orderSuccessMessage.value = t('restocking.orderSuccess', { date: formatDate(created.expected_delivery) })
        // Reset budget so the same recommendations can't be double-submitted
        budget.value = 0
      } catch (err) {
        orderErrorMessage.value = err.response?.data?.detail || t('restocking.orderError')
      } finally {
        placingOrder.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      budget,
      maxBudget,
      sliderStep,
      candidates,
      recommendations,
      budgetUsed,
      budgetRemaining,
      currencySymbol,
      translateProductName,
      placingOrder,
      orderSuccessMessage,
      orderErrorMessage,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.budget-controls {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.budget-slider {
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  outline: none;
  appearance: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.budget-input-wrap {
  display: flex;
  align-items: center;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0.4rem 0.75rem;
  background: white;
  transition: all 0.2s;
  flex-shrink: 0;
  min-width: 160px;
}

.budget-input-wrap:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.currency-prefix {
  color: #64748b;
  font-weight: 600;
  margin-right: 0.375rem;
}

.budget-number {
  border: none;
  outline: none;
  font-size: 0.938rem;
  font-weight: 600;
  color: #0f172a;
  width: 100%;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.success-message {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.below-reorder-badge {
  margin-left: 0.375rem;
}
</style>
