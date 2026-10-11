<template>
  <div class="history-container" :class="{ 'dark-mode': isDarkMode }">
    <div class="header">
      <h2>Processing History</h2>
      <div class="filters">
        <select v-model="filterStatus" class="select">
          <option value="">All Status</option>
          <option value="completed">Completed</option>
          <option value="processing">Processing</option>
          <option value="failed">Failed</option>
        </select>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search..."
          class="search-input"
        />
      </div>
    </div>

    <div v-if="filteredJobs.length === 0" class="empty-state">
      <p>No processing history found</p>
    </div>

    <div v-else class="jobs-grid">
      <div
        v-for="job in filteredJobs"
        :key="job.id || job.job_id"
        class="job-item"
        :class="{ active: isCurrentJob(job) }"
        @click="selectJob(job)"
      >
        <div class="job-title">
          {{ job.type === 'file' ? job.fileName : 'Text Article' }}
        </div>
        <div class="job-meta">
          <span class="status-badge" :class="job.status">{{ job.status }}</span>
          <span class="date">{{ formatDate(job.timestamp) }}</span>
        </div>
        <div class="job-stats">
          <span>{{ job.questions?.length || 0 }} Q&A</span>
        </div>
        <div class="job-actions">
          <button 
            class="btn-small download" 
            @click.stop="downloadJob(job)"
            title="Download as JSON"
          >
            ⬇
          </button>
          <button 
            class="btn-small delete" 
            @click.stop="deleteJob(job)"
            title="Delete"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()
const isDarkMode = computed(() => store.isDarkMode)
const jobs = computed(() => store.jobs)

const filterStatus = ref('')
const searchQuery = ref('')

const filteredJobs = computed(() => {
  return jobs.value.filter(job => {
    const matchStatus = !filterStatus.value || job.status === filterStatus.value
    const matchSearch = !searchQuery.value || 
      (job.source?.toLowerCase().includes(searchQuery.value.toLowerCase())) ||
      (job.fileName?.toLowerCase().includes(searchQuery.value.toLowerCase()))
    return matchStatus && matchSearch
  }).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
})

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const isCurrentJob = (job) => {
  return store.currentJob?.job_id === (job.id || job.job_id)
}

const selectJob = (job) => {
  store.currentJob = job
}

const downloadJob = (job) => {
  const data = {
    job_id: job.job_id || job.id,
    timestamp: job.timestamp,
    source: job.source,
    fileName: job.fileName,
    questions: job.questions
  }
  
  const jsonStr = JSON.stringify(data, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `qa-results-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const deleteJob = (job) => {
  if (confirm('Are you sure you want to delete this job?')) {
    const index = store.jobs.findIndex(j => (j.id || j.job_id) === (job.id || job.job_id))
    if (index !== -1) {
      store.jobs.splice(index, 1)
      localStorage.setItem('jobs', JSON.stringify(store.jobs))
      if (isCurrentJob(job)) {
        store.currentJob = null
      }
    }
  }
}
</script>

<style scoped>
.history-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: background 0.3s ease;
}

.history-container.dark-mode {
  background: #1e293b;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.header {
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.header h2 {
  margin: 0;
  color: #1e293b;
}

.history-container.dark-mode .header h2 {
  color: #e2e8f0;
}

.filters {
  display: flex;
  gap: 1rem;
}

.select,
.search-input {
  padding: 0.5rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.9rem;
}

.history-container.dark-mode .select,
.history-container.dark-mode .search-input {
  background: #0f172a;
  border-color: #334155;
  color: #e2e8f0;
}

.select:focus,
.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #94a3b8;
}

.jobs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.job-item {
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.history-container.dark-mode .job-item {
  background: #0f172a;
  border-color: #334155;
}

.job-item:hover,
.job-item.active {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.history-container.dark-mode .job-item.active {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.job-title {
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-container.dark-mode .job-title {
  color: #e2e8f0;
}

.job-meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.65rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.completed {
  background: #dbeafe;
  color: #0c4a6e;
}

.status-badge.processing {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.failed {
  background: #fee2e2;
  color: #7c2d12;
}

.history-container.dark-mode .status-badge.completed {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
}

.history-container.dark-mode .status-badge.processing {
  background: rgba(251, 146, 60, 0.2);
  color: #fed7aa;
}

.history-container.dark-mode .status-badge.failed {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.date {
  font-size: 0.8rem;
  color: #94a3b8;
}

.job-stats {
  font-size: 0.85rem;
  color: #667eea;
  font-weight: 500;
}

.job-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.btn-small {
  background: #e0e7ff;
  border: none;
  color: #3730a3;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-container.dark-mode .btn-small {
  background: #334155;
  color: #cbd5e1;
}

.btn-small:hover {
  background: #667eea;
  color: white;
}

.btn-small.delete:hover {
  background: #ef4444;
}

@media (max-width: 768px) {
  .history-container {
    padding: 1.5rem;
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
  }

  .filters {
    width: 100%;
    flex-direction: column;
  }

  .select,
  .search-input {
    width: 100%;
  }

  .jobs-grid {
    grid-template-columns: 1fr;
  }
}
</style>
