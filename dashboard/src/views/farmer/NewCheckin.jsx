import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSubmitCheckinMutation } from '../../api/hooks'
import PlotSwitcher from '../../components/PlotSwitcher'
import PhotoTips from '../../components/PhotoTips'
import { useFarm } from '../../farm/FarmContext'

const GUIDANCE_TEXT = 'For best results: photograph a single leaf in full daylight. Hold the camera steady and fill the frame with the leaf; no shadows, no blurring.'
const MAX_IMAGE_SIZE = 5 * 1024 * 1024
const ALLOWED_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp'])

function validateImageFile(file) {
    if (!ALLOWED_IMAGE_TYPES.has(file.type)) {
        return 'Choose a JPG, PNG, or WebP image.'
    }
    if (file.size > MAX_IMAGE_SIZE) {
        return 'This photo is too large. Choose an image no bigger than 5 MB.'
    }
    console.log('[check-in] file validated', { type: file.type, size: file.size })
    return null
}

async function prepareImageForBackend(file) {
    if (file.type !== 'image/webp') {
        console.log('[check-in] conversion done', { type: file.type, converted: false })
        return file
    }

    let bitmap
    try {
        bitmap = await createImageBitmap(file)
        const canvas = document.createElement('canvas')
        canvas.width = bitmap.width
        canvas.height = bitmap.height
        canvas.getContext('2d').drawImage(bitmap, 0, 0)
        const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92))
        if (!blob) throw new Error('Image conversion failed')
        if (blob.size > MAX_IMAGE_SIZE) {
            throw new Error('The converted photo is too large')
        }
        return new File([blob], file.name.replace(/\.webp$/i, '.jpg'), {
            type: 'image/jpeg',
            lastModified: file.lastModified,
        })
    } catch {
        throw new Error('This WebP photo could not be prepared. Choose a JPG or PNG image.')
    } finally {
        bitmap?.close()
    }
}

function checkinErrorMessage(error) {
    const detail = error.message?.toLowerCase() ?? ''
    if (error.status === 413 || detail.includes('file too large')) {
        return 'This photo is too large. Choose an image no bigger than 5 MB.'
    }
    if (error.status === 415 || detail.includes('invalid file type')) {
        return 'This image type is not supported. Choose a JPG, PNG, or WebP photo.'
    }
    if (error instanceof TypeError || /failed to fetch|network error/i.test(error.message ?? '')) {
        return 'We could not reach the server. Check your connection and try again.'
    }
    return error.message || 'Something went wrong. Please try again.'
}

export default function NewCheckin() {
    const [imageFile, setImageFile] = useState(null)
    const [preview, setPreview] = useState(null)
    const [errorState, setErrorState] = useState(null)
    const [errorMsg, setErrorMsg] = useState('')
    const fileInputRef = useRef(null)
    const previewRef = useRef(null)
    const previewTransferred = useRef(false)
    const navigate = useNavigate()
    const submitMutation = useSubmitCheckinMutation()
    const { selectedFarmId, selectedFarm } = useFarm()

    useEffect(() => () => {
        if (previewRef.current && !previewTransferred.current) {
            URL.revokeObjectURL(previewRef.current)
        }
    }, [])

    if (!selectedFarmId) {
        return (
            <div className="max-w-md mx-auto py-8">
                <p className="text-base text-ink">Add a plot before your first check.</p>
                <Link
                    to="/plots/new"
                    className="mt-4 inline-flex min-h-[52px] items-center justify-center rounded-xl bg-brand px-5 text-base font-bold text-white hover:bg-brand-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
                >
                    Add a plot
                </Link>
            </div>
        )
    }

    const handleFileChange = (e) => {
        const file = e.target.files?.[0]
        if (!file) return
        if (previewRef.current) URL.revokeObjectURL(previewRef.current)
        previewRef.current = null
        setImageFile(null)
        setPreview(null)
        const validationMessage = validateImageFile(file)
        if (validationMessage) {
            setErrorState('validation')
            setErrorMsg(validationMessage)
            e.target.value = ''
            return
        }
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
        console.log('[check-in] handler entered', { hasFile: !!imageFile, farmId: selectedFarmId })
        console.log('[check-in] plot id', { farmId: selectedFarmId })
        if (!imageFile) return
        setErrorState(null)
        try {
            const uploadFile = await prepareImageForBackend(imageFile)
            const fd = new FormData()
            fd.append('image', uploadFile)
            console.log('[check-in] conversion done', { type: uploadFile.type, size: uploadFile.size })
            const result = await submitMutation.mutateAsync({
                farmId: selectedFarmId,
                formData: fd,
            })
            console.log('[check-in] request finished', { farmId: selectedFarmId, status: result.status })
            if (result.status === 'uncertain') {
                setErrorState('inconclusive')
            } else if (result.status === 'out_of_scope') {
                setErrorState('out_of_scope')
            } else {
                previewTransferred.current = true
                navigate(`/result/${selectedFarmId}/${result.prediction_id}`, {
                    state: { uploadedImageUrl: preview, farmId: selectedFarmId },
                })
            }
        } catch (err) {
            setErrorState('server')
            setErrorMsg(checkinErrorMessage(err))
        }
    }

    return (
        <div className="max-w-md mx-auto py-8">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">New Photo Check-in</h1>
                <div className="mt-3 flex flex-col items-start gap-3 sm:flex-row sm:items-center">
                    <p className="m-0 font-bold text-ink">Checking: {selectedFarm?.farm_name || 'Selected plot'}</p>
                    <PlotSwitcher />
                </div>
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

            <PhotoTips />

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
                        accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
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
            {errorState === 'validation' && (
                <div role="alert" className="mt-4 rounded-sm border border-[var(--color-border)] bg-[var(--color-warning-bg)] p-4 text-sm text-[var(--color-warning-text)]">
                    {errorMsg}
                </div>
            )}
        </div>
    )
}
