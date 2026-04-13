# Deep Agents 01

Esempio `agents/` basato su Deep Agents (LangChain/LangGraph) con:
- backend agent separato
- API FastAPI SSE separata
- client CLI separato
- integrazione OCI OpenAI-compatible via `ChatOpenAI`

Questo esempio e pensato per esecuzione locale (senza JWT).

## Obiettivo

Fornire un secondo agente nel progetto `agent_hub` con struttura simile a `hello_world`, ma usando il framework Deep Agents.

## Architettura

Flusso alto livello:
1. Il client CLI invia `POST /chat` con `prompt`
2. L'API riceve la richiesta e apre stream SSE
3. Il backend invoca Deep Agents con `ChatOpenAI`
4. L'API inoltra eventi SSE al client
5. Il client stampa il testo finale oppure errore

## File principali

- `agents/deep_agents01/backend.py`
  - costruisce il deep agent (`create_deep_agent`)
  - configura `ChatOpenAI` su endpoint OCI
  - forza Responses API
  - converte output in eventi SSE-friendly (`response.started`, `response.output_text.delta`, `response.completed`, `response.error`)
- `agents/deep_agents01/api.py`
  - espone `GET /health`, `GET /ready`, `POST /chat`
  - serializza eventi in formato SSE
  - inizializza backend in modo lazy (al primo `POST /chat`)
- `agents/deep_agents01/client.py`
  - client CLI minimale
  - legge stream SSE
  - stampa output testuale
  - su errore backend stampa su `stderr` ed esce con code `1`
- `agents/deep_agents01/requirements.txt`
  - dipendenze specifiche di questo agente
- `agents/deep_agents01/.env.local`
  - secrets locali per API key e project id (non versionato)
- `agents/deep_agents01/deep_agents01.env.sample`
  - template da copiare per creare `.env.local`
- `tests/test_deep_agents01_api.py`
- `tests/test_deep_agents01_backend.py`
- `tests/test_deep_agents01_client.py`

## Configurazione OCI: dove viene presa

### File env locale consigliato

Questo agente carica automaticamente:
- `agents/deep_agents01/.env.local`

Workflow consigliato:

```bash
cp agents/deep_agents01/deep_agents01.env.sample agents/deep_agents01/.env.local
```

Poi valorizza nel file:
- `OPENAI_API_KEY`
- `OPENAI_PROJECT_ID`

### Endpoint e regione

L'endpoint e letto da:
- `config.py` -> `BASE_URL`

Costruzione endpoint:
- `https://inference.generativeai.{REGION}.oci.oraclecloud.com/20231130/openai/v1`

Regione:
- `AGENT_HUB_REGION` (env var), fallback a `us-chicago-1`

### API key

Ordine di risoluzione nel backend:
1. `OPENAI_API_KEY`
2. `OCI_GENAI_API_KEY`
3. errore esplicito se non impostata

### Project ID

Ordine di risoluzione nel backend:
1. `OPENAI_PROJECT_ID`
2. `OCI_PROJECT_ID`
3. errore esplicito se non impostato

Il project viene passato come header:
- `OpenAI-Project: <project_id>`

### Modello

Default:
- `openai.gpt-5.4`

Override runtime:
- `DEEP_AGENTS_MODEL`

Esempio:
```bash
export DEEP_AGENTS_MODEL=openai.gpt-5.2
```

## Punto importante: forcing Responses API

Nel tuo ambiente, con `deepagents` + `langchain-openai`, in auto-detect il model wrapper poteva usare `chat.completions`.

Con OCI e questo modello, quel percorso ha prodotto:
- `openai.NotFoundError: Not Found`

Per evitare regressioni, nel backend e impostato esplicitamente:
- `use_responses_api=True`
- `output_version="responses/v1"`

Questa scelta forza l'uso della Responses API invece di Chat Completions.

## Installazione

Dal root repo:

```bash
pip install -r agents/deep_agents01/requirements.txt
```

Se usi Conda (come nel progetto):

```bash
conda run -n agent_hub pip install -r agents/deep_agents01/requirements.txt
```

## Sicurezza secrets

- I secrets runtime vanno in `agents/deep_agents01/.env.local`
- `.env.local` e ignorato da git
- Il template versionato e `agents/deep_agents01/deep_agents01.env.sample`

## Avvio

### 1) Avvia API

```bash
uvicorn agents.deep_agents01.api:app --reload --port 8090
```

### 2) Lancia client

```bash
python -m agents.deep_agents01.client "Spiega in breve cos'e Deep Agents"
```

Con URL custom:

```bash
python -m agents.deep_agents01.client "Dammi 3 use case" --url http://127.0.0.1:8090/chat
```

## API contract

### Endpoint

- `GET /health`
- `GET /ready`
- `POST /chat` (SSE)

### Payload accettati

Forma primaria:

```json
{
  "prompt": "Spiega cos'e Deep Agents"
}
```

Compatibilita con payload stile demo:

```json
{
  "user_request": "Spiega cos'e Deep Agents"
}
```

### Eventi SSE principali

- `response.started`
- `graph.node.started`
- `response.output_text.delta`
- `response.error`
- `response.completed`

## Error handling

### Errori di runtime del modello

Se il backend riceve eccezioni dal provider/modello:
- non fa crash dello stream
- invia evento `response.error`
- chiude con `response.completed` contenente campo `error`

### Comportamento client

Il client ora:
- stampa `Backend error: ...` su `stderr` quando riceve `response.error`
- ritorna exit code `1` in caso di errore
- ritorna exit code `1` anche se non arriva output

Questo evita il caso "silenzioso" in cui non si vedeva nulla.

## Troubleshooting rapido

### `Not Found`

Possibili cause:
- modello non disponibile sulla route usata
- endpoint/region errati
- path API non coerente
- mancata forzatura Responses API (gia risolta in questo esempio)

Controlli consigliati:
1. verifica `AGENT_HUB_REGION`
2. verifica `BASE_URL` in `config.py`
3. verifica key (`OPENAI_API_KEY` o `OCI_GENAI_API_KEY`)
4. prova modello alternativo:
   ```bash
   export DEEP_AGENTS_MODEL=openai.gpt-5.2
   ```

### Client non stampa nulla

Con la versione corrente non dovrebbe succedere:
- se errore backend: stampa messaggio e exit `1`
- se stream senza testo: stampa `No output received from server.` e exit `1`

## Riferimento origine esempio

Adattato dal quickstart ufficiale Deep Agents:
- https://github.com/langchain-ai/deepagents

Con integrazione specifica per `agent_hub` (OCI endpoint, config locale, API/client separati).
