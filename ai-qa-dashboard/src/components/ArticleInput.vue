<template>
  <div class="article-input" :class="{ 'dark-mode': isDarkMode }">
    <div class="input-container">
      <!-- Tabs -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab"
          class="tab-button"
          :class="{ active: activeTab === tab }"
          @click="activeTab = tab"
        >
          {{ tab.charAt(0).toUpperCase() + tab.slice(1) }}
        </button>
      </div>

      <!-- Text Input Tab -->
      <div v-if="activeTab === 'text'" class="tab-content">
        <textarea
          v-model="articleText"
          placeholder="Paste your article text here... (minimum 100 characters)"
          class="textarea"
          rows="8"
        ></textarea>
        <p class="char-count">
          {{ articleText.length }} characters
        </p>
      </div>

      <!-- File Upload Tab -->
      <div v-if="activeTab === 'file'" class="tab-content">
        <div class="file-upload" @dragover.prevent @drop.prevent="handleFileDrop">
          <input
            ref="fileInput"
            type="file"
            accept=".txt,.pdf,.docx"
            class="file-input"
            @change="handleFileSelect"
          />
          <div v-if="!selectedFile" class="upload-prompt">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <p>Drag and drop your file here</p>
            <p class="secondary">or click to browse</p>
            <button class="browse-btn" @click="$refs.fileInput?.click()">
              Browse Files
            </button>
          </div>
          <div v-else class="file-selected">
            <p class="file-name">{{ selectedFile.name }}</p>
            <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
            <button class="remove-btn" @click="selectedFile = null">
              Remove
            </button>
          </div>
        </div>
      </div>

      <!-- URL Input Tab -->
      <div v-if="activeTab === 'url'" class="tab-content">
        <input
          v-model="articleUrl"
          type="url"
          placeholder="Enter article URL..."
          class="input"
        />
        <p class="info">Coming soon: URL scraping feature</p>
      </div>

      <!-- Options -->
      <div class="options">
        <div class="option-group">
          <label for="question-count">Number of Questions:</label>
          <div class="slider-container">
            <input
              id="question-count"
              v-model.number="questionCount"
              type="range"
              min="1"
              max="20"
              class="slider"
            />
            <input
              v-model.number="questionCount"
              type="number"
              min="1"
              max="20"
              class="input-number"
            />
          </div>
        </div>

        <div class="option-group">
          <label for="mode">Generation Mode:</label>
          <select v-model="mode" id="mode" class="select">
            <option value="simple">Simple</option>
            <option value="in_depth">In-Depth</option>
            <option value="faq">FAQ</option>
          </select>
        </div>
      </div>

      <!-- Submit Button -->
      <button
        class="submit-btn"
        @click="handleSubmit"
        :disabled="isLoading || !isFormValid"
      >
        <span v-if="!isLoading">Generate Q&A</span>
        <span v-else class="loading">
          <span class="spinner"></span>
          Generating...
        </span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/appStore'

const store = useAppStore()
const isDarkMode = computed(() => store.isDarkMode)
const isLoading = computed(() => store.isLoading)

const activeTab = ref('text')
const tabs = ['text', 'file', 'url']
const articleText = ref('')
const articleUrl = ref('')
const selectedFile = ref(null)
const fileInput = ref(null)
const questionCount = ref(5)
const mode = ref('simple')

const isFormValid = computed(() => {
  if (activeTab.value === 'text') {
    return articleText.value.length >= 100
  } else if (activeTab.value === 'file') {
    return selectedFile.value !== null
  }
  return false
})

const handleFileSelect = (event) => {
  const files = event.target.files
  if (files && files[0]) {
    selectedFile.value = files[0]
  }
}

const handleFileDrop = (event) => {
  const files = event.dataTransfer.files
  if (files && files[0]) {
    selectedFile.value = files[0]
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const handleSubmit = async () => {
  try {
    if (activeTab.value === 'text') {
      await store.processArticleText(articleText.value, questionCount.value)
      articleText.value = ''
    } else if (activeTab.value === 'file') {
      await store.uploadArticleFile(selectedFile.value, questionCount.value)
      selectedFile.value = null
    }
  } catch (error) {
    console.error('Error:', error)
  }
}
</script>

<style scoped>
.article-input {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: background 0.3s ease;
}

.article-input.dark-mode {
  background: #1e293b;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 1rem;
  border-bottom: 2px solid #e2e8f0;
}

.article-input.dark-mode .tabs {
  border-bottom-color: #334155;
}

.tab-button {
  background: none;
  border: none;
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  color: #64748b;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
}

.article-input.dark-mode .tab-button {
  color: #94a3b8;
}

.tab-button.active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.tab-button:hover {
  color: #667eea;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Textarea */
.textarea {
  width: 100%;
  padding: 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.95rem;
  resize: vertical;
  transition: border-color 0.3s ease;
}

.article-input.dark-mode .textarea {
  background: #0f172a;
  border-color: #334155;
  color: #e2e8f0;
}

.textarea:focus {
  outline: none;
  border-color: #667eea;
}

.char-count {
  font-size: 0.85rem;
  color: #94a3b8;
  margin: 0;
}

/* File Upload */
.file-upload {
  border: 2px dashed #cbd5e1;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.article-input.dark-mode .file-upload {
  border-color: #334155;
}

.file-upload:hover {
  border-color: #667eea;
  background: #f0f4ff;
}

.article-input.dark-mode .file-upload:hover {
  background: rgba(102, 126, 234, 0.1);
}

.file-input {
  display: none;
}

.upload-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.upload-prompt svg {
  color: #94a3b8;
}

.upload-prompt p {
  margin: 0;
  font-weight: 500;
}

.upload-prompt .secondary {
  font-size: 0.9rem;
  color: #94a3b8;
  font-weight: 400;
}

.browse-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.3s ease;
}

.browse-btn:hover {
  background: #764ba2;
}

.file-selected {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: center;
}

.file-name {
  font-weight: 600;
  margin: 0;
}

.article-input.dark-mode .file-name {
  color: #e2e8f0;
}

.file-size {
  font-size: 0.85rem;
  color: #94a3b8;
  margin: 0;
}

.remove-btn {
  background: #ef4444;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background 0.3s ease;
}

.remove-btn:hover {
  background: #dc2626;
}

/* Input */
.input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: border-color 0.3s ease;
}

.article-input.dark-mode .input {
  background: #0f172a;
  border-color: #334155;
  color: #e2e8f0;
}

.input:focus {
  outline: none;
  border-color: #667eea;
}

.info {
  font-size: 0.85rem;
  color: #94a3b8;
  margin: 0;
}

/* Options */
.options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.option-group label {
  font-weight: 500;
  color: #1e293b;
}

.article-input.dark-mode .option-group label {
  color: #e2e8f0;
}

.slider-container {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.slider {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: #e2e8f0;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.article-input.dark-mode .slider {
  background: #334155;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  transition: background 0.3s ease;
}

.slider::-webkit-slider-thumb:hover {
  background: #764ba2;
}

.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #667eea;
  cursor: pointer;
  border: none;
  transition: background 0.3s ease;
}

.slider::-moz-range-thumb:hover {
  background: #764ba2;
}

.input-number {
  width: 60px;
  padding: 0.4rem 0.6rem;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  text-align: center;
  font-size: 0.9rem;
}

.article-input.dark-mode .input-number {
  background: #0f172a;
  border-color: #334155;
  color: #e2e8f0;
}

.input-number:focus {
  outline: none;
  border-color: #667eea;
}

.select {
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: border-color 0.3s ease;
}

.article-input.dark-mode .select {
  background: #0f172a;
  border-color: #334155;
  color: #e2e8f0;
}

.select:focus {
  outline: none;
  border-color: #667eea;
}

/* Submit Button */
.submit-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .article-input {
    padding: 1.5rem;
  }

  .options {
    grid-template-columns: 1fr;
  }
}
</style>
