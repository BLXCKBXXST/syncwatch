import { useId } from 'react'
import './TextField.css'

// Поле ввода дизайн-системы. Состояния из макета Figma: обычное, с подсказкой,
// заполненное, в фокусе, с ошибкой. Ошибка имеет приоритет над подсказкой.
export default function TextField({
  label,
  required = false,
  error = '',
  hint = '',
  id,
  ...rest
}) {
  const generatedId = useId()
  const fieldId = id || rest.name || generatedId

  return (
    <div className={`field${error ? ' field--error' : ''}`}>
      {label && (
        <label className="field__label" htmlFor={fieldId}>
          {label}
        </label>
      )}
      <div className="field__control">
        <input id={fieldId} className="field__input" {...rest} />
        {required && (
          <span className="field__required" aria-hidden="true">
            *
          </span>
        )}
      </div>
      {error ? (
        <p className="field__error">{error}</p>
      ) : (
        hint && <p className="field__hint">{hint}</p>
      )}
    </div>
  )
}
