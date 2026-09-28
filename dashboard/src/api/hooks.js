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

export function useCreateFarmMutation() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (data) => client.createFarm(data),
        onSuccess: () => qc.invalidateQueries({ queryKey: ['farmerFarm'] }),
    })
}

export function useFarmStatus(farmId) {
    return useQuery({
        queryKey: ['farmStatus', farmId],
        queryFn: () => client.getFarmStatus(farmId),
        enabled: !!farmId,
    })
}

export function useFarmHistory(farmId, days = 30) {
    return useQuery({
        queryKey: ['farmHistory', farmId, days],
        queryFn: () => client.getFarmHistory(farmId, days),
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
        mutationFn: (formData) => client.submitCheckin(formData),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['alerts'] })
            qc.invalidateQueries({ queryKey: ['farmStatus'] })
        },
    })
}

export function usePrediction(predictionId) {
    return useQuery({
        queryKey: ['prediction', predictionId],
        queryFn: () => client.getPredictionById(predictionId),
        enabled: !!predictionId,
    })
}

export function useAlerts(farmId) {
    return useQuery({
        queryKey: ['alerts', farmId],
        queryFn: () => client.getAlerts(farmId),
        enabled: !!farmId,
    })
}

export function useAllAlerts() {
    return useQuery({ queryKey: ['allAlerts'], queryFn: client.getAllAlerts })
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
