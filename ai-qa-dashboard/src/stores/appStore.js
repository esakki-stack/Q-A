import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { qaService } from '@/services/qaService'

const safeLocalStorageGet = (key, fallback = null) => {
  try {
    return localStorage.getItem(key) ?? fallback
  } catch {
    return fallback
  }
}

export const useAppStore = defineStore('app', () => {
  // State
  const isDarkMode = ref(safeLocalStorageGet('darkMode', 'false') === 'true')
  const jobs = ref([])
  const currentJob = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  const successMessage = ref(null)

  // Computed
  const recentJobs = computed(() => jobs.value.slice(-10).reverse())
  const completedJobs = computed(() => jobs.value.filter(j => j.status === 'completed'))
  const processingJobs = computed(() => jobs.value.filter(j => j.status === 'processing'))

  // Actions
  const toggleDarkMode = () => {
    isDarkMode.value = !isDarkMode.value
    try {
      localStorage.setItem('darkMode', String(isDarkMode.value))
    } catch {
      // ignore storage access issues
    }
  }

  const addJob = (job) => {
    jobs.value.push(job)
    currentJob.value = job
    try {
      localStorage.setItem('jobs', JSON.stringify(jobs.value))
    } catch {
      // ignore storage access issues
    }
  }

  const updateJob = (jobId, updates) => {
    const index = jobs.value.findIndex(j => j.id === jobId || j.job_id === jobId)
    if (index !== -1) {
      jobs.value[index] = { ...jobs.value[index], ...updates }
      if (currentJob.value?.job_id === jobId) {
        currentJob.value = jobs.value[index]
      }
      try {
        localStorage.setItem('jobs', JSON.stringify(jobs.value))
      } catch {
        // ignore storage access issues
      }
    }
  }

  const setLoading = (value) => {
    isLoading.value = value
  }

  const setError = (msg) => {
    error.value = msg
    successMessage.value = null
  }

  const setSuccess = (msg) => {
    successMessage.value = msg
    error.value = null
  }

  const clearMessages = () => {
    error.value = null
    successMessage.value = null
  }

  const loadJobsFromStorage = () => {
    const stored = safeLocalStorageGet('jobs')
    if (stored) {
      try {
        const parsedJobs = JSON.parse(stored)
        jobs.value = Array.isArray(parsedJobs) ? parsedJobs : []
        if (jobs.value.length > 0) {
          // Keep the latest job selected as output context
          currentJob.value = jobs.value[jobs.value.length - 1]
        }
      } catch (err) {
        console.error('Failed to parse jobs from localStorage:', err)
        jobs.value = []
        currentJob.value = null
      }
    }
  }

  const processArticleText = async (text, questionCount) => {
    setLoading(true)
    clearMessages()
    
    try {
      const result = await qaService.processArticle(text, questionCount)
      addJob({
        id: result.job_id,
        job_id: result.job_id,
        type: 'text',
        status: result.status || 'completed',
        questions: result.questions || [],
        source: text.substring(0, 100) + '...',
        timestamp: new Date().toISOString(),
        articleText: text,
        questionCount
      })
      setSuccess('Q&A generation completed successfully!')
      return result
    } catch (err) {
      setError(err.message || 'Failed to generate Q&A')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const uploadArticleFile = async (file, questionCount) => {
    setLoading(true)
    clearMessages()
    
    try {
      const result = await qaService.uploadFile(file, questionCount)
      addJob({
        id: result.job_id,
        job_id: result.job_id,
        type: 'file',
        fileName: file.name,
        status: result.status || 'completed',
        questions: result.questions || [],
        source: file.name,
        timestamp: new Date().toISOString(),
        questionCount
      })
      setSuccess('Article processed successfully!')
      return result
    } catch (err) {
      setError(err.message || 'Failed to upload and process file')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const checkJobStatus = async (jobId) => {
    try {
      const result = await qaService.getStatus(jobId)
      updateJob(jobId, {
        status: result.status,
        questions: result.questions || []
      })
      return result
    } catch (err) {
      setError(err.message || 'Failed to check job status')
      throw err
    }
  }

  const clearError = () => {
    error.value = null
  }

  const clearSuccess = () => {
    successMessage.value = null
  }

  return {
    isDarkMode,
    jobs,
    currentJob,
    isLoading,
    error,
    successMessage,
    recentJobs,
    completedJobs,
    processingJobs,
    toggleDarkMode,
    addJob,
    updateJob,
    setLoading,
    setError,
    setSuccess,
    clearMessages,
    loadJobsFromStorage,
    processArticleText,
    uploadArticleFile,
    checkJobStatus,
    clearError,
    clearSuccess
  }
})
