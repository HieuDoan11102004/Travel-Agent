interface ConstraintStatusProps {
  satisfied: boolean
  violations: string[]
}

export default function ConstraintStatus({ satisfied, violations }: ConstraintStatusProps) {
  return (
    <div className={`constraint-status ${satisfied ? 'satisfied' : 'violated'}`}>
      <div className="constraint-header">
        {satisfied ? (
          <>
            <span className="status-icon">✅</span>
            <span className="status-text">All constraints satisfied</span>
          </>
        ) : (
          <>
            <span className="status-icon">⚠️</span>
            <span className="status-text">{violations.length} constraint(s) violated</span>
          </>
        )}
      </div>

      {!satisfied && violations.length > 0 && (
        <ul className="violation-list">
          {violations.map((v, i) => (
            <li key={i}>{v}</li>
          ))}
        </ul>
      )}

      <style>{`
        .constraint-status {
          padding: 0.75rem 1rem;
          border-radius: var(--border-radius);
          margin-bottom: 1rem;
        }
        .constraint-status.satisfied {
          background-color: #dcfce7;
          border: 1px solid #86efac;
        }
        .constraint-status.violated {
          background-color: #fef2f2;
          border: 1px solid #fca5a5;
        }
        .constraint-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .status-icon {
          font-size: 1.25rem;
        }
        .status-text {
          font-weight: 500;
        }
        .violation-list {
          margin: 0.5rem 0 0 1.5rem;
          font-size: 0.875rem;
        }
        .violation-list li {
          margin-bottom: 0.25rem;
        }
      `}</style>
    </div>
  )
}
