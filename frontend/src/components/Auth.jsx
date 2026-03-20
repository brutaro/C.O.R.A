import { ClipboardList, LogIn } from 'lucide-react';
import './Auth.css';

export default function AuthComponent({ onSignIn, loading, error }) {
  return (
    <div className="auth-container">
      <div className="auth-header">
        <h1 style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '15px' }}>
          <ClipboardList size={48} />
          C.O.R.A.
        </h1>
        <p>Conflito de Interesses: Orientacao, Registro e Analise</p>
      </div>
      <div className="auth-form">
        <button
          type="button"
          className="google-signin-button"
          onClick={onSignIn}
          disabled={loading}
        >
          <LogIn size={18} />
          <span>{loading ? 'Entrando...' : 'Entrar com Google'}</span>
        </button>
        {error ? <p className="auth-error">{error}</p> : null}
      </div>
    </div>
  );
}
