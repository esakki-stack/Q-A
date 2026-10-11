import api from './api'

export const qaService = {
  /**
   * Generate Q&A pairs from article text
   */
  async processArticle(text, questionCount = 5) {
    try {
      const response = await api.post('/process', null, {
        params: {
          text,
          question_count: questionCount
        }
      })
      return response.data
    } catch (error) {
      throw this._handleError(error)
    }
  },

  /**
   * Upload file and generate Q&A
   */
  async uploadFile(file, questionCount = 5) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post('/upload', formData, {
        params: {
          question_count: questionCount
        },
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } catch (error) {
      throw this._handleError(error)
    }
  },

  /**
   * Check processing status
   */
  async getStatus(jobId) {
    try {
      const response = await api.get(`/status/${jobId}`)
      return response.data
    } catch (error) {
      throw this._handleError(error)
    }
  },

  /**
   * Health check
   */
  async checkHealth() {
    try {
      const response = await api.get('/health')
      return response.data
    } catch (error) {
      throw this._handleError(error)
    }
  },

  /**
   * Error handling
   */
  _handleError(error) {
    if (error.response) {
      return {
        status: error.response.status,
        message: error.response.data?.detail || error.response.statusText || 'Unknown error',
        data: error.response.data
      }
    } else if (error.request) {
      return {
        status: 0,
        message: 'No response from server. Please check your connection.',
        data: null
      }
    } else {
      return {
        status: -1,
        message: error.message || 'Unknown error occurred',
        data: null
      }
    }
  }
}
