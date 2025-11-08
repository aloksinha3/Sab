import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Users, Phone, MessageSquare, AlertTriangle } from 'lucide-react'

interface Analytics {
  total_patients: number
  upcoming_calls: number
  pending_messages: number
  high_risk_patients: number
  low_risk_patients: number
}

export default function Dashboard() {
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

  const stats = [
    {
      name: 'Total Patients',
      value: analytics?.total_patients || 0,
      icon: Users,
      color: 'bg-blue-500',
    },
    {
      name: 'Upcoming Calls',
      value: analytics?.upcoming_calls || 0,
      icon: Phone,
      color: 'bg-green-500',
    },
    {
      name: 'Pending Messages',
      value: analytics?.pending_messages || 0,
      icon: MessageSquare,
      color: 'bg-yellow-500',
    },
    {
      name: 'High-Risk Patients',
      value: analytics?.high_risk_patients || 0,
      icon: AlertTriangle,
      color: 'bg-red-500',
    },
  ]

  return (
    <div>
      <h2 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.name} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="/patients"
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-center"
          >
            Add New Patient
          </a>
          <a
            href="/calls"
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-center"
          >
            View Call Queue
          </a>
          <a
            href="/analytics"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-center"
          >
            View Analytics
          </a>
        </div>
      </div>
    </div>
  )
}

