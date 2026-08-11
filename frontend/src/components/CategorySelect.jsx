import { useEffect, useState } from 'react'
import api from '../api'

export default function CategorySelect({ value, onChange, incomeOnly = null }) {
  const [categories, setCategories] = useState([])

  useEffect(() => {
    api.get('/categories/').then((res) => {
      const list = incomeOnly === null ? res.data : res.data.filter((c) => c.is_income === incomeOnly)
      setCategories(list)
      if (!value && list.length) onChange(list[0].id)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incomeOnly])

  return (
    <select
      value={value}
      onChange={(e) => onChange(parseInt(e.target.value))}
      className="border border-line px-2 py-1 rounded bg-white"
    >
      {categories.map((c) => (
        <option key={c.id} value={c.id}>
          {c.name}
        </option>
      ))}
    </select>
  )
}
