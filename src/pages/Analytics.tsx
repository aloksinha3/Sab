import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

interface Analytics {
  total_patients: number
  upcoming_calls: number
  pending_messages: number
  high_risk_patients: number
  low_risk_patients: number
}

export default function Analytics() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAnalytics()
  }, [])

  const loadAnalytics = async () => {
    try {
      const response = await api.getAnalytics()
      setAnalytics(response.data)
    } catch (error) {
      console.error('Error loading analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  const riskData = [
    { name: 'Low Risk', value: analytics?.low_risk_patients || 0 },
    { name: 'High Risk', value: analytics?.high_risk_patients || 0 },
  ]

  const COLORS = ['#10b981', '#ef4444']

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-8">Analytics</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {riskData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Overview Stats */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Overview</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Patients</span>
              <span className="text-2xl font-bold text-gray-900">{analytics?.total_patients || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Upcoming Calls</span>
              <span className="text-2xl font-bold text-green-600">{analytics?.upcoming_calls || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Pending Messages</span>
              <span className="text-2xl font-bold text-yellow-600">{analytics?.pending_messages || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">High-Risk Patients</span>
              <span className="text-2xl font-bold text-red-600">{analytics?.high_risk_patients || 0}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

