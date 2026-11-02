import { useUpdateFarmMutation } from '../../api/hooks'
import Card, { SectionHeader } from '../ui/Card'
import { buttonClass } from '../ui/styles'

// Turns the NPK sensor on or off for the selected plot. The nutrient charts and the low-nutrient alerts only exist while it is on.
export default function NpkSetting({ farm }) {
    const mutation = useUpdateFarmMutation()
    if (!farm) return null
    const enabled = Boolean(farm.hasNpkSensor)

    return (
        <Card aria-labelledby="npk-setting-title">
            <SectionHeader id="npk-setting-title" title="Soil nutrient sensor" as="h2" />
            <p className="m-0 text-body text-ink">
                {enabled
                    ? 'This plot has an NPK sensor, so nitrogen, phosphorus and potassium are shown above. If you turn it off, those charts are hidden and low-nutrient alerts stop. Readings already saved are kept.'
                    : 'Does this plot have an NPK sensor? Turn it on to see nitrogen, phosphorus and potassium here, and to get an alert in the app when one runs low.'}
            </p>
            <div className="mt-3">
                <button
                    type="button"
                    onClick={() => mutation.mutate({ farmId: farm.farm_id, changes: { hasNpkSensor: !enabled } })}
                    disabled={mutation.isPending}
                    className={buttonClass({ variant: 'secondary', size: 'sm' })}
                >
                    {mutation.isPending ? 'Saving…' : enabled ? 'Turn off NPK sensor' : 'This plot has an NPK sensor'}
                </button>
            </div>
            {mutation.isError && (
                <p role="alert" className="m-0 mt-2 text-small text-critical-text">
                    Could not save this setting. Please try again.
                </p>
            )}
        </Card>
    )
}
