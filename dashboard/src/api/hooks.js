import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as client from './client'

// ── Auth ──────────────────────────────────────────────────────────────────────
export function useLoginMutation() {
    return useMutation({ mutationFn: (creds) => client.login(creds) })
}

export function useRegisterMutation() {
    return useMutation({ mutationFn: (data) => client.register(data) })
}

// ── Farms ─────────────────────────────────────────────────────────────────────
export function useFarmerFarm(farmerId) {
    return useQuery({
        queryKey: ['farmerFarm', farmerId],
        queryFn: () => client.getFarmerFarm(farmerId),
        enabled: !!farmerId,
        retry: false,
    })
}

export function useFarmerFarms(farmerId) {
    return useQuery({
        queryKey: ['farmerFarms', farmerId],
        queryFn: () => client.getFarmerFarms(farmerId),
        enabled: !!farmerId,
        retry: false,
    })
}

export function useCreateFarmMutation() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (data) => client.createFarm(data),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['farmerFarm'] })
            qc.invalidateQueries({ queryKey: ['farmerFarms'] })
        },
    })
}

export function useFarmStatus(farmId) {
    return useQuery({
        queryKey: ['farmStatus', farmId],
        queryFn: () => client.getFarmStatus(farmId),
        enabled: !!farmId,
    })
}

export function useLatestReadings(farmId) {
    return useQuery({
        queryKey: ['latestReadings', farmId],
        queryFn: () => client.getLatestReadings(farmId),
        enabled: !!farmId,
    })
}

export function useFarmHistory(farmId, limit = 100, offset = 0) {
    return useQuery({
        queryKey: ['farmHistory', farmId, limit, offset],
        queryFn: () => client.getFarmHistory(farmId, limit, offset),
        enabled: !!farmId,
    })
}

export function useAllFarms() {
    return useQuery({ queryKey: ['allFarms'], queryFn: client.getAllFarms })
}

// ── Check-ins / Predictions ───────────────────────────────────────────────────
export function useSubmitCheckinMutation() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ farmId, formData }) => client.submitCheckin(farmId, formData),
        onSuccess: (_prediction, { farmId }) => {
            qc.invalidateQueries({ queryKey: ['alerts', farmId] })
            qc.invalidateQueries({ queryKey: ['farmStatus', farmId] })
            qc.invalidateQueries({ queryKey: ['farmHistory', farmId] })
        },
    })
}

export function usePrediction(farmId, predictionId) {
    return useQuery({
        queryKey: ['prediction', farmId, predictionId],
        queryFn: () => client.getPredictionById(farmId, predictionId),
        enabled: !!farmId && !!predictionId,
    })
}

export function useAlerts(farmId) {
    return useQuery({
        queryKey: ['alerts', farmId],
        queryFn: () => client.getAlerts(farmId),
        enabled: !!farmId,
    })
}

export function useAcknowledgeAlertMutation(farmId) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (alertId) => client.acknowledgeAlert(farmId, alertId),
        onMutate: async (alertId) => {
            await qc.cancelQueries({ queryKey: ['alerts', farmId] })
            const previousAlerts = qc.getQueryData(['alerts', farmId])
            qc.setQueryData(['alerts', farmId], (alerts = []) =>
                alerts.map((alert) =>
                    alert.alert_id === alertId
                        ? { ...alert, status: 'acknowledged' }
                        : alert,
                ),
            )
            return { previousAlerts }
        },
        onError: (_error, _alertId, context) => {
            if (context?.previousAlerts) {
                qc.setQueryData(['alerts', farmId], context.previousAlerts)
            }
        },
        onSettled: () => qc.invalidateQueries({ queryKey: ['alerts', farmId] }),
    })
}

// ── Feedback ──────────────────────────────────────────────────────────────────
export function useConfirmPredictionMutation() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ alertId, farmerId, confirmed, comment }) =>
            client.confirmPrediction(alertId, farmerId, confirmed, comment),
        onSuccess: () => qc.invalidateQueries({ queryKey: ['feedbackList'] }),
    })
}

export function useFeedbackList(filterNotAccurate = false) {
    return useQuery({
        queryKey: ['feedbackList', filterNotAccurate],
        queryFn: () => client.getFeedbackList(filterNotAccurate),
    })
}

// ── Admin / System ────────────────────────────────────────────────────────────
export function useSystemHealth() {
    return useQuery({ queryKey: ['systemHealth'], queryFn: client.getSystemHealth })
}

export function useAllUsers() {
    return useQuery({ queryKey: ['allUsers'], queryFn: client.getAllUsers })
}

export function useModelVersions() {
    return useQuery({ queryKey: ['modelVersions'], queryFn: client.getModelVersions })
}

export function useSwitchModelMutation() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: ({ modelType, versionId }) => client.switchModelVersion(modelType, versionId),
        onSuccess: () => qc.invalidateQueries({ queryKey: ['modelVersions'] }),
    })
}

export function useTriggerRetrainMutation() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (modelType) => client.triggerRetrain(modelType),
        onSuccess: () => qc.invalidateQueries({ queryKey: ['retrainingJobs'] }),
    })
}

export function useRetrainingJobs() {
    return useQuery({
        queryKey: ['retrainingJobs'],
        queryFn: client.getRetrainingJobs,
        refetchInterval: (data) => {
            const jobs = data?.state?.data ?? []
            const hasPending = jobs.some((j) => j.status === 'running' || j.status === 'pending')
            return hasPending ? 5000 : false
        },
    })
}

export function useSmsLog() {
    return useQuery({ queryKey: ['smsLog'], queryFn: client.getSmsLog })
}
