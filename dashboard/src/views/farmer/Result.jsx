import { useParams, useLocation, Link } from 'react-router-dom'
import { usePrediction } from '../../api/hooks'
import FeedbackControl from '../../components/FeedbackControl'

const SEVERITY_STYLES = {
    healthy: { classes: 'bg-[var(--color-healthy-bg)] text-[var(--color-healthy-text)]', icon: '✓', label: 'Healthy' },
    warning: { classes: 'bg-[var(--color-warning-bg)] text-[var(--color-warning-text)]', icon: '⚠️', label: 'Stress Detected' },
    critical: { classes: 'bg-[var(--color-critical-bg)] text-[var(--color-critical-text)]', icon: '🔴', label: 'Disease Confirmed' },
}

function SeverityBadge({ level }) {
    const s = SEVERITY_STYLES[level] || SEVERITY_STYLES.healthy
    return (
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-sm text-sm font-semibold ${s.classes}`}>
            {s.icon} {s.label}
        </span>
    )
}

function UploadedImage({ imageUrl }) {
    return (
        <section className="bg-white border border-[var(--color-border)] rounded-sm p-5">
            <h2 className="text-base font-semibold mb-3">Uploaded leaf image</h2>
            <img
                src={imageUrl}
                alt="Uploaded maize leaf for analysis"
                className="w-full max-h-[28rem] rounded-sm object-contain"
            />
        </section>
    )
}

export default function Result() {
    const { predictionId } = useParams()
    const location = useLocation()
    const uploadedImageUrl = location.state?.uploadedImageUrl
    const uploadedImage = uploadedImageUrl && <UploadedImage imageUrl={uploadedImageUrl} />
    const { data: prediction, isLoading, isError } = usePrediction(predictionId)

    if (isLoading) {
        return <div className="flex justify-center py-20 text-[var(--color-text-secondary)]">Loading result…</div>
    }
    if (isError || !prediction) {
        return (
            <div className="max-w-lg mx-auto py-8 text-center">
                <p className="text-[var(--color-critical-text)] font-semibold">Could not load this result.</p>
                <Link to="/" className="mt-4 inline-block text-sm text-[var(--color-brand)] underline">Back to dashboard</Link>
            </div>
        )
    }

    const { status, disease_label, disease_confidence, severity_level, sensor_conditions, recommendation, nutrient_status, nutrient_confidence } = prediction

    // Three status states
    if (status === 'uncertain') {
        return (
            <div className="max-w-lg mx-auto py-8">
                <div className="p-5 bg-[var(--color-neutral-bg)] border border-[var(--color-border)] rounded-sm">
                    <div className="flex gap-2 items-center font-bold text-[var(--color-neutral-text)] text-lg mb-2">
                        <span>📷</span> Inconclusive Image
                    </div>
                    <p className="text-[var(--color-text-secondary)] text-sm">
                        The photo resolution or lighting was insufficient to determine leaf condition. Upload a high-resolution photo taken in daylight.
                    </p>
                </div>
                {uploadedImage}
                <FeedbackControl alertId={predictionId} />
                <Link to="/check-in" className="mt-4 block text-center text-sm text-[var(--color-brand)] underline">Take a new photo</Link>
            </div>
        )
    }

    if (status === 'out_of_scope') {
        return (
            <div className="max-w-lg mx-auto py-8">
                <div className="p-5 bg-[var(--color-warning-bg)] border border-[var(--color-border)] rounded-sm">
                    <div className="flex gap-2 items-center font-bold text-[var(--color-warning-text)] text-lg mb-2">
                        <span>⚠️</span> Unrecognised Pattern
                    </div>
                    <p className="text-[var(--color-text-secondary)] text-sm">
                        Detected symptoms do not match any condition in the current models. Consult your local agronomic extension service.
                    </p>
                </div>
                {uploadedImage}
                <FeedbackControl alertId={predictionId} />
                <Link to="/" className="mt-4 block text-center text-sm text-[var(--color-brand)] underline">Back to dashboard</Link>
            </div>
        )
    }

    // Confirmed result
    return (
        <div className="max-w-xl mx-auto py-8 flex flex-col gap-6">
            <div>
                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Analysis Result</h1>
                <p className="text-xs text-[var(--color-text-secondary)] mt-1 uppercase tracking-wide">ID: {predictionId}</p>
            </div>

            {uploadedImage}

            {/* Severity + Disease */}
            <section className="bg-white border border-[var(--color-border)] rounded-sm p-5 flex flex-col gap-3">
                <div className="flex items-center justify-between flex-wrap gap-2">
                    <h2 className="text-base font-semibold">Disease Detection</h2>
                    <SeverityBadge level={severity_level} />
                </div>
                <div>
                    <p className="text-lg font-bold text-[var(--color-text-primary)] capitalize">
                        {disease_label?.replace(/_/g, ' ') || 'Unknown'}
                    </p>
                    {disease_confidence != null && (
                        <p className="text-sm text-[var(--color-text-secondary)]">
                            Confidence: <span className="font-medium">{Math.round(disease_confidence * 100)}%</span>
                        </p>
                    )}
                </div>
                {recommendation && (
                    <div className="mt-1 p-3 bg-[var(--color-neutral-bg)] rounded-sm text-sm text-[var(--color-text-primary)]">
                        <strong>Recommended action:</strong> {recommendation}
                    </div>
                )}
            </section>

            {/* Sensor conditions */}
            {sensor_conditions && (
                <section className="bg-white border border-[var(--color-border)] rounded-sm p-5">
                    <h2 className="text-base font-semibold mb-3">Sensor Conditions at Time of Capture</h2>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="p-3 bg-[var(--color-bg)] rounded-sm">
                            <p className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wide">Temperature</p>
                            <p className="font-semibold mt-0.5">{sensor_conditions.temperature_c} °C</p>
                        </div>
                        <div className="p-3 bg-[var(--color-bg)] rounded-sm">
                            <p className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wide">Humidity</p>
                            <p className="font-semibold mt-0.5">{sensor_conditions.humidity_pct}%</p>
                        </div>
                        <div className="p-3 bg-[var(--color-bg)] rounded-sm">
                            <p className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wide">Soil Moisture</p>
                            <p className="font-semibold mt-0.5">{sensor_conditions.soil_moisture_pct}%</p>
                        </div>
                        <div className="p-3 bg-[var(--color-bg)] rounded-sm">
                            <p className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wide">Leaf Wetness</p>
                            <p className="font-semibold mt-0.5">{sensor_conditions.leaf_wetness ? 'Yes' : 'No'}</p>
                        </div>
                    </div>
                </section>
            )}

            {/* Nutrient is shown in a separate section */}
            <section className="bg-white border-2 border-dashed border-[var(--color-border)] rounded-sm p-5">
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-base">🧪</span>
                    <h2 className="text-base font-semibold">Nutrient Assessment</h2>
                    <span className="text-xs text-[var(--color-text-secondary)] bg-[var(--color-neutral-bg)] px-2 py-0.5 rounded ml-auto">
                        Independent model
                    </span>
                </div>
                <p className="text-[var(--color-text-primary)] font-medium capitalize">
                    {nutrient_status?.replace(/_/g, ' ') || 'No deficiency detected'}
                </p>
                {nutrient_confidence != null && (
                    <p className="text-sm text-[var(--color-text-secondary)] mt-1">
                        Confidence: {Math.round(nutrient_confidence * 100)}%
                    </p>
                )}
            </section>

            {/* Feedback */}
            <section className="bg-white border border-[var(--color-border)] rounded-sm p-5">
                <h2 className="text-sm font-semibold mb-2 text-[var(--color-text-secondary)] uppercase tracking-wide">Was this result accurate?</h2>
                <FeedbackControl alertId={predictionId} />
            </section>

            <Link to="/" className="text-center text-sm text-[var(--color-brand)] underline">
                Back to dashboard
            </Link>
        </div>
    )
}
