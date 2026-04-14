# Streamlit Generalized Agent Client

Client Streamlit per testare endpoint agent OCI Enterprise AI con payload libero
(JSON o testo) e JWT opzionale.

## Avvio

Da root repository:

```bash
streamlit run agents/streamlit_client/app.py
```

## Sidebar

- toggle `Create JWT token`
- `client_id`
- `client_secret`
- `GenAI application id` (usato per derivare automaticamente la URL)
- `region`
- `Agent URL (derived, editable)`
- `Agent endpoint path` (default: `/actions/invoke/chat`)
- parametri JWT: `OCI domain URL`, `OCI scope`, `OCI token URL (optional)`, `Show important JWT claims`

## Uso

1. Compila la configurazione in sidebar.
2. Inserisci payload al centro (JSON oppure testo semplice).
3. Clicca `Invoke Agent`.
4. Vedi output finale e dettaglio eventi SSE.
