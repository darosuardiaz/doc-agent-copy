import { create } from "zustand"
import { devtools } from "zustand/middleware"
import { api } from "@/lib/api"

export interface Document {
  id: string
  filename: string
  original_filename: string
  file_size: number
  mime_type?: string
  page_count: number
  word_count: number
  financial_facts?: {
    revenue?: {
      current_year?: string
      previous_year?: string
      currency?: string
      period?: string
    }
    profit_loss?: {
      net_income?: string
      gross_profit?: string
      operating_profit?: string
      currency?: string
    }
  }
  investment_data?: {
    sector?: string
    stage?: string
    market_cap?: string
    valuation?: string
  }
  key_metrics?: {
    customer_count?: number
    arr?: string
    churn_rate?: string
    ev_sales_ttm?: string
    five_year_median?: string
    five_year_high?: string
    five_year_low?: string
  }
  is_processed: boolean
  is_embedded: boolean
  processing_error?: string
  pinecone_namespace?: string
  embedding_count?: number
  created_at: string
  updated_at: string
}

interface DocumentState {
  documents: Document[]
  currentDocument: Document | null
  isLoading: boolean
  error: string | null

  // Actions
  setDocuments: (documents: Document[]) => void
  setCurrentDocument: (document: Document | null) => void
  addDocument: (document: Document) => void
  updateDocument: (id: string, updates: Partial<Document>) => void
  removeDocument: (id: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  // API Actions
  fetchDocuments: () => Promise<void>
  fetchDocument: (id: string) => Promise<void>
  uploadDocument: (file: File) => Promise<string>
  deleteDocument: (id: string) => Promise<void>
}

export const useDocumentStore = create<DocumentState>()(
  devtools(
    (set, get) => ({
      documents: [],
      currentDocument: null,
      isLoading: false,
      error: null,

      setDocuments: (documents) => set({ documents }),
      setCurrentDocument: (document) => set({ currentDocument: document }),
      addDocument: (document) =>
        set((state) => ({
          documents: [...state.documents, document],
        })),
      updateDocument: (id, updates) =>
        set((state) => ({
          documents: state.documents.map((doc) => (doc.id === id ? { ...doc, ...updates } : doc)),
          currentDocument:
            state.currentDocument?.id === id ? { ...state.currentDocument, ...updates } : state.currentDocument,
        })),
      removeDocument: (id) =>
        set((state) => ({
          documents: state.documents.filter((doc) => doc.id !== id),
          currentDocument: state.currentDocument?.id === id ? null : state.currentDocument,
        })),
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),

      fetchDocuments: async () => {
        set({ isLoading: true, error: null })
        try {
          const documents = await api.documents.list()
          set({ documents, isLoading: false })
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false })
        }
      },

      fetchDocument: async (id: string) => {
        set({ isLoading: true, error: null })
        try {
          const document = await api.documents.get(id)
          set({ currentDocument: document, isLoading: false })
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false })
        }
      },

      uploadDocument: async (file: File) => {
        set({ isLoading: true, error: null })
        try {
          const result = await api.documents.upload(file)

          // Add the new document to the store
          const newDocument: Document = {
            id: result.document_id,
            filename: result.filename,
            original_filename: file.name,
            file_size: result.file_size,
            mime_type: file.type,
            page_count: 0,
            word_count: 0,
            is_processed: false,
            is_embedded: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }

          get().addDocument(newDocument)
          set({ isLoading: false })
          return result.document_id
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false })
          throw error
        }
      },

      deleteDocument: async (id: string) => {
        set({ isLoading: true, error: null })
        try {
          await api.documents.delete(id)
          get().removeDocument(id)
          set({ isLoading: false })
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false })
          throw error
        }
      },
    }),
    { name: "document-store" },
  ),
)
