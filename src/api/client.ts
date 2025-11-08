import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Medication {
  name: string
  dosage: string
  frequency: string[] // Array of days: ["Sun", "Mon", "Tue", etc.]
  time: string // Time in HH:MM format (24-hour)
}

export interface Patient {
  id: number
  name: string
  phone: string
  gestational_age_weeks: number
  risk_factors: string[]
  medications: Medication[]
  risk_category: string
  call_schedule?: any[]
  created_at: string
  updated_at: string
}

export interface PatientCreate {
  name: string
  phone: string
  gestational_age_weeks: number
  risk_factors: string[]
  medications: Medication[]
  risk_category: string
}

export const api = {
  // Patients
  getPatients: () => apiClient.get<Patient[]>('/patients/'),
  getPatient: (id: number) => apiClient.get<Patient>(`/patients/${id}`),
  createPatient: (data: PatientCreate) => apiClient.post('/patients/', data),
  updatePatient: (id: number, data: Partial<PatientCreate>) =>
    apiClient.put(`/patients/${id}`, data),
  deletePatient: (id: number) => apiClient.delete(`/patients/${id}`),
  
  // IVR Schedule
  generateIVRSchedule: (patientId: number) =>
    apiClient.post('/generate_comprehensive_ivr_schedule', { patient_id: patientId }),
  getUpcomingCalls: () => apiClient.get('/upcoming-calls-summary'),
  
  // Analytics
  getAnalytics: () => apiClient.get('/analytics/dashboard'),
  
  // Calls
  executeCall: (callId: number) => apiClient.post(`/calls/${callId}/execute`),
}

export default apiClient

