<template>
  <div id="app" :class="{ 'dark-mode': isDarkMode }">
    <Header></Header>

    <!-- Alert Messages -->
    <div v-if="errorMessage" class="alert alert-error">
      <div class="alert-content">
        <span>{{ errorMessage }}</span>
        <button @click="clearError" class="alert-close">✕</button>
      </div>
    </div>
    <div v-if="successMessage" class="alert alert-success">
      <div class="alert-content">
        <span>{{ successMessage }}</span>
        <button @click="clearSuccess" class="alert-close">✕</button>
      </div>
    </div>

    <!-- Main Content -->
    <main class="main-container">
      <div class="container">
        <!-- Dashboard -->
        <template v-if="!showGenerator && !showHistory">
          <Dashboard @selectJob="selectJob"></Dashboard>
        </template>

        <!-- Generator -->
        <template v-else-if="showGenerator">
          <div class="page-grid">
            <div class="input-section">
              <ArticleInput></ArticleInput>
            </div>
            <div class="results-section">
              <ResultsDisplay></ResultsDisplay>
            </div>
          </div>
        </template>

        <!-- History -->
        <template v-else-if="showHistory">
          <History></History>
        </template>
      </div>
    </main>

    <!-- Footer -->
    <footer class="footer">
      <p>&copy; 2024 NEXUS QA Generator. All rights reserved.</p>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import Header from '@/components/Header.vue'
import ArticleInput from '@/components/ArticleInput.vue'
import ResultsDisplay from '@/components/ResultsDisplay.vue'
import Dashboard from '@/components/Dashboard.vue'
import History from '@/components/History.vue'

const store = useAppStore()
const isDarkMode = computed(() => store.isDarkMode)
const errorMessage = computed(() => store.error)
const successMessage = computed(() => store.successMessage)

const showGenerator = ref(true)
const showHistory = ref(false)

const setView = (view) => {
  showGenerator.value = view === 'generator'
  showHistory.value = view === 'history'
}

const handleNavigation = () => {
  const hash = window.location.hash.slice(1)
  if (hash === '/history') {
    setView('history')
  } else {
    setView('generator')
  }
}

onMounted(() => {
  // Load jobs from localStorage
  store.loadJobsFromStorage()

  // Check backend health
  checkBackendHealth()

  // Parse hash-based URL and listen to hash changes
  window.addEventListener('hashchange', handleNavigation)
  handleNavigation()

  // Apply dark mode
  applyDarkMode()
})

const clearError = () => store.clearError()
const clearSuccess = () => store.clearSuccess()

const checkBackendHealth = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/health')
    if (!response.ok) {
      store.setError('Warning: Backend server may not be responding')
    }
  } catch (err) {
    store.setError('Warning: Cannot connect to backend. Make sure the server is running.')
  }
}

const applyDarkMode = () => {
  document.documentElement.style.colorScheme = isDarkMode.value ? 'dark' : 'light'
}

const selectJob = (job) => {
  store.currentJob = job
  window.location.hash = '#/generator'
  setView('generator')
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: white;
  color: #1e293b;
  transition: background 0.3s ease, color 0.3s ease;
}

html.dark-mode, body.dark-mode {
  background: #0f172a;
  color: #e2e8f0;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

#app.dark-mode {
  background: #0f172a;
  color: #e2e8f0;
}

/* Alerts */
.alert {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  max-width: 90%;
  z-index: 999;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.alert-error {
  background: #fee2e2;
  color: #991b1b;
}

#app.dark-mode .alert-error {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.alert-success {
  background: #dcfce7;
  color: #166534;
}

#app.dark-mode .alert-success {
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
}

.alert-content {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.alert-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 0;
}

/* Main Content */
.main-container {
  flex: 1;
  padding: 2rem 0;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 1rem;
}

.page-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.input-section,
.results-section {
  min-height: 400px;
}

/* Footer */
.footer {
  text-align: center;
  padding: 2rem;
  color: #94a3b8;
  border-top: 1px solid #e2e8f0;
  margin-top: 2rem;
}

#app.dark-mode .footer {
  border-top-color: #334155;
}

.footer p {
  margin: 0;
  font-size: 0.9rem;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .main-container {
    padding: 1.5rem 0;
  }

  .page-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .input-section,
  .results-section {
    min-height: 300px;
  }
}

@media (max-width: 768px) {
  .main-container {
    padding: 1rem 0;
  }

  .container {
    padding: 0 1rem;
  }

  .alert {
    top: 70px;
    max-width: calc(100% - 2rem);
  }

  .footer {
    padding: 1.5rem;
    margin-top: 1rem;
  }
}
</style>
