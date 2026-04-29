# Design per deploy automatizzato di componenti AI su OCI Enterprise AI

Autore: L. Saetta
Versione: 1.1
Data ultima modifica: 29-04-2026

Nota: in questa specifica i punti ancora da definire sono marcati come: `TBD`.

## 1. Obiettivo

L'obiettivo è costruire un meccanismo automatizzato per fare il deploy di componenti AI containerizzati su OCI Enterprise AI, per esempio:

• Agent
• MCP Server
• API service

Il deploy deve essere eseguibile da script, partendo da una immagine Docker locale del componente da distribuire e arrivando alla creazione delle risorse OCI necessarie.

Il percorso completo prevede:

• pubblicazione della immagine Docker su OCIR
• creazione o aggiornamento della Hosted Application
• creazione della Hosted Deployment
• configurazione di sicurezza, variabili ambiente, parametri runtime e riferimenti alla container image

## 2. Concetto di base

La OCI CLI consente di interagire con le risorse Generative AI, incluse Hosted Applications e Hosted Deployments, se la versione della CLI è sufficientemente recente.

Il deploy di un componente richiede due passaggi principali:

• creazione e configurazione della Hosted Application
• creazione e configurazione della Hosted Deployment

Poiché questi passaggi richiedono molti parametri, non conviene passare tutto a mano da linea di comando. La soluzione più pulita è introdurre un file dichiarativo di configurazione, letto da uno script.

Il file descrive cosa deployare e come configurarlo. Lo script si occupa di tradurre questa configurazione nei comandi OCI CLI corretti.

Il pattern raccomandato è:

```text
YAML -> Python -> JSON generati -> OCI CLI -> OCI Enterprise AI
```

In sintesi:

• YAML come sorgente umana
• JSON come formato tecnico generato
• OCI CLI come motore operativo
• Python come orchestratore del processo

## 3. Risorse OCI coinvolte

Il design ruota principalmente intorno a due risorse OCI Enterprise AI:

• Hosted Application
• Hosted Deployment

La distinzione tra le due risorse è importante perché alcune configurazioni appartengono logicamente alla applicazione, mentre altre appartengono al singolo deployment.

La tabella seguente chiarisce il mapping previsto. I punti marcati come `TBD` devono essere verificati contro il modello effettivo richiesto dalla OCI CLI e dalle API disponibili.

| Configurazione | Hosted Application | Hosted Deployment | Note |
|---|---:|---:|---|
| Nome logico applicazione | Sì | No | Identifica la applicazione AI gestita |
| Display name applicazione | Sì | No | Nome leggibile della Hosted Application |
| Compartment | Sì | Sì | Da verificare se entrambi i comandi richiedono esplicitamente il compartment |
| Container image URI | No | Sì | Il deployment deve puntare alla immagine Docker pubblicata su OCIR |
| Container tag | No | Sì | Deve essere immutabile, per esempio git sha, timestamp o build id |
| Artifact Docker | No | Sì | In particolare per la modalità single docker artifact |
| OAuth2 | Probabilmente sì | TBD | Da verificare in base al modello OCI CLI effettivo |
| Variabili ambiente | TBD | TBD | Da verificare dove OCI richiede di configurarle |
| Secrets | TBD | TBD | Da verificare se sono supportati direttamente o referenziati tramite ambiente e Vault |
| Scaling | TBD | TBD | Da verificare se appartiene alla applicazione o al deployment |
| Networking | Probabilmente sì | TBD | Da verificare in base al modello di esposizione del servizio |
| Endpoint | TBD | TBD | Può essere prodotto dalla Hosted Application, dal Deployment o da entrambi, a seconda del modello OCI |
| Stato di attivazione | No | Sì | Il deployment può essere creato e poi attivato |
| Work request e diagnostica | Sì | Sì | Entrambe le operazioni possono generare informazioni diagnostiche |

Questa tabella non sostituisce la documentazione OCI CLI. Serve come guida di design per decidere dove collocare i campi nel file YAML e quali parti validare nello script.

## 4. Architettura proposta

Il design proposto separa tre livelli.

### 4.1 File di configurazione

Un file YAML contiene tutti gli input necessari al deploy.

Esempio:

```text
oci_ai_deploy.yaml
```

Il file è leggibile, versionabile e può essere usato sia localmente sia in CI/CD.

### 4.2 Script di orchestrazione

Uno script Python legge il file YAML, valida i campi, genera eventuali JSON intermedi e chiama la OCI CLI.

Esempio:

```text
oci_ai_deploy.py
```

Il Python può chiamare la OCI CLI tramite `subprocess`, mantenendo il comportamento molto vicino ai comandi manuali già validati.

### 4.3 OCI CLI e Docker

La OCI CLI esegue tutte le operazioni su OCI:

• creazione Hosted Application
• creazione Hosted Deployment
• attesa dello stato finale
• recupero di OCID, endpoint, work request e diagnostica

Docker è invece usato per:

• build della immagine locale
• tag della immagine per OCIR
• push della immagine su OCIR

## 5. Flusso end to end

Il flusso completo dovrebbe essere ordinato così.

### 5.1 Validazione iniziale

Lo script controlla che siano disponibili:

• Docker
• OCI CLI
• versione OCI CLI compatibile
• configurazione OCI funzionante
• login OCIR valido o comunque possibile
• file YAML valido
• compartment id presente
• region e region key coerenti
• nome applicazione presente
• parametri di sicurezza presenti se richiesti
• prerequisiti IAM soddisfatti dagli admin OCI

### 5.2 Dry run

Prima di eseguire operazioni che modificano risorse o pubblicano immagini, il tool deve supportare una modalità `dry-run`.

La modalità `dry-run` deve essere attivabile tramite un parametro specifico da command line:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy --dry-run
```

In modalità `dry-run`, lo script non deve creare, aggiornare o cancellare risorse OCI e non deve fare push su OCIR.

La modalità `dry-run` dovrebbe mostrare:

• configurazione YAML risolta
• image URI calcolata
• tag immagine calcolato
• Hosted Application prevista
• Hosted Deployment previsto
• JSON che verrebbero passati alla OCI CLI
• comandi OCI CLI equivalenti che verrebbero eseguiti
• eventuali risorse già esistenti, se la verifica è sicura e in sola lettura
• eventuali errori di validazione

La modalità `dry-run` è particolarmente importante per CI/CD, code review e troubleshooting, perché consente di verificare il deploy prima di modificare risorse OCI.

### 5.3 Build della immagine Docker

Lo script esegue la build della immagine Docker usando le informazioni del file YAML.

Esempio logico:

```bash
docker build -f Dockerfile -t my-agent:abc1234 .
```

### 5.4 Tag della immagine per OCIR

Lo script costruisce il nome completo della immagine OCIR.

Esempio:

```text
fra.ocir.io/<namespace>/<repository>/<image-name>:<tag>
```

Il tag dovrebbe essere univoco, per esempio:

• git sha
• timestamp
• numero versione applicativo
• build id CI/CD

È preferibile evitare `latest` per i deploy reali.

### 5.5 Push su OCIR

Lo script esegue il push della immagine.

Esempio:

```bash
docker push fra.ocir.io/<namespace>/<repository>/<image-name>:<tag>
```

### 5.6 Creazione o riuso della Hosted Application

Lo script verifica se una Hosted Application con quel nome esiste già.

Se esiste:

• recupera l'OCID
• eventualmente aggiorna la configurazione, se previsto dal design

Se non esiste:

• crea una nuova Hosted Application
• applica configurazioni di runtime, sicurezza, networking e variabili di ambiente, in base al modello effettivo della OCI CLI

### 5.7 Creazione della Hosted Deployment

Lo script crea una nuova Hosted Deployment associata alla Hosted Application.

La Hosted Deployment punta alla immagine Docker pubblicata su OCIR.

Dati principali:

• hosted application id
• compartment id
• display name del deployment
• container URI
• container tag
• configurazione artifact
• eventuale flag di attivazione
• eventuale configurazione di scaling, se prevista a questo livello

### 5.8 Attesa e diagnostica

Lo script aspetta lo stato finale.

Se il deploy riesce:

• stampa Hosted Application OCID
• stampa Hosted Deployment OCID
• stampa image URI
• stampa eventuale endpoint

Se il deploy fallisce:

• stampa errore OCI CLI
• stampa work request, se disponibile
• stampa suggerimenti diagnostici

## 6. File YAML di configurazione

Il formato consigliato per il file principale è YAML.

Motivi:

• è più leggibile di JSON
• supporta bene configurazioni annidate
• permette commenti
• è comodo per molte variabili ambiente
• è comodo per gestire più ambienti, per esempio dev, test e prod
• può essere convertito facilmente in JSON dallo script

Esempio di file `oci_ai_deploy.yaml`:

```yaml
application:
  name: my-agent-app
  compartment_id: ocid1.compartment.oc1..example
  region: eu-frankfurt-1
  region_key: fra

container:
  context: .
  dockerfile: Dockerfile
  image_name: my-agent
  repository: ai-agents
  tag_strategy: git_sha
  ocir_namespace: auto

hosted_application:
  display_name: my-agent-app
  description: Agent application deployed through OCI Enterprise AI
  create_if_missing: true
  update_if_exists: false

  scaling:
    min_instances: 1
    max_instances: 2
    metric: cpu

  networking:
    mode: public

  security:
    auth_type: oauth2
    issuer_url: https://issuer.example.com
    audience: my-agent-api
    jwks_url: https://issuer.example.com/.well-known/jwks.json

  environment:
    variables:
      LOG_LEVEL: INFO
      OCI_REGION: eu-frankfurt-1
      AGENT_MODE: production
      MCP_SERVER_PORT: "8080"

    secrets:
      API_KEY:
        source: vault
        secret_ocid: ocid1.vaultsecret.oc1..example

hosted_deployment:
  display_name: my-agent-deployment
  create_new_version: true
  activate: true
  wait_for_state: SUCCEEDED
```

## 7. Mapping YAML verso OCI CLI JSON

La OCI CLI lavora bene con JSON, quindi il file YAML non dovrebbe essere passato direttamente ai comandi OCI.

Il pattern consigliato è:

```text
deploy.yaml
  -> script Python
  -> JSON generati per OCI CLI
  -> oci generative-ai hosted-application create/update
  -> oci generative-ai hosted-deployment create/update
```

Per configurazioni complesse, conviene usare JSON generati e `--from-json`.

Esempio:

```bash
oci generative-ai hosted-application create \
  --from-json file://generated/create-hosted-application.json
```

Il mapping esatto tra YAML e JSON deve essere implementato nello script Python e validato contro i comandi OCI CLI reali.

File generati tipici:

```text
generated/create-hosted-application.json
generated/create-hosted-deployment.json
```

Il contenuto della directory `generated` non dovrebbe essere modificato a mano. Può essere rigenerato dallo script a partire dal YAML.

## 8. Comandi del tool

Per uso locale:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml validate
python oci_ai_deploy.py --config oci_ai_deploy.yaml build
python oci_ai_deploy.py --config oci_ai_deploy.yaml push
python oci_ai_deploy.py --config oci_ai_deploy.yaml create-application
python oci_ai_deploy.py --config oci_ai_deploy.yaml create-deployment
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy --dry-run
```

Per CI/CD:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy --non-interactive
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy --non-interactive --dry-run
```

Eventuale modalità menu per uso manuale:

```text
1. Validate configuration
2. Dry run
3. Build Docker image
4. Push image to OCIR
5. Create or update Hosted Application
6. Create Hosted Deployment
7. Full deploy
8. Show current deployments
9. Rollback
```

Per automazione e pipeline è preferibile usare comandi non interattivi.

## 9. Idempotenza e update policy

Il tool dovrebbe essere rilanciabile senza creare risorse duplicate inutili.

Comportamento consigliato:

• se la Hosted Application esiste, riusarla
• se non esiste e `create_if_missing` è true, crearla
• ogni deploy crea una nuova Hosted Deployment con tag immagine univoco
• non usare `latest` come tag principale
• salvare e stampare sempre image URI, application id e deployment id

Esempio di naming:

```text
my-agent-app
my-agent-app-abc1234
my-agent-app-20260428153000
```

La strategia di update deve essere esplicita, perché alcune modifiche sono sicure mentre altre possono avere impatti importanti.

Esempi di comportamento da definire:

• se cambia solo la image, creare una nuova Hosted Deployment
• se cambiano le variabili ambiente, verificare se aggiornare la Hosted Application o creare una nuova Hosted Deployment, `TBD`
• se cambia OAuth2, richiedere una scelta esplicita o una modalità forzata
• se cambia networking, richiedere una scelta esplicita o una modalità forzata
• se cambia compartment, non aggiornare automaticamente

Esempio possibile di configurazione futura:

```yaml
update_policy:
  application:
    allow_update: true
    require_confirmation_for_security_changes: true
  deployment:
    always_create_new: true
    activate_new_deployment: true
```

## 10. Secrets e OAuth2

### 10.1 Variabili ambiente

Le variabili ambiente non devono essere passate una a una da linea di comando.

Devono stare nel file YAML in forma dichiarativa.

Esempio:

```yaml
environment:
  variables:
    LOG_LEVEL: INFO
    MCP_SERVER_PORT: "8080"
    AGENT_MODE: production
```

Lo script trasforma questa sezione nel formato richiesto dalla OCI CLI per la Hosted Application o per il deployment, in base al modello esatto previsto dal comando.

### 10.2 Secrets

I secrets non dovrebbero essere scritti in chiaro nel file YAML.

Da evitare:

```yaml
API_KEY: my-secret-value
```

Meglio usare riferimenti esterni.

Esempio con OCI Vault:

```yaml
secrets:
  API_KEY:
    source: vault
    secret_ocid: ocid1.vaultsecret.oc1..example
```

Oppure, per sviluppo locale:

```yaml
secrets:
  API_KEY:
    source: local_env
    env_name: MY_API_KEY
```

Per sviluppo locale è accettabile leggere secrets da variabili ambiente o da un file `.env` escluso dal versionamento. Per ambienti condivisi o CI/CD è preferibile usare OCI Vault o secret manager della pipeline.

In questo modo il file può essere versionato senza esporre credenziali.

Controlli consigliati:

• verificare che `.env` sia escluso dal versionamento
• non stampare mai secrets nei log
• mascherare valori sensibili negli output
• fallire se vengono rilevati secrets hardcoded nel YAML

### 10.3 OAuth2

La configurazione OAuth2 è uno degli elementi più delicati del deploy.

Nel file YAML dovrebbe essere dichiarata in una sezione dedicata.

Esempio:

```yaml
security:
  auth_type: oauth2
  issuer_url: https://issuer.example.com
  audience: my-agent-api
  jwks_url: https://issuer.example.com/.well-known/jwks.json
```

Lo script deve validare che i campi obbligatori siano presenti quando `auth_type` è `oauth2`.

Campi tipici da validare:

• issuer URL
• audience
• JWKS URL
• eventuale client id
• eventuali scope
• eventuali policy OCI correlate

## 11. IAM e accesso OCIR

Le policy IAM funzionanti sono un prerequisito del deploy.

Questo prerequisito deve essere soddisfatto dagli admin OCI prima di usare il tool in ambienti reali.

Il tool può verificare alcuni sintomi, per esempio errori di autorizzazione o impossibilità di accedere a OCIR, ma non dovrebbe assumersi la responsabilità di creare o modificare policy IAM.

Servono policy adeguate per:

• push su OCIR
• lettura della immagine da parte del servizio che esegue il deployment
• gestione Hosted Applications
• gestione Hosted Deployments
• eventuale accesso a Vault
• eventuale accesso a Logging
• eventuale accesso a Networking
• eventuale accesso a Object Storage, se richiesto dal componente

È importante distinguere tra:

• permessi dell'identità che esegue il deploy
• permessi del servizio o runtime che deve leggere la immagine ed eseguire il componente

Uno scenario possibile è che il push Docker riesca, ma il deployment fallisca perché il servizio non riesce a leggere la immagine da OCIR. Questa parte deve essere verificata con attenzione dagli admin OCI.

## 12. Rollback

Il rollback dovrebbe basarsi su versioni immutabili della immagine Docker.

Approccio consigliato:

• ogni build produce un tag univoco
• ogni Hosted Deployment punta a un tag preciso
• il tool può listare deployment precedenti
• il rollback seleziona un deployment precedente oppure crea un nuovo deployment che punta a una immagine precedente

Esempio:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml rollback --to-tag abc1234
```

Il rollback non dovrebbe dipendere da `latest`.

## 13. Validazione, render e dry run

La fase `validate` dovrebbe controllare almeno:

• `oci` presente nel PATH
• versione OCI CLI adeguata
• `docker` presente nel PATH
• autenticazione OCI funzionante
• namespace OCIR recuperabile
• compartment id valido sintatticamente
• region valorizzata
• region key valorizzata
• Dockerfile presente
• file YAML valido
• security config coerente
• secrets non hardcoded
• tag immagine calcolabile
• prerequisiti IAM dichiarati come soddisfatti per l'ambiente target

Oltre a `validate`, può essere utile aggiungere un comando `render`:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml render
```

Il comando `render` genera i JSON intermedi senza chiamare OCI e senza fare build o push.

La modalità `dry-run` invece simula l'intero deploy senza modificare risorse:

```bash
python oci_ai_deploy.py --config oci_ai_deploy.yaml deploy --dry-run
```

Differenza tra i comandi:

| Comando | Scopo | Modifica risorse? |
|---|---|---:|
| `validate` | Controlla configurazione e prerequisiti | No |
| `render` | Genera JSON intermedi | No |
| `deploy --dry-run` | Simula il deploy completo e mostra cosa verrebbe fatto | No |
| `deploy` | Esegue il deploy reale | Sì |

## 14. Diagnostica e report finale

Lo script dovrebbe produrre output leggibile sia per uso umano sia per CI/CD.

In caso di successo, dovrebbe stampare:

• Hosted Application OCID
• Hosted Deployment OCID
• image URI
• endpoint, se disponibile
• work request id, se disponibile
• stato finale

In caso di errore, dovrebbe stampare:

• comando fallito
• errore OCI CLI
• eventuale work request id
• suggerimenti diagnostici

È utile produrre anche un file di report finale, per esempio:

```text
generated/deploy-report.json
```

Contenuto suggerito:

```json
{
  "timestamp": "2026-04-29T00:00:00Z",
  "config_file": "oci_ai_deploy.yaml",
  "git_sha": "abc1234",
  "image_uri": "fra.ocir.io/example/ai-agents/my-agent:abc1234",
  "hosted_application_id": "ocid1.example...",
  "hosted_deployment_id": "ocid1.example...",
  "endpoint": "https://example.endpoint",
  "oci_cli_version": "TBD",
  "work_request_id": "TBD",
  "final_state": "SUCCEEDED"
}
```

Questo report è utile per audit, rollback e troubleshooting.

## 15. Principali difficoltà previste

### 15.1 Versione della OCI CLI

Se il comando seguente fallisce:

```bash
oci generative-ai hosted-application --help
```

allora la CLI non contiene ancora i sottocomandi necessari oppure il PATH punta a una installazione vecchia.

### 15.2 Permessi IAM

Le policy IAM sono un prerequisito che deve essere soddisfatto dagli admin OCI.

Il tool deve fallire in modo leggibile se i permessi non sono sufficienti, ma non deve nascondere il problema o tentare workaround non controllati.

### 15.3 Accesso alla immagine OCIR

Il push Docker può riuscire, ma il deployment può fallire se il servizio non riesce a leggere la immagine.

Questa parte va verificata con attenzione nelle policy OCI.

### 15.4 Configurazione OAuth2

OAuth2 richiede coerenza tra issuer, audience, JWKS e policy di accesso.

Questa configurazione va validata prima del deploy.

### 15.5 Readiness del container

Il container deve essere pronto per un runtime gestito.

Checklist:

• ascolta sulla porta corretta
• non dipende da file locali
• legge configurazione da environment variables
• scrive log su stdout e stderr
• gestisce shutdown pulito
• ha startup time ragionevole
• espone eventuale health endpoint, se richiesto

### 15.6 Comando OCI CLI specifico per il deployment

I comandi principali ipotizzati sono:

```bash
oci generative-ai hosted-application list
oci generative-ai hosted-application create
oci generative-ai hosted-application get
oci generative-ai hosted-application update

oci generative-ai hosted-deployment list
oci generative-ai hosted-deployment create
oci generative-ai hosted-deployment create-hosted-deployment-single-docker-artifact
oci generative-ai hosted-deployment get
oci generative-ai hosted-deployment update
```

`TBD`: verificare quale comando è quello corretto per la modalità single docker artifact nella versione OCI CLI target.

Questo è uno dei punti più importanti da validare durante la prima implementazione, perché il nome esatto del comando e il JSON richiesto dalla CLI possono essere specifici della versione installata.

## 16. Struttura del progetto

Struttura consigliata:

```text
oci-ai-deployer/
  oci_ai_deploy.py
  oci_ai_deploy.yaml
  schemas/
    oci_ai_deploy.schema.json
  generated/
    create-hosted-application.json
    create-hosted-deployment.json
    deploy-report.json
  examples/
    agent-dev.yaml
    agent-prod.yaml
    mcp-server-dev.yaml
  README.md
```

Significato:

• `oci_ai_deploy.py` contiene la logica operativa
• `oci_ai_deploy.yaml` contiene la configurazione del deploy
• `schemas` contiene lo schema di validazione
• `generated` contiene file temporanei generati dallo script
• `examples` contiene esempi riusabili per diversi componenti
• `README.md` documenta installazione, prerequisiti e uso del tool

## 17. Ruolo dello script Python

Lo script Python ha il compito di orchestrare il deploy.

Responsabilità principali:

• leggere YAML
• validare configurazione
• calcolare tag immagine
• recuperare namespace OCIR
• costruire image URI
• chiamare Docker per build, tag e push
• generare JSON intermedi per OCI CLI
• supportare modalità `dry-run`
• chiamare OCI CLI
• gestire errori
• stampare output finale leggibile
• produrre report finale

Nella prima versione il Python può chiamare la OCI CLI.

Esempio concettuale:

```python
import subprocess

subprocess.run([
    "oci",
    "generative-ai",
    "hosted-application",
    "create",
    "--from-json",
    "file://generated/create-hosted-application.json",
    "--wait-for-state",
    "SUCCEEDED"
], check=True)
```

Questo approccio è pratico perché consente di riusare gli stessi comandi già testati manualmente.

## 18. Roadmap

### Versione 1

Python più YAML più OCI CLI.

Obiettivo:

• automatizzare il flusso end to end
• mantenere la logica semplice
• usare comandi CLI già testabili manualmente
• supportare validazione
• supportare generazione JSON intermedi
• supportare modalità `dry-run`
• supportare modalità non interattiva per CI/CD

### Versione 2

Aggiungere:

• schema JSON di validazione completo
• gestione multi ambiente più evoluta
• rollback
• log strutturati
• diagnostica work request avanzata
• report finale completo
• eventuale integrazione più stretta con Vault o secret manager di pipeline

## 19. Decisione di design raccomandata

La soluzione raccomandata è:

• YAML come formato dichiarativo principale
• Python come orchestratore
• OCI CLI come motore operativo nella prima versione
• JSON generati come input tecnico per OCI CLI
• tag immagine immutabili
• secrets referenziati, non hardcoded
• validazione obbligatoria prima del deploy
• modalità `dry-run` tramite parametro command line dedicato
• supporto a modalità non interattiva per CI/CD
• policy IAM funzionanti come prerequisito gestito dagli admin OCI

## 20. Conclusione

Il design è fattibile e appropriato.

Automatizzare Hosted Application e Hosted Deployment tramite un file di configurazione è il modo più ordinato per gestire componenti AI come agent e MCP server.

Il vantaggio principale è che il deploy diventa:

• ripetibile
• versionabile
• controllabile
• adatto a CI/CD
• meno soggetto a errori manuali

La prima implementazione dovrebbe partire semplice:

```text
YAML -> Python -> JSON generati -> OCI CLI -> OCI Enterprise AI
```

La modalità `dry-run` rende il processo più sicuro, perché consente di vedere in anticipo cosa verrebbe eseguito prima di creare risorse, aggiornare configurazioni o pubblicare immagini.
