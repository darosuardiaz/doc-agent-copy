import { create } from "zustand"
import { devtools } from "zustand/middleware"
import { api } from "@/lib/api"

export interface ResearchTask {
  id: string
  document_id: string
  topic: string
  research_query: string
  status: "pending" | "in_progress" | "completed" | "failed"
  content_outline?: Record<
    string,
    {
      title: string
      description: string
    }
  >
  research_findings?: {
    summary: string
  }
  sources_used?: Array<{
    page: number
    content: string
    relevance_score: number
  }>
  processing_time?: number
  model_used?: string
  error_message?: string
  created_at: string
  completed_at?: string
}

interface ResearchState {
  tasks: ResearchTask[]
  currentTask: ResearchTask | null
  isLoading: boolean
  error: string | null
  pollingIntervals: Map<string, NodeJS.Timeout>

  // Actions
  setTasks: (tasks: ResearchTask[]) => void
  setCurrentTask: (task: ResearchTask | null) => void
  addTask: (task: ResearchTask) => void
  updateTask: (id: string, updates: Partial<ResearchTask>) => void
  removeTask: (id: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  // API Actions
  startResearch: (documentId: string, topic: string, customQuery?: string) => Promise<string>
  fetchTasks: (documentId: string) => Promise<void>
  fetchTask: (documentId: string, taskId: string) => Promise<void>
  
  // Polling Actions
  startPolling: (documentId: string, taskId: string) => void
  stopPolling: (taskId: string) => void
  stopAllPolling: () => void
}

export const useResearchStore = create<ResearchState>()(
  devtools(
    (set, get) => ({
      tasks: [],
      currentTask: null,
      isLoading: false,
      error: null,
      pollingIntervals: new Map(),

      setTasks: (tasks) => set({ tasks }),
      setCurrentTask: (task) => set({ currentTask: task }),
      addTask: (task) =>
        set((state) => ({
          tasks: [...state.tasks, task],
        })),
      updateTask: (id, updates) =>
        set((state) => ({
          tasks: state.tasks.map((task) => (task.id === id ? { ...task, ...updates } : task)),
          currentTask: state.currentTask?.id === id ? { ...state.currentTask, ...updates } : state.currentTask,
        })),
      removeTask: (id) =>
        set((state) => ({
          tasks: state.tasks.filter((task) => task.id !== id),
          currentTask: state.currentTask?.id === id ? null : state.currentTask,
        })),
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),

      startResearch: async (documentId: string, topic: string, customQuery?: string) => {
        set({ isLoading: true, error: null })
        try {
          const task = await api.research.start(documentId, topic, customQuery)

          // Add the new task to the store
          get().addTask(task)
          set({ currentTask: task, isLoading: false })
          
          // Start polling for this task
          get().startPolling(documentId, task.id)
          
          return task.id
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false })
          throw error
        }
      },

      fetchTasks: async (documentId: string) => {
        set({ isLoading: true, error: null })
        try {
          const tasks = await api.research.getTasks(documentId)
          set({ tasks, isLoading: false })
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false })
        }
      },

      fetchTask: async (documentId: string, taskId: string) => {
        try {
          const task = await api.research.getTask(documentId, taskId)
          get().updateTask(taskId, task)
          
          // If current task, update it
          if (get().currentTask?.id === taskId) {
            set({ currentTask: task })
          }
          
          // Stop polling if task is completed or failed
          if (task.status === 'completed' || task.status === 'failed') {
            get().stopPolling(taskId)
          }
        } catch (error) {
          console.error('Error fetching task:', error)
        }
      },

      startPolling: (documentId: string, taskId: string) => {
        // Clear existing interval if any
        get().stopPolling(taskId)
        
        const interval = setInterval(async () => {
          await get().fetchTask(documentId, taskId)
        }, 2000) // Poll every 2 seconds
        
        set((state) => ({
          pollingIntervals: new Map(state.pollingIntervals.set(taskId, interval))
        }))
      },

      stopPolling: (taskId: string) => {
        const interval = get().pollingIntervals.get(taskId)
        if (interval) {
          clearInterval(interval)
          set((state) => {
            const newIntervals = new Map(state.pollingIntervals)
            newIntervals.delete(taskId)
            return { pollingIntervals: newIntervals }
          })
        }
      },

      stopAllPolling: () => {
        get().pollingIntervals.forEach((interval) => clearInterval(interval))
        set({ pollingIntervals: new Map() })
      },
    }),
    { name: "research-store" },
  ),
)
