import './ParticipantsPanel.css'

// Список онлайн-зрителей комнаты с возможностью передать роль ведущего.
// Видна вкладка всем; кнопка «Сделать ведущим» — только текущему хосту.
export default function ParticipantsPanel({ socket, viewers, isHost }) {
  if (!viewers || viewers.length === 0) {
    return <p className="page-state">Пока никого нет в комнате.</p>
  }

  const promote = (participantId) => {
    socket?.send('room.transfer_host', { participant_id: participantId })
  }

  return (
    <ul className="participants">
      {viewers.map((v) => (
        <li key={v.id} className="participants__row">
          <span className="participants__name">
            {v.display_name}
            {v.is_guest && <span className="participants__tag">гость</span>}
          </span>
          {v.is_host ? (
            <span className="participants__badge">Ведущий</span>
          ) : (
            isHost && !v.is_guest && (
              <button
                type="button"
                className="participants__promote"
                onClick={() => promote(v.id)}
                title="Передать роль ведущего"
              >
                Сделать ведущим
              </button>
            )
          )}
        </li>
      ))}
    </ul>
  )
}
