<template>
  <div class="results-container" :class="{ 'dark-mode': isDarkMode }">
    <div v-if="!currentJob" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z"></path>
      </svg>
      <p>Generate Q&A pairs to see results here</p>
    </div>

    <div v-else>
      <!-- Generated Q&A Summary -->
      <div class="qa-summary">
        <div>
          <h3>Generated Q&A</h3>
          <p id="qa-count" class="qa-count">{{ totalQuestions }} questions generated</p>
          <p class="qa-confidence">Overview · {{ avgConfidence.toFixed(0) }}% confidence</p>
        </div>
        <div class="qa-actions-summary">
          <button class="btn-add" @click="addNewQuestion">+ Add Question</button>
        </div>
      </div>

      <!-- Job Header -->
      <div class="job-header">
        <div>
          <h2>{{ currentJob.type === 'text' ? 'Text Article' : currentJob.fileName }}</h2>
          <p class="job-info">
            <span class="badge" :class="currentJob.status">{{ currentJob.status }}</span>
            <span class="timestamp">{{ formatDate(currentJob.timestamp) }}</span>
          </p>
        </div>
        <div class="header-actions">
          <button class="action-btn export" @click="exportResults" title="Export as JSON">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
              <polyline points="17 21 17 13 7 13 7 21"></polyline>
              <polyline points="7 3 7 8 15 8"></polyline>
            </svg>
          </button>
          <button class="action-btn copy" @click="copyToClipboard" title="Copy all Q&A">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
              <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
            </svg>
          </button>
        </div>
      </div>

      <!-- Statistics -->
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-label">Total Questions</span>
          <span class="stat-value">{{ currentJob.questions?.length || 0 }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Avg Confidence</span>
          <span class="stat-value">
            {{ currentJob.questions?.length > 0 
              ? (currentJob.questions.reduce((sum, q) => sum + (q.confidence || 0.85), 0) / currentJob.questions.length * 100).toFixed(1)
              : 0
            }}%
          </span>
        </div>
      </div>

      <!-- Q&A List -->
      <div class="qa-list">
        <div
          v-for="(qa, index) in currentJob.questions || []"
          :key="index"
          class="qa-card"
        >
          <div class="qa-header">
            <span class="qa-number">Q{{ index + 1 }}</span>
            <span class="confidence-badge">
              {{ ((qa.confidence ?? 0.85) * 100).toFixed(0) }}% confidence
            </span>
          </div>
          <div class="qa-content">
            <p class="question">{{ qa.question }}</p>
            <p class="answer">{{ qa.answer }}</p>
          </div>
          <div class="qa-actions">
            <button class="action-link" @click="copyQA(qa)">Copy</button>
            <span class="separator">•</span>
            <button class="action-link" @click="editQA(index)">Edit</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="editingIndex !== null" class="modal-overlay" @click="editingIndex = null">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>Edit Q&A</h3>
          <button class="close-btn" @click="editingIndex = null">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Question:</label>
            <textarea v-model="editedQA.question" rows="2"></textarea>
          </div>
          <div class="form-group">
            <label>Answer:</label>
            <textarea v-model="editedQA.answer" rows="3"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="editingIndex = null">Cancel</button>
          <button class="btn-save" @click="saveEdit">Save Changes</button>
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
const currentJob = computed(() => store.currentJob)

const editingIndex = ref(null)
const editedQA = ref({})

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString()
}

const exportResults = () => {
  if (!currentJob.value) return
  
  const data = {
    job_id: currentJob.value.job_id,
    timestamp: currentJob.value.timestamp,
    source: currentJob.value.source,
    questions: currentJob.value.questions
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

const copyToClipboard = async () => {
  if (!currentJob.value?.questions) return
  
  const text = currentJob.value.questions
    .map((q, i) => `Q${i + 1}: ${q.question}\nA: ${q.answer}`)
    .join('\n\n')
  
  try {
    await navigator.clipboard.writeText(text)
    store.setSuccess('Copied to clipboard!')
    setTimeout(() => store.clearSuccess(), 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

const totalQuestions = computed(() => currentJob.value?.questions?.length || 0)
const avgConfidence = computed(() => {
  const questions = currentJob.value?.questions || []
  if (!questions.length) return 0
  const sum = questions.reduce((acc, q) => acc + (q.confidence ?? 0.85), 0)
  return (sum / questions.length) * 100
})

const addNewQuestion = () => {
  if (!currentJob.value) return
  if (!Array.isArray(currentJob.value.questions)) {
    currentJob.value.questions = []
  }
  currentJob.value.questions.push({
    question: 'New question',
    answer: 'Add answer',
    confidence: 0.5
  })
  store.setSuccess('Question added. Edit as needed.')
  setTimeout(() => store.clearSuccess(), 2000)
}

const copyQA = async (qa) => {
  const text = `Q: ${qa.question}\nA: ${qa.answer}`
  try {
    await navigator.clipboard.writeText(text)
    store.setSuccess('Q&A copied to clipboard!')
    setTimeout(() => store.clearSuccess(), 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

const editQA = (index) => {
  editingIndex.value = index
  editedQA.value = {
    question: currentJob.value.questions[index].question,
    answer: currentJob.value.questions[index].answer
  }
}

const saveEdit = () => {
  if (editingIndex.value !== null) {
    currentJob.value.questions[editingIndex.value] = {
      ...currentJob.value.questions[editingIndex.value],
      ...editedQA.value
    }
    editingIndex.value = null
  }
}
</script>

<style scoped>
.results-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: background 0.3s ease;
}

.results-container.dark-mode {
  background: #1e293b;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #94a3b8;
}

.empty-state svg {
  opacity: 0.3;
  margin-bottom: 1rem;
}

.empty-state p {
  font-size: 1.1rem;
  margin: 0;
}

/* Generated Q&A Summary */
.qa-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  background: #f8fafc;
}
.qa-summary h3 {
  margin: 0;
  font-size: 1.1rem;
}
.qa-count {
  margin: 0.25rem 0;
  font-weight: 700;
}
.qa-confidence {
  margin: 0;
  color: #475569;
  font-size: 0.9rem;
}
.qa-actions-summary .btn-add {
  background: #0ea5e9;
  color: #fff;
  border: none;
  padding: 0.55rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease;
}
.qa-actions-summary .btn-add:hover {
  background: #0284c7;
}

/* Job Header */
.job-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #e2e8f0;
}

.results-container.dark-mode .job-header {
  border-bottom-color: #334155;
}

.job-header h2 {
  margin: 0 0 0.5rem 0;
  color: #1e293b;
}

.results-container.dark-mode .job-header h2 {
  color: #e2e8f0;
}

.job-info {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin: 0;
  font-size: 0.9rem;
}

.badge {
  display: inline-block;
  padding: 0.3rem 0.8rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge.completed {
  background: #dbeafe;
  color: #0c4a6e;
}

.results-container.dark-mode .badge.completed {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
}

.badge.processing {
  background: #fef3c7;
  color: #92400e;
}

.timestamp {
  color: #94a3b8;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  background: #f1f5f9;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  transition: all 0.3s ease;
}

.results-container.dark-mode .action-btn {
  background: #334155;
  color: #cbd5e1;
}

.action-btn:hover {
  background: #667eea;
  color: white;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: #f0f4ff;
  padding: 1.5rem;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.results-container.dark-mode .stat-card {
  background: #0f172a;
}

.stat-label {
  font-size: 0.9rem;
  color: #64748b;
  font-weight: 500;
}

.results-container.dark-mode .stat-label {
  color: #94a3b8;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #667eea;
}

/* Q&A List */
.qa-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.qa-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.results-container.dark-mode .qa-card {
  background: #0f172a;
  border-color: #334155;
}

.qa-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.results-container.dark-mode .qa-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.qa-number {
  font-weight: 700;
  color: #667eea;
  font-size: 0.95rem;
}

.confidence-badge {
  background: #e0e7ff;
  color: #3730a3;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.results-container.dark-mode .confidence-badge {
  background: rgba(102, 126, 234, 0.2);
  color: #a5b4fc;
}

.qa-content {
  margin-bottom: 1rem;
}

.question {
  margin: 0 0 0.75rem 0;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.5;
}

.results-container.dark-mode .question {
  color: #e2e8f0;
}

.answer {
  margin: 0;
  color: #475569;
  line-height: 1.6;
}

.results-container.dark-mode .answer {
  color: #cbd5e1;
}

.qa-actions {
  display: flex;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.action-link {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  padding: 0;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.action-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

.separator {
  color: #cbd5e1;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  width: 90%;
  max-width: 500px;
}

.results-container.dark-mode .modal {
  background: #1e293b;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.results-container.dark-mode .modal-header {
  border-bottom-color: #334155;
}

.modal-header h3 {
  margin: 0;
  color: #1e293b;
}

.results-container.dark-mode .modal-header h3 {
  color: #e2e8f0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #94a3b8;
}

.modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  color: #1e293b;
}

.results-container.dark-mode .form-group label {
  color: #e2e8f0;
}

.form-group textarea {
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  font-family: inherit;
  resize: vertical;
}

.results-container.dark-mode .form-group textarea {
  background: #0f172a;
  border-color: #334155;
  color: #e2e8f0;
}

.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.results-container.dark-mode .modal-footer {
  border-top-color: #334155;
}

.btn-cancel,
.btn-save {
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-cancel {
  background: #f1f5f9;
  color: #1e293b;
}

.results-container.dark-mode .btn-cancel {
  background: #334155;
  color: #e2e8f0;
}

.btn-save {
  background: #667eea;
  color: white;
}

.btn-save:hover {
  background: #764ba2;
}

@media (max-width: 768px) {
  .results-container {
    padding: 1.5rem;
  }

  .job-header {
    flex-direction: column;
    gap: 1rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .qa-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>
