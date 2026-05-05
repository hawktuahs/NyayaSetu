import { create } from 'zustand'
import { healthCheck, listCases } from '../api/client'

export const useAppStore = create((set, get) => ({
  llmStatus: null,
  cases: [],
  pendingCount: 0,

  fetchHealth: async () => {
    try {
      const { data } = await healthCheck()
      set({ llmStatus: data })
    } catch {}
  },

  fetchCases: async () => {
    try {
      const { data } = await listCases()
      const pending = data.filter(c => c.status === 'pending_verification').length
      set({ cases: data, pendingCount: pending })
    } catch {}
  },
}))
