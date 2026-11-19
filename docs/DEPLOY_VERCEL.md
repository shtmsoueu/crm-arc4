# Implantação na Vercel

Hospedagem escolhida no momento (D-007). **Um projeto Vercel** com a raiz do repositório, mais um banco PostgreSQL gerenciado.

```
navegador ──► crm-arc4 (Vercel)
               ├─ /assets, /, telas  → web/dist (Vite, estático)
               └─ /api/*, /health    → api/app.py (FastAPI, função Python) ──► PostgreSQL (Neon)
```

Tudo fica no mesmo domínio: sem CORS, e o cookie de sessão da Fase 1 funciona direto.

## 1. Projeto

| Configuração | Valor |
| --- | --- |
| Root Directory | em branco (raiz do repositório) |
| Framework Preset | Other: os comandos vêm do `vercel.json` |
| Build | `cd web && npm run build` → `web/dist` (no `vercel.json`) |
| API | `api/app.py`; dependências Python do `pyproject.toml`/`uv.lock` da raiz |
| Variáveis | `DATABASE_URL` (criada ao conectar o Neon) |

Não mude esses campos no painel: o `vercel.json` é a fonte da configuração e tem teste (`api/tests/test_entrada_vercel.py`).

## 2. Banco

1. No painel: **Storage → Create Database → Neon (Postgres)** e conecte ao projeto `crm-arc4`. A variável `DATABASE_URL` é criada sozinha.
2. Aplique as migrations **da sua máquina** (a API não migra sozinha, de propósito):

```bash
DATABASE_URL='<url do Neon, com sslmode=require>' make migrate
```

Reaplicar é seguro. Rode de novo sempre que um PR trouxer migration nova.

3. Conferência: `https://<seu-projeto>.vercel.app/api/health` deve responder `{"status":"ok","banco":"ok","migracao":"0001"}`. Sem banco configurado, responde 503 com `"banco":"indisponivel"`.

## Limites da Vercel que afetam o projeto

Consultados em 2026-11-19 (https://vercel.com/docs/functions/limitations e https://vercel.com/docs/limits). Confira antes de cada fase, porque mudam.

| Limite (plano Hobby) | Valor | Impacto |
| --- | --- | --- |
| Corpo da requisição/resposta | 4,5 MB | Upload dos ZIPs (até 78 MB) **não passa pela API**. Exportações grandes precisam de streaming |
| Duração da função | até 300 s (configurado em 60 s) | Importação de uma carga (1,8 mi parcelas) não cabe numa requisição |
| Memória | 2 GB | Idem |
| Logs de execução | 1 hora | Auditoria vai para o banco (`seguranca.evento`), nunca para log da plataforma |
| Repositório de organização GitHub | Não conecta no Hobby | O repositório precisa estar na sua conta pessoal, ou o time precisa do plano Pro |

**Consequência para a Fase 2:** o importador roda fora da Vercel (CLI `make import` numa máquina autorizada ou GitHub Actions) e grava direto no PostgreSQL. A API e a tela de Importação mostram o lote, a simulação e a aprovação, que são operações leves. Os ZIPs originais vão para um armazenamento de objetos, não para a função.

## Antes de colocar dados reais

- **Termos de uso:** confirme nos termos da Vercel (https://vercel.com/legal/terms e https://vercel.com/docs/limits/fair-use-guidelines) se o plano Hobby permite uso comercial. Não foi possível confirmar isso na leitura de 2026-11-19.
- **LGPD:** a carga tem CPF, nome, telefone e dados bancários. Hospedar isso exige aval de quem responde pela carteira (contrato com o banco, DPA com Vercel e Neon, região dos dados).
- Até lá, use o ambiente só com as fixtures sintéticas (`make fixtures`).
