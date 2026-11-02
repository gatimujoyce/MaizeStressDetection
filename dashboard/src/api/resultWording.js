import { confidenceBand } from './statusAdapter'

// What one past photo check-in found, in the same words as the result page (Possible / Not sure), so the history never
// calls a weak guess a confirmed disease. The photo's own finding only; the plot sensors have their own alerts.
export function describeResult(prediction) {
    const label = prediction?.disease_label
    if (prediction?.triage_result === 'out_of_scope') return { label: 'Not a maize leaf', tone: 'neutral' }
    if (!label || label === 'Unassessed') return { label: 'Photo unclear', tone: 'neutral' }
    if (label.toLowerCase() === 'healthy') return { label: 'Leaf looks healthy', tone: 'healthy' }
    const band = confidenceBand(prediction.disease_conf ?? 0)
    if (band === 'strong') return { label, tone: 'critical' }
    if (band === 'weak') return { label: `Possible: ${label}`, tone: 'warning' }
    return { label: 'Not sure', tone: 'neutral' }
}

// What the leaf-photo nutrient model said at one check-in. It is only ever "possible" and never "confirmed": the nutrient
// model has not been checked against an agronomist's diagnosis, and nitrogen is capped at weak in the fusion rules.
export function describeNutrient(prediction) {
    const label = prediction?.nutrient_label
    if (prediction?.triage_result === 'out_of_scope' || !label || label === 'Unassessed') {
        return { label: 'Photo unclear', tone: 'neutral' }
    }
    const key = label.toLowerCase().replace(/_/g, ' ')
    if (key === 'no deficiency' || key === 'healthy') return { label: 'No deficiency seen', tone: 'healthy' }
    if (confidenceBand(prediction.nutrient_conf ?? 0) === 'none') return { label: 'Not sure', tone: 'neutral' }
    return {
        label: `Possible: ${label}`,
        detail: 'An early sign only. Ask your extension officer to confirm it.',
        tone: 'warning',
    }
}