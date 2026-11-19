# Implantação na Vercel

Hospedagem escolhida no momento (D-007). São **dois projetos Vercel** apontando para o mesmo repositório, mais um banco PostgreSQL gerenciado.

```
navegador ──► arc4-web (Vite, estático) ──/api/*──► arc4-api (FastAPI, função Python) ──► PostgreSQL (Neon)
```

O navegador só conversa com o domínio do `arc4-web`. O frontend repassa `/api/*` para a API (rewrite), então não há CORS e o cookie de sessão da Fase 1 fica no mesmo domínio.

## 1. Banco

1. No painel da Vercel: **Storage → Create Database → Neon (Postgres)**, região mais próxima (ex.: São Paulo, se houver; senão `us-east`).
2. Conecte o banco ao projeto `arc4-api` (passo 3). A variável `DATABASE_URL` é criada sozinha.
3. Aplique as migrations **da sua máquina** (a API não migra sozinha, de propósito):

```bash
DATABASE_URL='<url do Neon, com sslmode=require>' make migrate
```

Reaplicar é seguro. Rode de novo sempre que um PR trouxer migration nova.

## 2. Projeto `arc4-web`

| Configuração | Valor |
| --- | --- |
| Root Directory | `web` |
| Framework Preset | Vite (lido do `web/vercel.json`) |
| Build / Output | `npm run build` → `dist` (lido do `web/vercel.json`) |

Depois de criar o `arc4-api`, troque `TROQUE-PELO-DOMINIO-DA-API` em `web/vercel.json` pelo domínio de produção da API (ex.: `arc4-api.vercel.app`), faça commit e push.

## 3. Projeto `arc4-api`

| Configuração | Valor |
| --- | --- |
| Root Directory | `api` |
| Framework Preset | FastAPI (detectado por `api/app.py`) |
| Python | 3.12 (padrão da Vercel) |
| Dependências | `api/requirements.txt` (mantenha igual a `api/pyproject.toml`; há teste que confere) |
| Variáveis | `DATABASE_URL` (criada ao conectar o Neon) |

Conferência: `https://<arc4-api>.vercel.app/api/health` deve responder `{"status":"ok","banco":"ok","migracao":"0001"}` e, pelo frontend, `https://<arc4-web>.vercel.app/api/health` deve responder o mesmo.

## Limites da Vercel que afetam o projeto

Consultados em 2026-11-19 (https://vercel.com/docs/functions/limitations e https://vercel.com/docs/limits). Confira antes de cada fase, porque mudam.

| Limite (plano Hobby) | Valor | Impacto |
| --- | --- | --- |
| Corpo da requisição/resposta | 4,5 MB | Upload dos ZIPs (até 78 MB) **não passa pela API**. Exportações grandes precisam de streaming |
| Duração da função | 300 s | Importação de uma carga (1,8 mi parcelas) não cabe numa requisição |
| Memória | 2 GB | Idem |
| Logs de execução | 1 hora | Auditoria vai para o banco (`seguranca.evento`), nunca para log da plataforma |
| Repositório de organização GitHub | Não conecta no Hobby | O repositório precisa estar na sua conta pessoal, ou o time precisa do plano Pro |

**Consequência para a Fase 2:** o importador roda fora da Vercel (CLI `make import` numa máquina autorizada ou GitHub Actions) e grava direto no PostgreSQL. A API e a tela de Importação mostram o lote, a simulação e a aprovação, que são operações leves. Os ZIPs originais vão para um armazenamento de objetos, não para a função.

## Antes de colocar dados reais

- **Termos de uso:** confirme nos termos da Vercel (https://vercel.com/legal/terms e https://vercel.com/docs/limits/fair-use-guidelines) se o plano Hobby permite uso comercial. Não foi possível confirmar isso na leitura de 2026-11-19.
- **LGPD:** a carga tem CPF, nome, telefone e dados bancários. Hospedar isso exige aval de quem responde pela carteira (contrato com o banco, DPA com Vercel e Neon, região dos dados).
- Até lá, use o ambiente só com as fixtures sintéticas (`make fixtures`).
