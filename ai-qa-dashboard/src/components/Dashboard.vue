<template>
  <div class="dashboard-container" :class="{ 'dark-mode': isDarkMode }">
    <div class="dashboard-header">
      <h2>Dashboard</h2>
    </div>

    <!-- Stats Overview -->
    <div class="stats-overview">
      <div class="stat-box">
        <div class="stat-icon processing">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
        </div>
        <div class="stat-info">
          <p class="stat-label">Total Jobs</p>
          <p class="stat-number">{{ jobs.length }}</p>
        </div>
      </div>

      <div class="stat-box">
        <div class="stat-icon success">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
        <div class="stat-info">
          <p class="stat-label">Completed</p>
          <p class="stat-number">{{ completedJobs.length }}</p>
        </div>
      </div>

      <div class="stat-box">
        <div class="stat-icon pending">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
        </div>
        <div class="stat-info">
          <p class="stat-label">Processing</p>
          <p class="stat-number">{{ processingJobs.length }}</p>
        </div>
      </div>

      <div class="stat-box">
        <div class="stat-icon questions">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 16v-4"></path>
            <path d="M12 8h.01"></path>
          </svg>
        </div>
        <div class="stat-info">
          <p class="stat-label">Total Q&A Generated</p>
          <p class="stat-number">{{ totalQAGenerated }}</p>
        </div>
      </div>
    </div>

    <!-- Recent Jobs -->
    <div class="recent-jobs">
      <h3>Recent Jobs</h3>
      <div v-if="recentJobs.length === 0" class="empty">
        <p>No jobs yet. Start by generating Q&A from an article!</p>
      </div>
      <div v-else class="jobs-list">
        <div
          v-for="job in recentJobs"
          :key="job.id || job.job_id"
          class="job-row"
          @click="$emit('selectJob', job)"
        >
          <div class="job-info">
            <p class="job-name">{{ job.type === 'file' ? job.fileName : 'Text Article' }}</p>
            <p class="job-time">{{ formatDate(job.timestamp) }}</p>
          </div>
          <div class="job-result">
            <span class="badge" :class="job.status">{{ job.status }}</span>
            <span class="qa-count">{{ job.questions?.length || 0 }} Q&A</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <h3>Quick Actions</h3>
      <div class="actions-grid">
        <button class="action-card" @click="goToGenerator()">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>New Generation</span>
        </button>
        <button class="action-card" @click="clearHistory">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 4 21 4 23 6 23 20 1 20 1 6"></polyline>
            <line x1="10" y1="11" x2="10" y2="17"></line>
            <line x1="14" y1="11" x2="14" y2="17"></line>
            <line x1="5" y1="4" x2="19" y2="4"></line>
          </svg>
          <span>Clear History</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()
const isDarkMode = computed(() => store.isDarkMode)
const jobs = computed(() => store.jobs)
const completedJobs = computed(() => store.completedJobs)
const processingJobs = computed(() => store.processingJobs)
const recentJobs = computed(() => store.recentJobs)

const totalQAGenerated = computed(() => {
  return jobs.value.reduce((sum, job) => sum + (job.questions?.length || 0), 0)
})

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const clearHistory = () => {
  if (confirm('Are you sure you want to clear all history? This cannot be undone.')) {
    store.jobs = []
    localStorage.removeItem('jobs')
    store.currentJob = null
    store.setSuccess('History cleared')
  }
}

const goToGenerator = () => {
  window.location.hash = '#/generator'
}

defineEmits(['selectJob'])
</script>

<style scoped>
.dashboard-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: background 0.3s ease;
}

.dashboard-container.dark-mode {
  background: #1e293b;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.dashboard-header h2 {
  margin: 0 0 2rem 0;
  color: #1e293b;
}

.dashboard-container.dark-mode .dashboard-header h2 {
  color: #e2e8f0;
}

/* Stats Overview */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-box {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 10px;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
  transition: transform 0.3s ease;
}

.stat-box:hover {
  transform: translateY(-4px);
}

.dashboard-container.dark-mode .stat-box {
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
}

.stat-icon.success {
  background: rgba(34, 197, 94, 0.2);
}

.stat-icon.pending {
  background: rgba(251, 146, 60, 0.2);
}

.stat-icon.questions {
  background: rgba(59, 130, 246, 0.2);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat-label {
  margin: 0;
  font-size: 0.85rem;
  opacity: 0.9;
  font-weight: 500;
}

.stat-number {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
}

/* Recent Jobs */
.recent-jobs,
.quick-actions {
  margin-bottom: 2rem;
}

.recent-jobs h3,
.quick-actions h3 {
  margin: 0 0 1rem 0;
  color: #1e293b;
}

.dashboard-container.dark-mode .recent-jobs h3,
.dashboard-container.dark-mode .quick-actions h3 {
  color: #e2e8f0;
}

.empty {
  padding: 2rem 1rem;
  text-align: center;
  color: #94a3b8;
}

.jobs-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.job-row {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.dashboard-container.dark-mode .job-row {
  background: #0f172a;
}

.job-row:hover {
  background: #f1f5f9;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.dashboard-container.dark-mode .job-row:hover {
  background: #1e293b;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.job-info {
  flex: 1;
}

.job-name {
  margin: 0 0 0.25rem 0;
  forward-weight: 600;
  color: #1e293b;
}

.dashboard-container.dark-mode .job-name {
  color: #e2e8f0;
}

.job-time {
  margin: 0;
  font-size: 0.85rem;
  color: #94a3b8;
}

.job-result {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge.completed {
  background: #dbeafe;
  color: #0c4a6e;
}

.badge.processing {
  background: #fef3c7;
  color: #92400e;
}

.dashboard-container.dark-mode .badge.completed {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
}

.dashboard-container.dark-mode .badge.processing {
  background: rgba(251, 146, 60, 0.2);
  color: #fed7aa;
}

.qa-count {
  font-size: 0.9rem;
  color: #667eea;
  font-weight: 500;
}

/* Quick Actions */
.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.action-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1.5rem;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 1.5rem;
  }

  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }

  .stat-box {
    padding: 1rem;
  }

  .stat-number {
    font-size: 1.5rem;
  }

  .job-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .job-result {
    width: 100%;
    justify-content: space-between;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
