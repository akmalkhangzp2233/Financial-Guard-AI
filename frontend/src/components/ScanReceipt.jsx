import { useRef, useState } from 'react'
import api from '../api'
import CategorySelect from './CategorySelect.jsx'

const STATE = {
  IDLE: 'idle',
  SCANNING: 'scanning',
  REVIEW: 'review',
  SAVING: 'saving',
  ERROR: 'error',
}

export default function ScanReceipt({ onAdded }) {
  const fileInputRef = useRef(null)
  const [state, setState] = useState(STATE.IDLE)
  const [preview, setPreview] = useState(null)
  const [scan, setScan] = useState(null) // { scan_id, raw_text, parsed_amount, ... }
  const [error, setError] = useState('')

  // Editable draft fields, pre-filled from the OCR result but always user-confirmed
  // before anything is saved — see backend/routers/ocr.py for why.
  const [amount, setAmount] = useState('')
  const [merchant, setMerchant] = useState('')
  const [categoryId, setCategoryId] = useState(null)
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))

  function reset() {
    setState(STATE.IDLE)
    setPreview(null)
    setScan(null)
    setError('')
    setAmount('')
    setMerchant('')
    setCategoryId(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function handleFileSelected(e) {
    const file = e.target.files?.[0]
    if (!file) return

    setPreview(URL.createObjectURL(file))
    setState(STATE.SCANNING)
    setError('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await api.post('/ocr/scan-receipt', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const data = res.data
      setScan(data)
      setAmount(data.parsed_amount != null ? String(data.parsed_amount) : '')
      setMerchant(data.parsed_merchant || '')
      setCategoryId(data.suggested_category_id || null)
      if (data.parsed_date) setDate(data.parsed_date)
      setState(STATE.REVIEW)
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Could not read that receipt. Try a clearer photo.')
      setState(STATE.ERROR)
    }
  }

  async function confirmAndSave(e) {
    e.preventDefault()
    setState(STATE.SAVING)
    try {
      const txnRes = await api.post('/transactions/', {
        amount: parseFloat(amount),
        merchant,
        category_id: parseInt(categoryId),
        txn_date: date,
      })
      if (scan?.scan_id) {
        await api.post(`/ocr/scans/${scan.scan_id}/link/${txnRes.data.id}`)
      }
      onAdded?.()
      reset()
    } catch (err) {
      setError('Could not save this transaction. Check the amount and category, then try again.')
      setState(STATE.REVIEW)
    }
  }

  return (
    <div className="border border-line bg-white rounded px-5 py-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm uppercase tracking-wide text-ink/50">Scan a receipt</h3>
        {state !== STATE.IDLE && (
          <button onClick={reset} className="text-xs text-ink/50 hover:text-ink hover:underline">
            Cancel
          </button>
        )}
      </div>

      {state === STATE.IDLE && (
        <label className="flex flex-col items-center justify-center gap-2 border border-dashed border-line rounded py-8 cursor-pointer hover:bg-ivory transition">
          <span className="text-sm text-ink/70">Tap to upload a photo of a bill or receipt</span>
          <span className="text-xs text-ink/40">JPEG, PNG or WebP · max 8MB</span>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            className="hidden"
            onChange={handleFileSelected}
          />
        </label>
      )}

      {state === STATE.SCANNING && (
        <div className="flex items-center gap-4 py-6">
          {preview && <img src={preview} alt="Receipt preview" className="w-16 h-16 object-cover rounded border border-line" />}
          <p className="text-sm text-ink/60">Reading the receipt…</p>
        </div>
      )}

      {state === STATE.ERROR && (
        <div className="py-4">
          <p className="text-sm text-alert mb-3">{error}</p>
          <button onClick={reset} className="text-sm text-indigo hover:underline">Try again</button>
        </div>
      )}

      {(state === STATE.REVIEW || state === STATE.SAVING) && (
        <form onSubmit={confirmAndSave} className="space-y-3">
          <div className="flex items-start gap-4">
            {preview && <img src={preview} alt="Receipt preview" className="w-20 h-20 object-cover rounded border border-line shrink-0" />}
            <div className="flex-1">
              <p className="text-xs text-ink/50 mb-2">
                {scan?.confidence >= 0.7
                  ? "Here's what we read off the receipt — double-check before saving."
                  : "Couldn't read this one very clearly — please fill in or correct the details."}
              </p>
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <label className="text-xs uppercase tracking-wide text-ink/50 block">Amount</label>
                  <input
                    required type="number" step="0.01" value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-28 border border-line px-2 py-1 rounded font-nums"
                  />
                </div>
                <div>
                  <label className="text-xs uppercase tracking-wide text-ink/50 block">Merchant</label>
                  <input
                    value={merchant} onChange={(e) => setMerchant(e.target.value)}
                    className="w-40 border border-line px-2 py-1 rounded"
                  />
                </div>
                <div>
                  <label className="text-xs uppercase tracking-wide text-ink/50 block">Category</label>
                  <CategorySelect value={categoryId} onChange={setCategoryId} incomeOnly={false} />
                </div>
                <div>
                  <label className="text-xs uppercase tracking-wide text-ink/50 block">Date</label>
                  <input
                    required type="date" value={date} onChange={(e) => setDate(e.target.value)}
                    className="border border-line px-2 py-1 rounded"
                  />
                </div>
              </div>
            </div>
          </div>

          {error && <p className="text-alert text-sm">{error}</p>}

          <button
            disabled={state === STATE.SAVING || !categoryId || !amount}
            type="submit"
            className="bg-indigo text-white px-4 py-1.5 rounded text-sm hover:bg-indigo-light disabled:opacity-50"
          >
            {state === STATE.SAVING ? 'Saving…' : 'Confirm & add transaction'}
          </button>
        </form>
      )}
    </div>
  )
}
