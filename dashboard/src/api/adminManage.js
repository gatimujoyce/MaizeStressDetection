import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { httpClient } from './httpClient'

// Admin management calls: edit farmers and farms, reset a password, read the action log.
export const updateAdminUser = ({ id, data }) => httpClient.patch(`/admin/users/${id}`, data)
export const resetAdminUserPassword = ({ id }) => httpClient.post(`/admin/users/${id}/reset-password`, {})
export const createAdminFarm = ({ userId, data }) => httpClient.post(`/admin/users/${userId}/farms`, data)
export const updateAdminFarm = ({ id, data }) => httpClient.patch(`/admin/farms/${id}`, data)
export const archiveAdminFarm = ({ id }) => httpClient.post(`/admin/farms/${id}/archive`, {})
export const restoreAdminFarm = ({ id }) => httpClient.post(`/admin/farms/${id}/restore`, {})
export const getAdminAuditLog = () => httpClient.get('/admin/audit-log')
export const getDeviceKey = (farmId) => httpClient.get(`/admin/farms/${farmId}/device-key`)
export const createDeviceKey = ({ id }) => httpClient.post(`/admin/farms/${id}/device-key`, {})
export const revokeDeviceKey = ({ id }) => httpClient.delete(`/admin/farms/${id}/device-key`)

// Every change refreshes the admin lists and the action log.
export function useAdminManageMutation(mutationFn) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin'] }),
  })
}

export function useAdminAuditLog() {
  return useQuery({ queryKey: ['admin', 'auditLog'], queryFn: getAdminAuditLog, refetchInterval: 30000 })
}
