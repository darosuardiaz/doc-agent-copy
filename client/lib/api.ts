// API service functions for backend communication
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new ApiError(response.status, `API Error: ${response.statusText}`)
  }

  return response.json()
}

export const api = {
  // Document endpoints
  documents: {
    list: () => apiRequest<any[]>("/documents"),
    get: (id: string) => apiRequest<any>(`/documents/${id}`),
    upload: (file: File) => {
      const formData = new FormData()
      formData.append("file", file)
      return apiRequest<any>("/upload", {
        method: "POST",
        body: formData,
        headers: {}, // Let browser set Content-Type for FormData
      })
    },
    delete: (id: string) =>
      apiRequest<any>(`/documents/${id}`, {
        method: "DELETE",
      }),
    getStatus: (id: string) => apiRequest<any>(`/documents/${id}/status`),
  },

  // Research endpoints
  research: {
    start: (documentId: string, topic: string, customQuery?: string) =>
      apiRequest<any>(`/documents/${documentId}/research/start`, {
        method: "POST",
        body: JSON.stringify({ topic, custom_query: customQuery }),
      }),
    getTasks: (documentId: string) => apiRequest<any[]>(`/documents/${documentId}/research/tasks`),
    getTask: (documentId: string, taskId: string) =>
      apiRequest<any>(`/documents/${documentId}/research/tasks/${taskId}`),
  },

  // Chat endpoints
  chat: {
    sendMessage: (message: string, documentId: string, useRag = true) =>
      apiRequest<any>("/conversation", {
        method: "POST",
        body: JSON.stringify({
          message,
          document_id: documentId,
          use_rag: useRag,
        }),
      }),
    createSession: (documentId: string, sessionName?: string) =>
      apiRequest<any>("/conversation/new", {
        method: "POST",
        body: JSON.stringify({
          document_id: documentId,
          session_name: sessionName,
        }),
      }),
    getSessions: () => apiRequest<any[]>("/conversation/sessions"),
    getHistory: (sessionId: string) => apiRequest<any[]>(`/conversation/${sessionId}/history`),
  },
}
