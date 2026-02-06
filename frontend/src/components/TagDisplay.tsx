import React, { useState } from 'react'

interface TagDisplayProps {
  value: string | string[] | undefined | null
  emptyLabel?: string
  className?: string
}

export const TagDisplay: React.FC<TagDisplayProps> = ({
  value,
  emptyLabel = '-',
  className = ''
}) => {
  const [expanded, setExpanded] = useState(false)

  const isNone = !value || value === 'None'
  const isArray = Array.isArray(value)

  if (isNone) {
    return <span className={`text-gray-400 ${className}`}>{emptyLabel}</span>
  }

  if (isArray) {
    if (value.length === 0) {
      return <span className={`text-gray-400 ${className}`}>{emptyLabel}</span>
    }

    if (value.length === 1 || expanded) {
      return (
        <span className={`text-sm ${className}`}>
          {value.join(' · ')}
        </span>
      )
    }

    const mainTag = value[0]
    const remaining = value.length - 1

    return (
      <button
        onClick={() => setExpanded(true)}
        className="text-sm text-blue-600 hover:text-blue-800 cursor-pointer transition-colors"
      >
        {mainTag} <span className="bg-blue-100 text-blue-800 text-xs px-1.5 py-0.5 rounded ml-1">+{remaining}</span>
      </button>
    )
  }

  return <span className={`text-sm ${className}`}>{value}</span>
}
