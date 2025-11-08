import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Phone, Clock, CheckCircle, Play } from 'lucide-react'

interface Call {
  id: number
  patient_id: number
  call_type: string
  status: string
  message_text: string
  scheduled_time: string
  completed_at: string | null
  name: string
  phone: string
}

export default function CallQueue() {
  const [calls, setCalls] = useState<Call[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadCalls()
    const interval = setInterval(loadCalls, 5000) // Refresh every 5 seconds for better real-time updates
    return () => clearInterval(interval)
  }, [])

  const loadCalls = async () => {
    try {
      const response = await api.getUpcomingCalls()
      setCalls(response.data.calls || [])
      setLoading(false)
    } catch (error) {
      console.error('Error loading calls:', error)
      setLoading(false)
    }
  }

  const handleExecuteCall = async (callId: number) => {
    if (!confirm('Are you sure you want to execute this call now?')) {
      return
    }
    
    try {
      await api.executeCall(callId)
      alert('Call executed successfully!')
      loadCalls() // Refresh the list
    } catch (error) {
      console.error('Error executing call:', error)
      alert('Error executing call. Please check Twilio configuration.')
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900">Call Queue</h2>
        <button
          onClick={loadCalls}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Refresh
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Patient
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Call Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Scheduled Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Message Preview
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {calls.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  No upcoming calls scheduled
                </td>
              </tr>
            ) : (
              calls.map((call) => (
                <tr key={call.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{call.name}</div>
                    <div className="text-sm text-gray-500">{call.phone}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                      {call.call_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(call.scheduled_time).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        call.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : call.status === 'scheduled'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {call.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {call.message_text?.substring(0, 100)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {call.status === 'scheduled' && (
                      <button
                        onClick={() => handleExecuteCall(call.id)}
                        className="text-green-600 hover:text-green-900 flex items-center"
                        title="Execute call now"
                      >
                        <Play className="w-4 h-4 mr-1" />
                        Execute
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

