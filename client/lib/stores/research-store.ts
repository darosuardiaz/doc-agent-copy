import { create } from "zustand"
import { devtools } from "zustand/middleware"
import { api } from "@/lib/api"

export interface ResearchTask {
  id: string
  document_id: string
  topic: string
  custom_query?: string
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
  created_at: string
  completed_at?: string
  processing_time?: number
}

interface ResearchState {
  tasks: ResearchTask[]
  currentTask: ResearchTask | null
  isLoading: boolean
  error: string | null

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
}

export const useResearchStore = create<ResearchState>()(
  devtools(
    (set, get) => ({
      tasks: [],
      currentTask: null,
      isLoading: false,
      error: null,

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
          const result = await api.research.start(documentId, topic, customQuery)

          const newTask: ResearchTask = {
            id: result.task_id,
            document_id: documentId,
            topic,
            custom_query: customQuery,
            status: "completed",
            content_outline: result.content_outline,
            research_findings: result.research_findings,
            sources_used: result.sources_used,
            created_at: new Date().toISOString(),
            completed_at: new Date().toISOString(),
            processing_time: result.processing_time,
          }

          get().addTask(newTask)
          set({ currentTask: newTask, isLoading: false })
          return result.task_id
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
        set({ isLoading: true, error: null })
        try {
          const task = await api.research.getTask(documentId, taskId)
          set({ currentTask: task, isLoading: false })
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false })
        }
      },
    }),
    { name: "research-store" },
  ),
)
