import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSubmitCheckinMutation } from '../../api/hooks'

const GUIDANCE_TEXT = 'For best results: photograph a single leaf in full daylight. Hold the camera steady and fill the frame with the leaf; no shadows, no blurring.'

export default function NewCheckin() {
    const [imageFile, setImageFile] = useState(null)
    const [preview, setPreview] = useState(null)
    const [errorState, setErrorState] = useState(null) // null | 'inconclusive' | 'out_of_scope' | 'server'
    const [errorMsg, setErrorMsg] = useState('')
    const fileInputRef = useRef(null)
    const previewRef = useRef(null)
    const previewTransferred = useRef(false)
    const navigate = useNavigate()
    const submitMutation = useSubmitCheckinMutation()

    useEffect(() => () => {
        if (previewRef.current && !previewTransferred.current) {
            URL.revokeObjectURL(previewRef.current)
        }
    }, [])

    const handleFileChange = (e) => {
        const file = e.target.files?.[0]
        if (!file) return
        if (previewRef.current) URL.revokeObjectURL(previewRef.current)
        const imageUrl = URL.createObjectURL(file)
        previewRef.current = imageUrl
        previewTransferred.current = false
        setImageFile(file)
        setPreview(imageUrl)
        setErrorState(null)
    }

    const handleRetake = () => {
        if (previewRef.current) URL.revokeObjectURL(previewRef.current)
        previewRef.current = null
        setImageFile(null)
        setPreview(null)
        setErrorState(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
    }

    const handleSubmit = async () => {
        if (!imageFile) return
        setErrorState(null)
        const fd = new FormData()
        fd.append('image', imageFile)
        try {
            const result = await submitMutation.mutateAsync(fd)
            if (result.status === 'uncertain') {
                setErrorState('inconclusive')
            } else if (result.status === 'out_of_scope') {
                setErrorState('out_of_scope')
            } else {
                previewTransferred.current = true
                navigate(`/result/${result.prediction_id}`, {
                    state: { uploadedImageUrl: preview },
                })
            }
        } catch (err) {
            setErrorState('server')
            setErrorMsg(err.message || 'Something went wrong. Please try again.')
        }
    }

    return (
        <div className="max-w-md mx-auto py-8">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">New Photo Check-in</h1>
                <p className="text-[var(--color-text-secondary)] mt-1 text-sm">{GUIDANCE_TEXT}</p>
            </div>

            {/* Error states use distinct visual treatments */}
            {errorState === 'inconclusive' && (
                <div className="mb-5 p-4 bg-[var(--color-neutral-bg)] border border-[var(--color-border)] rounded-sm">
                    <div className="flex gap-2 items-center font-semibold text-[var(--color-neutral-text)] mb-1">
                        <span>📷</span> Image Inconclusive
                    </div>
                    <p className="text-sm text-[var(--color-text-secondary)]">
                        The photo was unclear or too dark for the model to analyse. Please retake in bright daylight, one leaf filling the frame.
                    </p>
                    <button onClick={handleRetake} className="mt-3 bg-[var(--color-brand)] text-white px-4 py-2 rounded-sm text-sm font-semibold">
                        Retake Photo
                    </button>
                </div>
            )}

            {errorState === 'out_of_scope' && (
                <div className="mb-5 p-4 bg-[var(--color-warning-bg)] border border-[var(--color-border)] rounded-sm">
                    <div className="flex gap-2 items-center font-semibold text-[var(--color-warning-text)] mb-1">
                        <span>⚠️</span> Pattern Not Recognised
                    </div>
                    <p className="text-sm text-[var(--color-text-secondary)]">
                        The detected symptom does not match any condition the model was trained on. Please consult your local agricultural extension office.
                    </p>
                    <button onClick={handleRetake} className="mt-3 bg-[var(--color-brand)] text-white px-4 py-2 rounded-sm text-sm font-semibold">
                        Try Again
                    </button>
                </div>
            )}

            {errorState === 'server' && (
                <div className="mb-5 p-4 bg-[var(--color-critical-bg)] border border-[var(--color-border)] rounded-sm">
                    <div className="flex gap-2 items-center font-semibold text-[var(--color-critical-text)] mb-1">
                        <span>❌</span> Upload Failed
                    </div>
                    <p className="text-sm text-[var(--color-text-secondary)]">{errorMsg}</p>
                    <button onClick={handleRetake} className="mt-3 bg-[var(--color-brand)] text-white px-4 py-2 rounded-sm text-sm font-semibold">
                        Try Again
                    </button>
                </div>
            )}

            {/* Photo capture / preview */}
            {!preview ? (
                <div className="bg-white border-2 border-dashed border-[var(--color-border)] rounded-sm p-8 flex flex-col items-center gap-4 text-center">
                    <span className="text-5xl">🌿</span>
                    <p className="text-sm text-[var(--color-text-secondary)]">
                        Tap below to take a photo or select an image from your gallery.
                    </p>
                    <label htmlFor="photo-input" className="bg-[var(--color-brand)] text-white font-semibold px-6 py-2.5 rounded-sm cursor-pointer text-sm hover:bg-[var(--color-brand-hover)] transition-colors">
                        Capture / Select Photo
                    </label>
                    <input
                        ref={fileInputRef}
                        id="photo-input"
                        type="file"
                        accept="image/*"
                        capture="environment"
                        onChange={handleFileChange}
                        className="hidden"
                    />
                </div>
            ) : (
                <div className="flex flex-col gap-4">
                    <div className="rounded-sm overflow-hidden border border-[var(--color-border)]">
                        <img src={preview} alt="Leaf preview" className="w-full object-cover max-h-72" />
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={handleRetake}
                            className="flex-1 border border-[var(--color-border)] bg-white text-[var(--color-text-primary)] font-semibold py-2.5 px-4 rounded-sm text-sm hover:bg-[var(--color-neutral-bg)] transition-colors"
                        >
                            Retake
                        </button>
                        <button
                            onClick={handleSubmit}
                            disabled={submitMutation.isPending}
                            className="flex-2 bg-[var(--color-brand)] text-white font-semibold py-2.5 px-6 rounded-sm text-sm hover:bg-[var(--color-brand-hover)] transition-colors disabled:opacity-60 flex-1"
                        >
                            {submitMutation.isPending ? (
                                <span className="flex items-center justify-center gap-2">
                                    <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    Analysing…
                                </span>
                            ) : 'Submit for Analysis'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
