# Runbook: Install Langfuse on an Ubuntu VM (Docker Compose)

This runbook provides a production-minded, step-by-step installation of **Langfuse v3** on an Ubuntu VM using the official Docker Compose deployment.

It is based on the official Langfuse self-hosting documentation and the official `docker-compose.yml` from the Langfuse repository.

## 1) Scope and assumptions

- Target OS: Ubuntu 22.04+ (or Ubuntu 24.04) on a cloud VM.
- Access: SSH access with sudo privileges.
- Deployment type: single VM, Docker Compose (good for low-scale / non-HA usage).
- Recommended VM size from Langfuse docs: at least **4 vCPU, 16 GiB RAM**, and sufficient disk (example: 100 GiB).

## 2) Open required network ports

Allow inbound traffic at least for:

- `3000/tcp` (Langfuse Web UI/API)
- `9090/tcp` (MinIO S3 endpoint, used by default setup)

Optional hardening: keep all other service ports private (the official compose file already binds most internal services to `127.0.0.1`).

If you use `ufw` on Ubuntu:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 9090/tcp
sudo ufw enable
sudo ufw status
```

## 3) Install Docker Engine + Docker Compose plugin

Run exactly (official Docker apt-repo flow, also referenced by Langfuse docs):

```bash
# Add Docker's official GPG key and repo
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Verify:

```bash
sudo docker run hello-world
docker compose version
```

Optional (run Docker without `sudo`, then reconnect SSH):

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 4) Clone Langfuse

```bash
git clone https://github.com/langfuse/langfuse.git
cd langfuse
```

## 5) Configure secrets (mandatory)

Langfuse marks sensitive values in `docker-compose.yml` with `# CHANGEME`.

Create secure values first:

```bash
openssl rand -hex 32   # use for NEXTAUTH_SECRET
openssl rand -hex 32   # use for SALT
openssl rand -hex 32   # use for ENCRYPTION_KEY (must be 64 hex chars)
openssl rand -base64 24
openssl rand -base64 24
openssl rand -base64 24
openssl rand -base64 24
openssl rand -base64 24
openssl rand -base64 24
openssl rand -base64 24
```

Update the `# CHANGEME` values in `docker-compose.yml` with strong random secrets, at minimum for:

- `NEXTAUTH_SECRET`
- `SALT`
- `ENCRYPTION_KEY`
- `POSTGRES_PASSWORD`
- `CLICKHOUSE_PASSWORD`
- `REDIS_AUTH`
- `MINIO_ROOT_PASSWORD`
- `LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY`
- `LANGFUSE_S3_MEDIA_UPLOAD_SECRET_ACCESS_KEY`
- `LANGFUSE_S3_BATCH_EXPORT_SECRET_ACCESS_KEY`

Edit file:

```bash
nano docker-compose.yml
```

## 6) Confirm timezone requirement (UTC)

Langfuse requires infrastructure components (especially Postgres/ClickHouse) in UTC.

Check VM timezone:

```bash
timedatectl
```

If needed, set UTC:

```bash
sudo timedatectl set-timezone UTC
```

## 7) Start Langfuse

Foreground mode (best for first startup):

```bash
docker compose up
```

Detached mode:

```bash
docker compose up -d
```

Wait ~2-3 minutes and verify `langfuse-web` is healthy/ready.

Useful checks:

```bash
docker compose ps
docker compose logs -f langfuse-web
docker compose logs -f langfuse-worker
```

## 8) Access the UI

Open in browser:

```text
http://<VM_PUBLIC_IP>:3000
```

If direct access is blocked, create an SSH tunnel from your local machine:

```bash
ssh -L 3000:localhost:3000 <user>@<VM_PUBLIC_IP>
```

Then browse locally:

```text
http://localhost:3000
```

## 9) Lifecycle commands

Stop:

```bash
docker compose down
```

Stop and remove volumes (destructive):

```bash
docker compose down -v
```

Upgrade to latest images:

```bash
docker compose up --pull always -d
```

## 10) Post-install validation checklist

- `docker compose ps` shows all services `Up`.
- UI reachable on port `3000`.
- You can log in/create initial workspace.
- No startup errors in `langfuse-web` and `langfuse-worker` logs.
- VM disk has enough free space for trace growth.

## 11) Notes for production

- Docker Compose setup is intended for local/VM or low-scale scenarios.
- For high availability/scaling/backup-focused production, use Kubernetes or Terraform-based cloud deployment options from Langfuse docs.
- Put Langfuse behind HTTPS reverse proxy/load balancer for internet-facing use.

## Official references

- Langfuse Self-Hosting overview: https://langfuse.com/docs/deployment/self-host
- Langfuse Docker Compose deployment (Local/VM): https://langfuse.com/self-hosting/deployment/docker-compose
- Official Langfuse docker-compose file: https://github.com/langfuse/langfuse/blob/main/docker-compose.yml
- Docker Engine install (Ubuntu): https://docs.docker.com/engine/install/ubuntu/
