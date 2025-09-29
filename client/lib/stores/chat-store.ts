import { create } from "zustand"
import { devtools } from "zustand/middleware"
import { api } from "@/lib/api"

export interface ChatMessage {
  id: string
  session_id: string
  role: "user" | "assistant"
  content: string
  created_at: string
  token_count?: number
  sources_used?: Array<{
    page: number
    content: string
    relevance_score: number
  }>
}

export interface ChatSession {
  id: string
  document_id: string
  session_name: string
  user_id?: string
  is_active: boolean
  created_at: string
  last_activity: string
  message_count: number
  temperature?: number
  max_tokens?: number
  system_prompt?: string
}

interface ChatState {
  sessions: ChatSession[]
  currentSession: ChatSession | null
  messages: ChatMessage[]
  isLoading: boolean
  isTyping: boolean
  error: string | null

  // Actions
  setSessions: (sessions: ChatSession[]) => void
  setCurrentSession: (session: ChatSession | null) => void
  setMessages: (messages: ChatMessage[]) => void
  addMessage: (message: ChatMessage) => void
  setLoading: (loading: boolean) => void
  setTyping: (typing: boolean) => void
  setError: (error: string | null) => void

  // API Actions
  createSession: (documentId: string, sessionName?: string) => Promise<string>
  fetchSessions: () => Promise<void>
  fetchMessages: (sessionId: string) => Promise<void>
  sendMessage: (message: string, documentId: string, useRag?: boolean) => Promise<void>
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set, get) => ({
      sessions: [],
      currentSession: null,
      messages: [],
      isLoading: false,
      isTyping: false,
      error: null,

      setSessions: (sessions) => set({ sessions }),
      setCurrentSession: (session) => set({ currentSession: session }),
      setMessages: (messages) => set({ messages }),
      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),
      setLoading: (loading) => set({ isLoading: loading }),
      setTyping: (typing) => set({ isTyping: typing }),
      setError: (error) => set({ error }),

      createSession: async (documentId: string, sessionName?: string) => {
        set({ isLoading: true, error: null })
        try {
          const session = await api.chat.createSession(
            documentId,
            sessionName || "New Chat Session",
          )

          set((state) => ({
            sessions: [...state.sessions, session],
            currentSession: session,
            messages: [],
            isLoading: false,
          }))

          return session.id
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false })
          throw error
        }
      },

      fetchSessions: async () => {
        set({ isLoading: true, error: null })
        try {
          const sessions = await api.chat.getSessions()
          set({ sessions, isLoading: false })
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false })
        }
      },

      fetchMessages: async (sessionId: string) => {
        set({ isLoading: true, error: null })
        try {
          const messages = await api.chat.getHistory(sessionId)
          set({ messages, isLoading: false })
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false })
        }
      },

      sendMessage: async (message: string, documentId: string, useRag = true) => {
        const userMessage: ChatMessage = {
          id: `msg_${Date.now()}_user`,
          session_id: get().currentSession?.id || "",
          role: "user",
          content: message,
          created_at: new Date().toISOString(),
        }

        get().addMessage(userMessage)
        set({ isTyping: true, error: null })

        try {
          const result = await api.chat.sendMessage(message, documentId, useRag)

          const assistantMessage: ChatMessage = {
            id: `msg_${Date.now()}_assistant`,
            session_id: result.session_id,
            role: "assistant",
            content: result.message,
            created_at: new Date().toISOString(),
            token_count: result.token_count,
            sources_used: result.sources_used,
          }

          get().addMessage(assistantMessage)
          set({ isTyping: false })
        } catch (error) {
          set({ error: (error as Error).message, isTyping: false })
        }
      },
    }),
    { name: "chat-store" },
  ),
)
