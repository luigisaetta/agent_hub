# demo6 web

UI `Next.js` per `demos/demo6` (backend FastAPI SSE su `POST /chat`).

## Avvio

Dalla root del repository:

```bash
cd demos/demo6/web
npm install
npm run dev
```

La UI è disponibile su `http://localhost:3000`.

## Configurazione endpoint

Puoi impostare l'endpoint backend copiando il template versionato:

```bash
cp demos/demo6/web/.env.local.example demos/demo6/web/.env.local
```

Il file locale contiene questa variabile:

```bash
NEXT_PUBLIC_DEMO6_CHAT_URL=http://127.0.0.1:8080/chat
```

oppure modificarlo direttamente dalla sidebar della UI.
