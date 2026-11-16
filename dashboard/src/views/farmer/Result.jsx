import { useParams, useLocation, Link } from 'react-router-dom'
import { useLatestReadingClassification, useLatestReadings, usePrediction } from '../../api/hooks'
import FeedbackControl from '../../components/FeedbackControl'
import { useFarm } from '../../farm/FarmContext'
import { getFusedPredictionCopy } from '../../content/farmerCopy'
import Badge from '../../components/ui/Badge'
import Card, { SectionHeader } from '../../components/ui/Card'
import DescriptionList from '../../components/ui/DescriptionList'
import Notice from '../../components/ui/Notice'
import Page from '../../components/ui/Page'
import PageHeader from '../../components/ui/PageHeader'
import Skeleton from '../../components/ui/Skeleton'
import { buttonClass } from '../../components/ui/styles'

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

function LeafPhoto({ imageUrl }) {
    if (!imageUrl) return null
    return (
        <img
            src={imageUrl}
            alt="Uploaded maize leaf for analysis"
            className="max-h-72 w-full rounded-control bg-app-bg object-contain"
        />
    )
}

// The sensor's leaf_wetness value is the dew point gap: air temperature minus dew point, in degrees C. A SMALL gap means
// damp air and wet leaves, a large gap means dry air, so the number must not be shown as a score that rises with wetness.
// The cut-offs are provisional (the disease rules use below 3 as "wet enough to favour disease").
function leafDampness(gap) {
    if (!Number.isFinite(gap)) return 'Not reporting'
    if (gap < 3) return 'Likely wet'
    if (gap < 6) return 'Damp'
    return 'Dry'
}

// What the field was like: the sensor values saved with the photo, and the plot's latest reading.
function Conditions({ sensorConditions, farmId }) {
    const { data: reading } = useLatestReadings(farmId)
    const { data: label } = useLatestReadingClassification(farmId)
    if (!sensorConditions && !reading) return null

    return (
        <Card divided aria-labelledby="conditions-title">
            <h2 id="conditions-title" className="m-0 text-section text-ink">Conditions</h2>
            {sensorConditions && (
                <section aria-labelledby="capture-title">
                    <SectionHeader id="capture-title" as="h3" title="Sensor conditions at time of capture" />
                    <DescriptionList
                        items={[
                            { label: 'Temperature', value: `${sensorConditions.temperature_c} °C` },
                            { label: 'Humidity', value: `${sensorConditions.humidity_pct}%` },
                            { label: 'Soil moisture', value: `${sensorConditions.soil_moisture_pct}%` },
                            { label: 'Leaf wetness', value: sensorConditions.leaf_wetness ? 'Yes' : 'No' },
                        ]}
                    />
                </section>
            )}
            {reading && (
                <section aria-labelledby="latest-title">
                    <SectionHeader
                        id="latest-title"
                        as="h3"
                        title="Latest field reading for this plot"
                        description={`Simulated sensor · ${reading.recorded_at ? new Date(reading.recorded_at).toLocaleString('en-GB') : ''}`}
                    />
                    <DescriptionList
                        items={[
                            { label: 'Temperature', value: Number.isFinite(reading.temperature) ? `${reading.temperature} °C` : 'Not reporting' },
                            { label: 'Humidity', value: Number.isFinite(reading.humidity) ? `${reading.humidity}%` : 'Not reporting' },
                            { label: 'Soil moisture', value: Number.isFinite(reading.soil_moisture) ? `${reading.soil_moisture}%` : 'Not reporting' },
                            { label: 'Leaves', value: leafDampness(reading.leaf_wetness) },
                        ]}
                    />
                    {label && (
                        <p className="mb-0 mt-3 text-small text-ink-secondary">
                            Sensor model, this reading: <strong className="text-ink">{label.title}</strong> ({Math.round(label.confidence * 100)}%)
                        </p>
                    )}
                </section>
            )}
        </Card>
    )
}

function FeedbackCard({ predictionId }) {
    return (
        <Card aria-labelledby="feedback-title">
            <SectionHeader id="feedback-title" title="Was this result accurate?" className="!mb-0" />
            <FeedbackControl alertId={predictionId} />
        </Card>
    )
}

export default function Result() {
    const { farmId: routeFarmId, predictionId } = useParams()
    const location = useLocation()
    const uploadedImageUrl = location.state?.uploadedImageUrl
    const { farms, selectedFarmId } = useFarm()
    const farmId = routeFarmId || location.state?.farmId || selectedFarmId
    const { data: prediction, isLoading, isError, isFetching, refetch } = usePrediction(farmId, predictionId)
    const back = { to: '/', label: 'Back to dashboard' }

    if (isLoading) {
        return (
            <Page>
                <Skeleton label="Loading result" className="h-10 w-2/3" />
                <Skeleton className="h-64" />
                <Skeleton className="h-32" />
            </Page>
        )
    }

    if (isError || !prediction) {
        return (
            <Page>
                <PageHeader title="Analysis result" back={back} />
                <Notice tone="critical" onRetry={isError ? () => refetch() : undefined} retrying={isFetching}>
                    <p>Could not load this result.</p>
                </Notice>
            </Page>
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
    // How sure the model is about the disease decides the wording of the Disease detection section.
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
    const plotLine = predictionFarm ? `Plot: ${predictionFarm.farm_name}` : undefined

    // The photo could not be read, or it is not something the model knows.
    if (status === 'uncertain' || status === 'out_of_scope') {
        return (
            <Page>
                <PageHeader title="Analysis result" subtitle={plotLine} back={back} />
                <Notice tone={status === 'uncertain' ? 'neutral' : 'warning'} title={copy.headline}>
                    <p>{copy.support}</p>
                </Notice>
                {uploadedImageUrl && (
                    <Card>
                        <LeafPhoto imageUrl={uploadedImageUrl} />
                    </Card>
                )}
                <FeedbackCard predictionId={predictionId} />
                {status === 'uncertain' && (
                    <Link to="/check-in" className={`${buttonClass({ block: true })} sm:w-auto sm:self-start`}>Take a new photo</Link>
                )}
            </Page>
        )
    }

    return (
        <Page>
            <PageHeader title="Analysis result" subtitle={plotLine} back={back} />

            <Card divided aria-labelledby="disease-title" className="motion-reveal">
                {uploadedImageUrl && <LeafPhoto imageUrl={uploadedImageUrl} />}
                <div className="flex flex-col gap-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                        <h2 id="disease-title" className="m-0 text-small font-bold text-ink-secondary">Disease detection</h2>
                        <DiseaseBadge band={disease_band} label={disease_label} level={severity_level} />
                    </div>
                    <p className="m-0 text-section capitalize text-ink">{diseaseHeadline}</p>
                    {disease_confidence != null && (
                        diseaseUnsure ? (
                            <p className="m-0 text-small text-ink-secondary">
                                Closest match: <span className="capitalize">{diseaseName}</span> ({Math.round(disease_confidence * 100)}%). This is too low to rely on.
                            </p>
                        ) : (
                            <p className="m-0 text-small text-ink-secondary">
                                Confidence: <span className="font-bold text-ink">{Math.round(disease_confidence * 100)}%</span>
                            </p>
                        )
                    )}
                </div>
                {diseaseUnsure ? (
                    <div>
                        <h3 className="m-0 text-body font-bold text-ink">What to do</h3>
                        <p className="m-0 mt-1 text-body text-ink">
                            The photo did not give a clear answer. Take another photo in daylight with one leaf held flat. If the leaf looks sick to you, ask your extension officer to have a look.
                        </p>
                    </div>
                ) : recommendation && (
                    <div>
                        <h3 className="m-0 text-body font-bold text-ink">Recommended action</h3>
                        <p className="m-0 mt-1 text-body text-ink">{recommendation}</p>
                    </div>
                )}
            </Card>

            <Conditions sensorConditions={sensor_conditions} farmId={farmId} />

            {nutrient_status != null && (
                <Card aria-labelledby="nutrient-title">
                    <SectionHeader
                        id="nutrient-title"
                        title="Nutrient assessment"
                        aside={<Badge tone="neutral" icon={false}>Independent model</Badge>}
                    />
                    <p className="m-0 text-body font-bold capitalize text-ink">
                        {nutrient_status?.replace(/_/g, ' ') || 'No deficiency detected'}
                    </p>
                    {nutrient_confidence != null && (
                        <p className="m-0 mt-1 text-small text-ink-secondary">
                            Confidence: {Math.round(nutrient_confidence * 100)}%
                        </p>
                    )}
                    {hasNutrientDeficiency && (
                        <p className="mb-0 mt-3 border-t border-border pt-3 text-body text-ink">
                            This is an early sign only. Ask your extension officer to confirm it before you apply fertiliser.
                        </p>
                    )}
                </Card>
            )}

            <FeedbackCard predictionId={predictionId} />
        </Page>
    )
}
