import { useEffect, useState } from 'react'
import { api, Patient, PatientCreate, Medication } from '../api/client'
import { Plus, Edit, Trash2, X } from 'lucide-react'

export default function PatientManager() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null)
  const [formData, setFormData] = useState<PatientCreate>({
    name: '',
    phone: '',
    gestational_age_weeks: 0,
    risk_factors: [],
    medications: [],
    risk_category: 'low',
  })
  const [riskFactorsInput, setRiskFactorsInput] = useState('')
  const [medicationInputs, setMedicationInputs] = useState<Medication[]>([])

  useEffect(() => {
    loadPatients()
  }, [])

  const loadPatients = async () => {
    try {
      const response = await api.getPatients()
      setPatients(response.data)
    } catch (error) {
      console.error('Error loading patients:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      // Convert risk factors input to array
      const riskFactors = riskFactorsInput.split(',').map(s => s.trim()).filter(s => s)
      
      // Use medication inputs
      const medications = medicationInputs.filter(med => med.name.trim() !== '')
      
      const submitData = {
        ...formData,
        risk_factors: riskFactors,
        medications: medications,
      }
      
      if (editingPatient) {
        await api.updatePatient(editingPatient.id, submitData)
      } else {
        await api.createPatient(submitData)
      }
      setShowModal(false)
      setEditingPatient(null)
      resetForm()
      loadPatients()
    } catch (error) {
      console.error('Error saving patient:', error)
      alert('Error saving patient. Please try again.')
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      phone: '',
      gestational_age_weeks: 0,
      risk_factors: [],
      medications: [],
      risk_category: 'low',
    })
    setRiskFactorsInput('')
    setMedicationInputs([{ name: '', dosage: '', frequency: '' }])
  }

  const handleEdit = (patient: Patient) => {
    setEditingPatient(patient)
    setFormData({
      name: patient.name,
      phone: patient.phone,
      gestational_age_weeks: patient.gestational_age_weeks,
      risk_factors: patient.risk_factors,
      medications: patient.medications,
      risk_category: patient.risk_category,
    })
    setRiskFactorsInput(patient.risk_factors.join(', '))
    
    // Set medication inputs
    if (patient.medications && patient.medications.length > 0) {
      setMedicationInputs(patient.medications)
    } else {
      setMedicationInputs([{ name: '', dosage: '', frequency: '' }])
    }
    
    setShowModal(true)
  }

  const handleGenerateSchedule = async (patientId: number) => {
    try {
      await api.generateIVRSchedule(patientId)
      alert('IVR schedule generated successfully!')
      loadPatients()
    } catch (error) {
      console.error('Error generating schedule:', error)
      alert('Error generating schedule. Please try again.')
    }
  }

  const addMedication = () => {
    setMedicationInputs([...medicationInputs, { name: '', dosage: '', frequency: '' }])
  }

  const removeMedication = (index: number) => {
    setMedicationInputs(medicationInputs.filter((_, i) => i !== index))
  }

  const updateMedication = (index: number, field: keyof Medication, value: string) => {
    const updated = [...medicationInputs]
    updated[index] = { ...updated[index], [field]: value }
    setMedicationInputs(updated)
  }

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900">Patient Manager</h2>
        <button
          onClick={() => {
            setShowModal(true)
            setEditingPatient(null)
            resetForm()
          }}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-5 h-5 mr-2" />
          Add New Patient
        </button>
      </div>

      {/* Patients Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Phone
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Gestational Age
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Risk Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Medications
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {patients.map((patient) => (
              <tr key={patient.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {patient.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {patient.phone}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {patient.gestational_age_weeks} weeks
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      patient.risk_category === 'high'
                        ? 'bg-red-100 text-red-800'
                        : patient.risk_category === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {patient.risk_category}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {patient.medications && patient.medications.length > 0 ? (
                    <div>
                      {patient.medications.map((med, idx) => (
                        <div key={idx} className="mb-1">
                          {med.name}
                          {med.dosage && ` - ${med.dosage}`}
                          {med.frequency && ` (${med.frequency})`}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-gray-400">None</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                  <button
                    onClick={() => handleEdit(patient)}
                    className="text-primary-600 hover:text-primary-900"
                    title="Edit Patient"
                  >
                    <Edit className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => handleGenerateSchedule(patient.id)}
                    className="text-green-600 hover:text-green-900 text-xs"
                    title="Generate Schedule"
                  >
                    Schedule
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              {editingPatient ? 'Edit Patient' : 'Add New Patient'}
            </h3>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  required
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="+1234567890"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Gestational Age (weeks)
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  max="42"
                  value={formData.gestational_age_weeks}
                  onChange={(e) =>
                    setFormData({ ...formData, gestational_age_weeks: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Risk Category
                </label>
                <select
                  value={formData.risk_category}
                  onChange={(e) => setFormData({ ...formData, risk_category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Risk Factors (comma-separated)
                </label>
                <input
                  type="text"
                  value={riskFactorsInput}
                  onChange={(e) => setRiskFactorsInput(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="diabetes, hypertension"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Medications
                </label>
                {medicationInputs.map((med, index) => (
                  <div key={index} className="mb-3 p-3 border border-gray-200 rounded-md">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">Medication {index + 1}</span>
                      {medicationInputs.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeMedication(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <input
                          type="text"
                          placeholder="Medication name"
                          value={med.name}
                          onChange={(e) => updateMedication(index, 'name', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                      </div>
                      <div>
                        <input
                          type="text"
                          placeholder="Dosage (e.g., 400mg)"
                          value={med.dosage}
                          onChange={(e) => updateMedication(index, 'dosage', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                      </div>
                      <div>
                        <input
                          type="text"
                          placeholder="Frequency (e.g., daily)"
                          value={med.frequency}
                          onChange={(e) => updateMedication(index, 'frequency', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        />
                      </div>
                    </div>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addMedication}
                  className="text-sm text-primary-600 hover:text-primary-800"
                >
                  + Add Medication
                </button>
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false)
                    setEditingPatient(null)
                    resetForm()
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
                >
                  {editingPatient ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
