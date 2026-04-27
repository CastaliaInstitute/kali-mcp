# Docker pentest lab (Codespace / local)

This stack gives students an **isolated L2 segment** (`student_lab`, `172.30.0.0/24`) and a well-known **training** web app ([OWASP Juice Shop](https://owasp.org/www-project-juice-shop/)) at **`172.30.0.10`**.

**Scope:** Instructors are responsible for policy, age appropriateness, and laws. This lab is for **teaching in environments you own or control** (e.g. your GitHub org’s Codespace), not for attacking others.

## Prerequisites

- The devcontainer must include **Docker** (this repo’s `.devcontainer` uses Docker-in-Docker) **or** use Docker on a normal Kali/VM.
- In **GitHub Codespaces**, the first `docker compose up` can take several minutes (image pull) and may need a machine with **at least ~8 GiB** RAM in org settings.

## Start / stop

```bash
# From repository root
./scripts/lab-up.sh
./scripts/lab-down.sh
```

## How students reach targets from the Kali (Codespace) shell

- **Web UI (browser or curl):** `http://127.0.0.1:3000` (bound to loopback in compose). The container is also on **`172.30.0.10`** for exercises that reference the internal lab subnet (L3 to that IP may vary with Docker-in-Docker; use `docker exec` to verify from a throwaway `alpine` on `student_lab` if needed).
- **kali-mcp + LLM (HTTP on 8765):** Example prompts: use `nmap_scan` for `127.0.0.1` and ports you expect, or `http_head` with `http://127.0.0.1:3000/`. Never aim tools at systems outside your lab.
- If `172.30.0.10` is not pingable from the devcontainer but **localhost:3000** is, that is still valid for a web-focused exercise (Docker port publishing).

## Extend the lab

- Add more `services` under the same `student_lab` network (e.g. another image your institution approves).
- Keep a **separate** compose file or `profiles` if you offer “reduced” or “light” options.

## Stop and reset

```bash
./scripts/lab-down.sh
```

`lab-down` runs `docker compose down` (add `-v` in the script if you need to drop volumes for a full reset).
