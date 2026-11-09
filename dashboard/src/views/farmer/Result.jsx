import { useParams, useLocation, Link } from 'react-router-dom'
import { useLatestReadingClassification, useLatestReadings, usePrediction } from '../../api/hooks'
import FeedbackControl from '../../components/FeedbackControl'
import { useFarm } from '../../farm/FarmContext'
import { getFusedPredictionCopy } from '../../content/farmerCopy'
import { WarningIcon } from '../../components/Icons'
import { CameraIcon } from '../../components/NavIcons'
import Badge from '../../components/ui/Badge'
import Card from '../../components/ui/Card'
import Notice from '../../components/ui/Notice'
import Skeleton from '../../components/ui/Skeleton'
import { buttonClass, insetClass, linkClass } from '../../components/ui/styles'

const SEVERITY_STYLES = {
    healthy: { tone: 'healthy', label: 'Healthy' },
    warning: { tone: 'warning', label: 'Stress Detected' },
    critical: { tone: 'critical', label: 'Urgent' },
    neutral: { tone: 'neutral', label: 'Needs review' },
}

function SeverityBadge({ level }) {
    const s = SEVERITY_STYLES[level] || SEVERITY_STYLES.neutral
    return <Badge tone={s.tone}>{s.label}</Badge>
}

const BAND_BADGES = {
    weak: { tone: 'warning', label: 'Possible, please check' },
    none: { tone: 'neutral', label: 'Not sure' },
}

// The severity badge (Urgent, Stress detected) shows only when the model is confident. A weaker result gets a softer badge.
function DiseaseBadge({ band, label, level }) {
    const isDisease = Boolean(label) && label.toLowerCase() !== 'healthy'
    const style = isDisease ? BAND_BADGES[band] : null
    if (!style) return <SeverityBadge level={level} />
    return <Badge tone={style.tone}>{style.label}</Badge>
}

function UploadedImage({ imageUrl }) {
    return (
        <Card>
            <h2 className="mb-3 mt-0 text-heading text-ink-secondary">Uploaded leaf image</h2>
            <img
                src={imageUrl}
                alt="Uploaded maize leaf for analysis"
                className="max-h-[28rem] w-full rounded-control object-contain"
            />
        </Card>
    )
}

function ReadingGrid({ tiles }) {
    return (
        <dl className="m-0 grid grid-cols-2 gap-3">
            {tiles.map(([name, value]) => (
                <div key={name} className={insetClass}>
                    <dt className="text-small text-ink-secondary">{name}</dt>
                    <dd className="m-0 mt-0.5 text-heading tabular-nums text-ink">{value}</dd>
                </div>
            ))}
        </dl>
    )
}

function PlotReadingsCard({ farmId }) {
    const { data: reading } = useLatestReadings(farmId)
    const { data: label } = useLatestReadingClassification(farmId)
    if (!reading) return null
    const tiles = [
        ['Temperature', `${reading.temperature} °C`],
        ['Humidity', `${reading.humidity}%`],
        ['Soil moisture', `${reading.soil_moisture}%`],
        ['Leaf wetness', `${reading.leaf_wetness}`],
    ]
    return (
        <Card>
            <h2 className="m-0 text-heading text-ink-secondary">Latest field reading for this plot</h2>
            <p className="mb-3 mt-1 text-small text-ink-secondary">
                Simulated sensor · {reading.recorded_at ? new Date(reading.recorded_at).toLocaleString('en-GB') : ''}
            </p>
            <ReadingGrid tiles={tiles} />
            {label && (
                <p className="mb-0 mt-3 text-small">
                    <span className="text-ink-secondary">Sensor model, this reading: </span>
                    <strong>{label.title}</strong>{' '}
                    <span className="text-ink-secondary">({Math.round(label.confidence * 100)}%)</span>
                </p>
            )}
        </Card>
    )
}

export default function Result() {
    const { farmId: routeFarmId, predictionId } = useParams()
    const location = useLocation()
    const uploadedImageUrl = location.state?.uploadedImageUrl
    const uploadedImage = uploadedImageUrl && <UploadedImage imageUrl={uploadedImageUrl} />
    const { farms, selectedFarmId } = useFarm()
    const farmId = routeFarmId || location.state?.farmId || selectedFarmId
    const { data: prediction, isLoading, isError } = usePrediction(farmId, predictionId)

    if (isLoading) {
        return (
            <div className="mx-auto flex max-w-xl flex-col gap-4">
                <Skeleton label="Loading result…" className="h-10 w-2/3" />
                <Skeleton className="h-56" />
                <Skeleton className="h-32" />
            </div>
        )
    }
    if (isError || !prediction) {
        return (
            <div className="mx-auto max-w-lg">
                <Notice tone="critical" action={<Link to="/" className={buttonClass({ variant: 'secondary', size: 'sm' })}>Back to dashboard</Link>}>
                    <p>Could not load this result.</p>
                </Notice>
            </div>
        )
    }

    const {
        status,
        fused_prediction,
        disease_label,
        disease_confidence,
        disease_band,
        severity_level,
        sensor_conditions,
        recommendation,
        nutrient_status,
        nutrient_confidence,
    } = prediction
    const copy = getFusedPredictionCopy(fused_prediction)

    // How sure the model is about the disease decides the wording of the Disease Detection card.
    const diseaseName = disease_label?.replace(/_/g, ' ') || 'Unknown'
    const isDiseaseLabel = diseaseName.toLowerCase() !== 'healthy' && diseaseName !== 'Unknown'
    const diseaseUnsure = isDiseaseLabel && disease_band === 'none'
    const diseaseHeadline = !isDiseaseLabel
        ? diseaseName
        : diseaseUnsure
            ? 'Not sure what this is'
            : disease_band === 'weak'
                ? `Possible: ${diseaseName}`
                : diseaseName
    const hasNutrientDeficiency = /deficiency/i.test(nutrient_status || '') && !/^no[ _]deficiency$/i.test(nutrient_status || '')
    const predictionFarm = farms.find((farm) => farm.farm_id === prediction.farm_id)

    // Three status states
    if (status === 'uncertain') {
        return (
            <div className="mx-auto flex max-w-lg flex-col gap-4">
                <div className="motion-reveal flex gap-3 rounded-card bg-neutral-bg p-5 text-neutral-text">
                    <CameraIcon className="h-6 w-6 shrink-0" />
                    <div>
                        <h1 className="m-0 text-title">{copy.headline}</h1>
                        <p className="mb-0 mt-1 text-body text-ink">{copy.support}</p>
                    </div>
                </div>
                {uploadedImage}
                <Card><FeedbackControl alertId={predictionId} /></Card>
                <Link to="/check-in" className={buttonClass({ block: true })}>Take a new photo</Link>
            </div>
        )
    }

    if (status === 'out_of_scope') {
        return (
            <div className="mx-auto flex max-w-lg flex-col gap-4">
                <div className="motion-reveal flex gap-3 rounded-card bg-warning-bg p-5 text-warning-text">
                    <span aria-hidden="true" className="mt-1 flex shrink-0"><WarningIcon size={20} /></span>
                    <div>
                        <h1 className="m-0 text-title">{copy.headline}</h1>
                        <p className="mb-0 mt-1 text-body text-ink">{copy.support}</p>
                    </div>
                </div>
                {uploadedImage}
                <Card><FeedbackControl alertId={predictionId} /></Card>
                <Link to="/" className={`inline-flex min-h-11 items-center self-center text-small ${linkClass}`}>Back to dashboard</Link>
            </div>
        )
    }

    // Confirmed result
    return (
        <div className="mx-auto flex max-w-xl flex-col gap-6">
            <header>
                <h1 className="m-0 text-display text-ink">Analysis Result</h1>
                {predictionFarm && (
                    <p className="m-0 mt-1 text-small text-ink-secondary">Plot: {predictionFarm.farm_name}</p>
                )}
            </header>

            {uploadedImage}

            {/* Severity + Disease */}
            <Card className="motion-reveal flex flex-col gap-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                    <h2 className="m-0 text-heading text-ink-secondary">Disease Detection</h2>
                    <DiseaseBadge band={disease_band} label={disease_label} level={severity_level} />
                </div>
                <div>
                    <p className="m-0 text-title capitalize text-ink">
                        {diseaseHeadline}
                    </p>
                    {disease_confidence != null && (
                        diseaseUnsure ? (
                            <p className="mb-0 mt-1 text-small normal-case text-ink-secondary">
                                Closest match: <span className="font-normal capitalize">{diseaseName}</span> ({Math.round(disease_confidence * 100)}%). This is too low to rely on.
                            </p>
                        ) : (
                            <p className="mb-0 mt-1 text-small text-ink-secondary">
                                Confidence: <span className="font-bold">{Math.round(disease_confidence * 100)}%</span>
                            </p>
                        )
                    )}
                </div>
                {diseaseUnsure && (
                    <div className={`${insetClass} text-body text-ink`}>
                        <strong>What to do:</strong> The photo did not give a clear answer. Take another photo in daylight with one leaf held flat. If the leaf looks sick to you, ask your extension officer to have a look.
                    </div>
                )}
                {recommendation && !diseaseUnsure && (
                    <div className={`${insetClass} text-body text-ink`}>
                        <strong>Recommended action:</strong> {recommendation}
                    </div>
                )}
            </Card>

            {/* Sensor conditions */}
            {sensor_conditions && (
                <Card>
                    <h2 className="mb-3 mt-0 text-heading text-ink-secondary">Sensor Conditions at Time of Capture</h2>
                    <ReadingGrid
                        tiles={[
                            ['Temperature', `${sensor_conditions.temperature_c} °C`],
                            ['Humidity', `${sensor_conditions.humidity_pct}%`],
                            ['Soil Moisture', `${sensor_conditions.soil_moisture_pct}%`],
                            ['Leaf Wetness', sensor_conditions.leaf_wetness ? 'Yes' : 'No'],
                        ]}
                    />
                </Card>
            )}

            <PlotReadingsCard farmId={farmId} />

            {/* Nutrient is shown in a separate section */}
            {nutrient_status != null && (
            <Card className="border-2 border-dashed !border-control">
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <h2 className="m-0 text-heading text-ink-secondary">Nutrient Assessment</h2>
                    <Badge tone="neutral" icon={false}>Independent model</Badge>
                </div>
                <p className="m-0 text-heading capitalize text-ink">
                    {nutrient_status?.replace(/_/g, ' ') || 'No deficiency detected'}
                </p>
                {nutrient_confidence != null && (
                    <p className="mb-0 mt-1 text-small text-ink-secondary">
                        Confidence: {Math.round(nutrient_confidence * 100)}%
                    </p>
                )}
                {hasNutrientDeficiency && (
                    <p className={`mb-0 mt-3 ${insetClass} text-body text-ink`}>
                        This is an early sign only. Ask your extension officer to confirm it before you apply fertiliser.
                    </p>
                )}
            </Card>
            )}

            {/* Feedback */}
            <Card>
                <h2 className="m-0 text-heading text-ink-secondary">Was this result accurate?</h2>
                <FeedbackControl alertId={predictionId} />
            </Card>

            <Link to="/" className={`inline-flex min-h-11 items-center self-center text-small ${linkClass}`}>
                Back to dashboard
            </Link>
        </div>
    )
}
