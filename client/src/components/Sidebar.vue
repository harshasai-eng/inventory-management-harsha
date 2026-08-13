<template>
  <aside class="sidebar">
    <div class="brand">
      <h1 class="brand-title">{{ t('nav.companyName') }}</h1>
      <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
    </div>

    <nav class="nav-links">
      <router-link to="/" active-class="active" exact-active-class="active">
        {{ t('nav.overview') }}
      </router-link>
      <router-link to="/inventory" active-class="active">
        {{ t('nav.inventory') }}
      </router-link>
      <router-link to="/orders" active-class="active">
        {{ t('nav.orders') }}
      </router-link>
      <router-link to="/spending" active-class="active">
        {{ t('nav.finance') }}
      </router-link>
      <router-link to="/demand" active-class="active">
        {{ t('nav.demandForecast') }}
      </router-link>
      <router-link to="/restocking" active-class="active">
        {{ t('nav.restocking') }}
      </router-link>
      <router-link to="/reports" active-class="active">
        {{ t('nav.reports') }}
      </router-link>
    </nav>
  </aside>
</template>

<script setup>
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  height: 100vh;
  position: sticky;
  top: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.brand {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-6) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.brand-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.025em;
}

.brand-subtitle {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-weight: 400;
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4);
}

.nav-links a {
  padding: var(--space-3) var(--space-4);
  color: var(--color-text-secondary);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.nav-links a:hover {
  color: var(--color-text-primary);
  background: #f1f5f9;
}

.nav-links a.active {
  color: var(--color-accent);
  background: var(--color-accent-subtle);
}
</style>
