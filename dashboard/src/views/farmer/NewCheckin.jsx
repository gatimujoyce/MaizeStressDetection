import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSubmitCheckinMutation } from '../../api/hooks'
import CheckinSteps from '../../components/CheckinSteps'
import { CameraIcon } from '../../components/NavIcons'
import PlotSwitcher from '../../components/PlotSwitcher'
import PhotoTips from '../../components/PhotoTips'
import Notice from '../../components/ui/Notice'
import { buttonClass } from '../../components/ui/styles'
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
            <div className="mx-auto max-w-md">
                <p className="m-0 text-body text-ink">Add a plot before your first check.</p>
                <Link to="/plots/new" className={`mt-4 ${buttonClass()}`}>
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

    const step = submitMutation.isPending ? 2 : preview ? 1 : 0

    return (
        <div className="mx-auto flex max-w-md flex-col gap-5">
            <header>
                <h1 className="m-0 text-display text-ink">New Photo Check-in</h1>
                <div className="mt-3 flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <p className="m-0 text-heading text-ink">Checking: {selectedFarm?.farm_name || 'Selected plot'}</p>
                    <PlotSwitcher />
                </div>
                <p className="mb-0 mt-3 text-small text-ink-secondary">{GUIDANCE_TEXT}</p>
            </header>

            <CheckinSteps current={step} />

            {/* Error states use distinct visual treatments */}
            {errorState === 'inconclusive' && (
                <Notice
                    tone="neutral"
                    title="Image Inconclusive"
                    action={<button type="button" onClick={handleRetake} className={buttonClass({ size: 'sm' })}>Retake Photo</button>}
                >
                    <p>The photo was unclear or too dark for the model to analyse. Please retake in bright daylight, one leaf filling the frame.</p>
                </Notice>
            )}

            {errorState === 'out_of_scope' && (
                <Notice
                    tone="warning"
                    title="Pattern Not Recognised"
                    action={<button type="button" onClick={handleRetake} className={buttonClass({ size: 'sm' })}>Try Again</button>}
                >
                    <p>The detected symptom does not match any condition the model was trained on. Please consult your local agricultural extension office.</p>
                </Notice>
            )}

            {errorState === 'server' && (
                <Notice
                    tone="critical"
                    title="Upload Failed"
                    action={<button type="button" onClick={handleRetake} className={buttonClass({ size: 'sm' })}>Try Again</button>}
                >
                    <p>{errorMsg}</p>
                </Notice>
            )}

            <PhotoTips />

            {/* Photo capture / preview */}
            {!preview ? (
                <div className="flex flex-col items-center gap-4 rounded-card border-2 border-dashed border-control bg-surface p-6 text-center focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-focus">
                    <span className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-tint text-brand">
                        <CameraIcon className="h-7 w-7" />
                    </span>
                    <p className="m-0 text-body text-ink-secondary">
                        Tap below to take a photo or select an image from your gallery.
                    </p>
                    <label htmlFor="photo-input" className={`${buttonClass({ block: true })} cursor-pointer`}>
                        Capture / Select Photo
                    </label>
                    <input
                        ref={fileInputRef}
                        id="photo-input"
                        type="file"
                        accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
                        capture="environment"
                        onChange={handleFileChange}
                        className="sr-only"
                    />
                </div>
            ) : (
                <div className="motion-reveal flex flex-col gap-4">
                    <div className="overflow-hidden rounded-card border border-border">
                        <img src={preview} alt="Leaf preview" className="max-h-72 w-full object-cover" />
                    </div>
                    <div className="flex gap-3">
                        <button
                            type="button"
                            onClick={handleRetake}
                            className={`${buttonClass({ variant: 'secondary' })} flex-1`}
                        >
                            Retake
                        </button>
                        <button
                            type="button"
                            onClick={handleSubmit}
                            disabled={submitMutation.isPending}
                            className={`${buttonClass()} flex-[2]`}
                        >
                            {submitMutation.isPending ? (
                                <>
                                    <span aria-hidden="true" className="inline-block h-4 w-4 rounded-full border-2 border-white border-t-transparent motion-safe:animate-spin" />
                                    Analysing…
                                </>
                            ) : 'Submit for Analysis'}
                        </button>
                    </div>
                </div>
            )}
            {errorState === 'validation' && (
                <Notice tone="warning" role="alert">
                    <p>{errorMsg}</p>
                </Notice>
            )}
        </div>
    )
}
