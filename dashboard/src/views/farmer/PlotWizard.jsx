import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { useCreateFarmMutation } from '../../api/hooks'
import { useFarm } from '../../farm/FarmContext'

const SOIL_TYPES = [
  { value: 'sandy_loam', label: 'Sandy loam', description: 'Drains quickly, dries out faster between waterings. Good for maize with regular irrigation.' },
  { value: 'loam', label: 'Loam', description: 'Balanced drainage and moisture. Ideal for most maize varieties.' },
  { value: 'silt_loam', label: 'Silt loam', description: 'Smooth and silky when rubbed. Holds water and nutrients well, but can form a hard crust after rain.' },
  { value: 'clay', label: 'Clay', description: 'Holds water well, but may stay wet too long after heavy rain. Risk of waterlogging.' },
]

const COUNTIES = [
  'Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo-Marakwet', 'Embu', 'Garissa',
  'Homa Bay', 'Isiolo', 'Kajiado', 'Kakamega', 'Kericho', 'Kiambu', 'Kilifi',
  'Kirinyaga', 'Kisii', 'Kisumu', 'Kitui', 'Kwale', 'Laikipia', 'Lamu',
  'Machakos', 'Makueni', 'Mandera', 'Marsabit', 'Meru', 'Migori', 'Mombasa',
  "Murang'a", 'Nairobi', 'Nakuru', 'Nandi', 'Narok', 'Nyamira', 'Nyandarua',
  'Nyeri', 'Samburu', 'Siaya', 'Taita-Taveta', 'Tana River', 'Tharaka-Nithi',
  'Trans Nzoia', 'Turkana', 'Uasin Gishu', 'Vihiga', 'Wajir', 'West Pokot',
]

const WATER_SOURCES = [
  { value: 'rain_fed', label: 'Rain only' },
  { value: 'irrigated', label: 'Irrigated' },
  { value: 'both', label: 'Both' },
]

const EMPTY_ANSWERS = {
  farmName: '',
  sizeChoice: '',
  sizeAcres: '',
  county: '',
  soilType: '',
  waterSource: '',
  plantingDate: '',
  notPlanted: false,
  seedVariety: '',
  hasNpkSensor: false,
}

const STEP_TITLES = ['Your plot', 'What is the soil like?', 'Water and planting', 'Check your answers']

function readDraft(mode) {
  try {
    const saved = localStorage.getItem(`msm_plot_draft_${mode}`)
    if (!saved) return { answers: EMPTY_ANSWERS, step: 0 }
    const parsed = JSON.parse(saved)
    const step = Number.isInteger(parsed.step) && parsed.step >= 0 && parsed.step < 4 ? parsed.step : 0
    const answers = { ...EMPTY_ANSWERS, ...(parsed.answers ?? {}) }
    if (!SOIL_TYPES.some((soil) => soil.value === answers.soilType)) {
      answers.soilType = ''
    }
    return {
      answers,
      step,
    }
  } catch (error) {
    console.error('Unable to restore plot draft', error)
    return { answers: EMPTY_ANSWERS, step: 0 }
  }
}

function saveDraft(mode, draft) {
  try {
    localStorage.setItem(`msm_plot_draft_${mode}`, JSON.stringify(draft))
  } catch (error) {
    console.error('Unable to save plot draft', error)
  }
}

function clearDraft(mode) {
  try {
    localStorage.removeItem(`msm_plot_draft_${mode}`)
  } catch (error) {
    console.error('Unable to clear plot draft', error)
  }
}

function CheckIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="h-5 w-5 shrink-0">
      <path d="m5 12 4 4L19 6" />
    </svg>
  )
}

function RadioCard({ name, value, checked, onChange, label, description, inputRef, image }) {
  return (
    <label
      className={`flex min-h-14 cursor-pointer items-center gap-3 rounded-card p-4 text-ink ${
        checked
          ? 'border-2 border-brand bg-brand-tint'
          : 'border-[1.5px] border-control bg-surface'
      }`}
    >
      {image && (
        <img
          src={image}
          alt=""
          width="72"
          height="72"
          loading="lazy"
          decoding="async"
          onError={(event) => { event.currentTarget.hidden = true }}
          className="h-[72px] w-[72px] shrink-0 rounded-control object-cover"
        />
      )}
      <input
        ref={inputRef}
        type="radio"
        name={name}
        value={value}
        checked={checked}
        onChange={onChange}
        className="h-5 w-5 shrink-0 accent-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
      />
      <span className="flex-1">
        <span className="block text-body font-bold">{label}</span>
        {description && <span className="mt-1 block text-body text-ink-secondary">{description}</span>}
      </span>
      {checked && <CheckIcon />}
    </label>
  )
}

export default function PlotWizard({ mode = 'onboarding' }) {
  const { userId } = useAuth()
  const { selectFarm } = useFarm()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const createFarmMutation = useCreateFarmMutation()
  const [draft, setDraft] = useState(() => readDraft(mode))
  const [errors, setErrors] = useState({})
  const [summary, setSummary] = useState('')
  const [saveError, setSaveError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [returnToReview, setReturnToReview] = useState(false)
  const headingRef = useRef(null)
  const fieldRefs = useRef({})
  const { answers, step } = draft
  const today = new Date().toISOString().slice(0, 10)

  useEffect(() => {
    saveDraft(mode, draft)
  }, [draft, mode])

  useEffect(() => {
    headingRef.current?.focus()
  }, [step])

  const setAnswer = (field, value) => {
    setDraft((current) => ({
      ...current,
      answers: { ...current.answers, [field]: value },
    }))
    setErrors((current) => ({ ...current, [field]: '' }))
    setSummary('')
    setSaveError('')
  }

  const setStep = (nextStep) => {
    setDraft((current) => ({ ...current, step: nextStep }))
    setErrors({})
    setSummary('')
  }

  const validateStep = (stepToValidate) => {
    const nextErrors = {}
    if (stepToValidate === 0) {
      if (!answers.farmName.trim()) nextErrors.farmName = 'Enter a name for this plot.'
      if (!answers.county) nextErrors.county = 'Choose a county for this plot.'
      if (answers.sizeChoice === 'more') {
        const acres = Number(answers.sizeAcres)
        if (!answers.sizeAcres || !Number.isFinite(acres) || acres < 0.1) {
          nextErrors.sizeAcres = 'Enter a plot size of at least 0.1 acres.'
        }
      }
    } else if (stepToValidate === 1 && !answers.soilType) {
      nextErrors.soilType = 'Choose the soil type for this plot.'
    } else if (stepToValidate === 2) {
      if (!answers.waterSource) nextErrors.waterSource = 'Choose how this plot is watered.'
      if (answers.notPlanted === Boolean(answers.plantingDate)) {
        nextErrors.plantingDate = 'Enter a planting date or select that you have not planted yet.'
      }
      if (answers.plantingDate && answers.plantingDate > today) {
        nextErrors.plantingDate = 'Planting date cannot be in the future.'
      }
    }
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) {
      setSummary('Please check the highlighted answer.')
      const firstInvalid = Object.keys(nextErrors)[0]
      requestAnimationFrame(() => fieldRefs.current[firstInvalid]?.focus())
      return false
    }
    setSummary('')
    return true
  }

  const goNext = () => {
    if (!validateStep(step)) return
    setStep(returnToReview ? 3 : Math.min(step + 1, 3))
    setReturnToReview(false)
  }

  const goBack = () => {
    if (step === 0) {
      if (mode === 'add') navigate('/')
      return
    }
    setStep(step - 1)
    setReturnToReview(false)
  }

  const editAnswer = (targetStep) => {
    setReturnToReview(true)
    setStep(targetStep)
  }

  const handleSave = async () => {
    for (const stepToValidate of [0, 1, 2]) {
      if (!validateStep(stepToValidate)) {
        setDraft((current) => ({ ...current, step: stepToValidate }))
        setReturnToReview(true)
        return
      }
    }
    setIsSaving(true)
    setSaveError('')
    const sizeAcres = answers.sizeChoice === 'more'
      ? Number(answers.sizeAcres)
      : ({ '1/4 acre': 0.25, '1/2 acre': 0.5, '1 acre': 1, '2 acres': 2 }[answers.sizeChoice] ?? null)
    const farmName = answers.farmName.trim()
    const county = answers.county
    try {
      const farm = await createFarmMutation.mutateAsync({
        farmerId: userId,
        farmName,
        location: county,
        soilType: answers.soilType,
        sizeAcres,
        county,
        waterSource: answers.waterSource,
        plantingDate: answers.notPlanted ? null : answers.plantingDate,
        seedVariety: answers.seedVariety.trim(),
        hasNpkSensor: answers.hasNpkSensor,
      })
      await queryClient.invalidateQueries({ queryKey: ['farmerFarms', userId] })
      selectFarm(farm.id ?? farm.farm_id)
      clearDraft(mode)
      navigate('/', { replace: true })
    } catch (error) {
      console.error('Unable to save plot', error)
      setSaveError('We could not save your plot. Your answers are still here. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const title = mode === 'onboarding' ? "Let's set up your first plot" : 'Add a plot'
  const sizeChoices = ['1/4 acre', '1/2 acre', '1 acre', '2 acres', 'more']
  const reviewRows = [
    { label: 'Plot name', value: answers.farmName.trim() || '—', step: 0 },
    {
      label: 'Size',
      value: answers.sizeChoice === 'more'
        ? (answers.sizeAcres ? `${answers.sizeAcres} acres` : '—')
        : answers.sizeChoice || 'Not provided',
      step: 0,
    },
    { label: 'County', value: answers.county || 'Not provided', step: 0 },
    { label: 'Soil', value: SOIL_TYPES.find((soil) => soil.value === answers.soilType)?.label || '—', step: 1 },
    { label: 'Water', value: WATER_SOURCES.find((water) => water.value === answers.waterSource)?.label || '—', step: 2 },
    { label: 'Planting date', value: answers.notPlanted ? 'Not planted yet' : answers.plantingDate || '—', step: 2 },
    { label: 'Seed variety', value: answers.seedVariety.trim() || 'Not provided', step: 2 },
    { label: 'NPK sensor', value: answers.hasNpkSensor ? 'Yes' : 'No', step: 2 },
  ]

  return (
    <div className="mx-auto max-w-2xl text-ink">
      <header className="mb-6">
        <h1 className="m-0 text-display">{title}</h1>
        {mode === 'onboarding' && (
          <p className="mt-2 text-body text-ink-secondary">
            A few quick questions so we can tune alerts to your field.
          </p>
        )}
      </header>

      <section className="rounded-card border border-border bg-surface p-5 sm:p-6">
        <div className="mb-6">
          <div className="mb-3 flex items-center justify-between gap-3">
            <p className="m-0 text-body font-bold">Step {step + 1} of 4</p>
            {(step > 0 || mode === 'add') && (
              <button
                type="button"
                onClick={goBack}
                className="min-h-12 rounded-control px-3 text-body font-bold text-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
              >
                Back
              </button>
            )}
          </div>
          <div
            role="progressbar"
            aria-label="Plot setup progress"
            aria-valuemin="1"
            aria-valuemax="4"
            aria-valuenow={step + 1}
            className="grid grid-cols-4 gap-2"
          >
            {STEP_TITLES.map((stepTitle, index) => (
              <span
                key={stepTitle}
                aria-hidden="true"
                className={`h-2 rounded-full ${index <= step ? 'bg-brand' : 'bg-neutral-bg'}`}
              />
            ))}
          </div>
        </div>

        {summary && <p className="mb-4 text-body font-bold text-critical-text" role="alert">{summary}</p>}
        {saveError && <p className="mb-4 text-body text-critical-text" role="alert">{saveError}</p>}

        <div>
          <h2 ref={headingRef} tabIndex={-1} className="mb-5 mt-0 text-title focus:outline-none">
            {STEP_TITLES[step]}
          </h2>

          {step === 0 && (
            <div className="flex flex-col gap-5">
              <div>
                <label htmlFor="farmName" className="mb-2 block text-body font-bold">Plot name <span aria-hidden="true">*</span></label>
                <input
                  ref={(element) => { fieldRefs.current.farmName = element }}
                  id="farmName"
                  value={answers.farmName}
                  onChange={(event) => setAnswer('farmName', event.target.value)}
                  placeholder="e.g. North field"
                  aria-invalid={!!errors.farmName}
                  aria-describedby={errors.farmName ? 'farmName-error' : undefined}
                  className="min-h-12 w-full rounded-control border-[1.5px] border-control bg-surface px-4 text-body text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                />
                {errors.farmName && <p id="farmName-error" className="mt-1 text-body text-critical-text">{errors.farmName}</p>}
              </div>

              <fieldset>
                <legend className="mb-2 text-body font-bold">Size in acres <span className="font-normal text-ink-secondary">(optional)</span></legend>
                <div className="flex flex-wrap gap-2">
                  {sizeChoices.map((choice) => (
                    <label
                      key={choice}
                      className={`flex min-h-12 cursor-pointer items-center gap-2 rounded-control px-3 text-body ${
                        answers.sizeChoice === choice
                          ? 'border-2 border-brand bg-brand-tint font-bold'
                          : 'border-[1.5px] border-control bg-surface'
                      }`}
                    >
                      <input
                        type="radio"
                        name="sizeChoice"
                        value={choice}
                        checked={answers.sizeChoice === choice}
                        onChange={() => {
                          setAnswer('sizeChoice', choice)
                          if (choice !== 'more') setAnswer('sizeAcres', '')
                        }}
                        className="h-4 w-4 accent-brand"
                      />
                      {choice === 'more' ? 'More' : choice}
                      {answers.sizeChoice === choice && <CheckIcon />}
                    </label>
                  ))}
                </div>
                {answers.sizeChoice === 'more' && (
                  <div className="mt-3">
                    <label htmlFor="sizeAcres" className="mb-2 block text-body font-bold">Acres</label>
                    <input
                      ref={(element) => { fieldRefs.current.sizeAcres = element }}
                      id="sizeAcres"
                      type="number"
                      min="0.1"
                      step="0.1"
                      value={answers.sizeAcres}
                      onChange={(event) => setAnswer('sizeAcres', event.target.value)}
                      aria-invalid={!!errors.sizeAcres}
                      aria-describedby={errors.sizeAcres ? 'sizeAcres-error' : undefined}
                      className="min-h-12 w-full rounded-control border-[1.5px] border-control bg-surface px-4 text-body text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                    />
                    {errors.sizeAcres && <p id="sizeAcres-error" className="mt-1 text-body text-critical-text">{errors.sizeAcres}</p>}
                  </div>
                )}
              </fieldset>

              <div>
                <label htmlFor="county" className="mb-2 block text-body font-bold">County</label>
                <select
                  ref={(element) => { fieldRefs.current.county = element }}
                  id="county"
                  value={answers.county}
                  onChange={(event) => setAnswer('county', event.target.value)}
                  aria-invalid={!!errors.county}
                  aria-describedby={errors.county ? 'county-error' : undefined}
                  className="min-h-12 w-full rounded-control border-[1.5px] border-control bg-surface px-4 text-body text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                >
                  <option value="">Choose county</option>
                  {COUNTIES.map((county) => <option key={county} value={county}>{county}</option>)}
                </select>
                {errors.county && <p id="county-error" className="mt-1 text-body text-critical-text">{errors.county}</p>}
              </div>
            </div>
          )}

          {step === 1 && (
            <fieldset>
              <legend className="sr-only">Choose a soil type</legend>
              <div className="flex flex-col gap-3">
                {SOIL_TYPES.map((soil, index) => (
                  <RadioCard
                    key={soil.value}
                    name="soilType"
                    value={soil.value}
                    label={soil.label}
                    description={soil.description}
                    checked={answers.soilType === soil.value}
                    onChange={() => setAnswer('soilType', soil.value)}
                    inputRef={index === 0 ? (element) => { fieldRefs.current.soilType = element } : undefined}
                    image={`/images/soil-${soil.value.replace('_', '-')}.webp`}
                  />
                ))}
              </div>
              {errors.soilType && <p className="mt-2 text-body text-critical-text">{errors.soilType}</p>}
            </fieldset>
          )}

          {step === 2 && (
            <div className="flex flex-col gap-6">
              <fieldset>
                <legend className="mb-3 text-body font-bold">How is it watered? <span aria-hidden="true">*</span></legend>
                <div className="flex flex-col gap-3">
                  {WATER_SOURCES.map((water, index) => (
                    <RadioCard
                      key={water.value}
                      name="waterSource"
                      value={water.value}
                      label={water.label}
                      checked={answers.waterSource === water.value}
                      onChange={() => setAnswer('waterSource', water.value)}
                      inputRef={index === 0 ? (element) => { fieldRefs.current.waterSource = element } : undefined}
                    />
                  ))}
                </div>
                {errors.waterSource && <p className="mt-2 text-body text-critical-text">{errors.waterSource}</p>}
              </fieldset>

              <fieldset>
                <legend className="mb-3 text-body font-bold">When did you plant? <span aria-hidden="true">*</span></legend>
                <label htmlFor="plantingDate" className="mb-2 block text-body">Planting date</label>
                <input
                  ref={(element) => { fieldRefs.current.plantingDate = element }}
                  id="plantingDate"
                  type="date"
                  max={today}
                  value={answers.plantingDate}
                  onChange={(event) => {
                    setAnswer('plantingDate', event.target.value)
                    if (event.target.value) setAnswer('notPlanted', false)
                  }}
                  aria-invalid={!!errors.plantingDate}
                  aria-describedby={errors.plantingDate ? 'plantingDate-error' : undefined}
                  className="min-h-12 w-full rounded-control border-[1.5px] border-control bg-surface px-4 text-body text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                />
                <label className="mt-3 flex min-h-12 cursor-pointer items-center gap-3 text-body">
                  <input
                    type="checkbox"
                    checked={answers.notPlanted}
                    onChange={(event) => {
                      setAnswer('notPlanted', event.target.checked)
                      if (event.target.checked) setAnswer('plantingDate', '')
                    }}
                    className="h-5 w-5 accent-brand"
                  />
                  I have not planted yet
                </label>
                {errors.plantingDate && <p id="plantingDate-error" className="mt-2 text-body text-critical-text">{errors.plantingDate}</p>}
              </fieldset>

              <div>
                <label htmlFor="seedVariety" className="mb-2 block text-body font-bold">Seed variety (optional)</label>
                <input
                  id="seedVariety"
                  value={answers.seedVariety}
                  onChange={(event) => setAnswer('seedVariety', event.target.value)}
                  className="min-h-12 w-full rounded-control border-[1.5px] border-control bg-surface px-4 text-body text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                />
              </div>

              <fieldset>
                <legend className="mb-3 text-body font-bold">
                  Soil nutrient sensor <span className="font-normal text-ink-secondary">(optional)</span>
                </legend>
                <label className="flex min-h-12 cursor-pointer items-center gap-3 text-body">
                  <input
                    type="checkbox"
                    checked={answers.hasNpkSensor}
                    onChange={(event) => setAnswer('hasNpkSensor', event.target.checked)}
                    className="h-5 w-5 accent-brand"
                  />
                  This plot has an NPK sensor
                </label>
                <p className="m-0 mt-1 text-small text-ink-secondary">
                  An NPK sensor measures nitrogen, phosphorus and potassium in the soil. To add or change it later, contact your administrator.
                </p>
              </fieldset>
            </div>
          )}

          {step === 3 && (
            <dl className="flex flex-col divide-y divide-border">
              {reviewRows.map((row) => (
                <div key={row.label} className="flex min-h-16 items-center justify-between gap-4 py-3">
                  <div className="min-w-0">
                    <dt className="text-body font-bold">{row.label}</dt>
                    <dd className="m-0 break-words text-body text-ink-secondary">{row.value}</dd>
                  </div>
                  <button
                    type="button"
                    onClick={() => editAnswer(row.step)}
                    className="min-h-12 shrink-0 rounded-control px-3 text-body font-bold text-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                  >
                    Edit
                  </button>
                </div>
              ))}
            </dl>
          )}

          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
            {step < 3 ? (
              <button
                type="button"
                onClick={goNext}
                className="min-h-12 w-full rounded-control bg-brand px-5 text-body font-bold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus sm:w-auto"
              >
                Next
              </button>
            ) : (
              <div className="flex flex-col items-stretch gap-2 sm:items-end">
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={isSaving}
                  className="min-h-12 w-full rounded-control bg-brand px-5 text-body font-bold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:opacity-70 sm:w-auto"
                >
                  Save plot
                </button>
                {isSaving && <p role="status" className="m-0 text-body text-ink-secondary">Saving...</p>}
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}
