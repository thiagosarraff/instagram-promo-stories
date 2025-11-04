# Instagram Session Setup

## Problema

O Instagram requer verificação quando você faz login de um novo dispositivo/IP. Em ambientes Docker não-interativos, não é possível inserir o código de verificação manualmente.

## Solução: Arquivo de Sessão

Gere o arquivo de sessão **localmente no seu computador** (onde você pode inserir o código de verificação) e depois copie para o servidor.

---

## Passo a Passo

### 1️⃣ No seu computador local

#### Instalar dependências
```bash
pip install instagrapi python-dotenv
```

#### Configurar .env local
Crie um arquivo `.env` com suas credenciais:
```env
INSTAGRAM_USERNAME=seu_usuario
INSTAGRAM_PASSWORD=sua_senha
```

#### Executar script de geração
```bash
python generate_session.py
```

**Se o Instagram pedir verificação:**
- Verifique seu email/SMS
- Digite o código quando solicitado
- O script salvará a sessão automaticamente

**Resultado:** Arquivo `session_seu_usuario.json` será criado

---

### 2️⃣ Copiar arquivo para o servidor

#### Criar pasta de sessões no servidor
```bash
ssh seu_usuario@seu_servidor
cd ~/instagram-promo-stories
mkdir -p session
```

#### Copiar arquivo do local para servidor
```bash
# Do seu computador local
scp session_seu_usuario.json seu_usuario@seu_servidor:~/instagram-promo-stories/session/
```

---

### 3️⃣ Reiniciar Docker no servidor

```bash
# No servidor
cd ~/instagram-promo-stories
docker-compose restart
```

---

## Verificação

Teste a API novamente com o n8n. Agora você deve ver nos logs:

```
🔐 ETAPA 2: Fazendo login como @seu_usuario...
   📂 Carregando sessão salva...
✅ Login bem-sucedido usando sessão salva!
```

---

## Estrutura de Arquivos

```
instagram-promo-stories/
├── session/                          # ← Pasta montada pelo Docker
│   └── session_seu_usuario.json     # ← Arquivo de sessão
├── generate_session.py               # ← Script para gerar sessão
├── .env                              # ← Credenciais
└── docker-compose.yml                # ← Volume: ./session:/app/session
```

---

## Dicas de Segurança

1. **Nunca commite** o arquivo de sessão no Git (já está no .gitignore)
2. **Proteja as permissões** no servidor:
   ```bash
   chmod 600 session/session_*.json
   ```
3. **Regenere periodicamente** (recomendado a cada 30 dias)
4. **Use conta dedicada** para automação, não sua conta pessoal

---

## Troubleshooting

### Erro: "EOF when reading a line"
**Causa:** Instagram pediu verificação mas está em modo não-interativo
**Solução:** Siga os passos acima para gerar a sessão localmente

### Erro: "challenge_required"
**Causa:** Instagram detectou atividade suspeita
**Solução:**
1. Regenere a sessão localmente
2. Aguarde algumas horas antes de tentar novamente
3. Use proxy/VPN se estiver fazendo muitas requisições

### Sessão expirou
**Causa:** Sessões do Instagram expiram após ~30 dias de inatividade
**Solução:** Regenere a sessão seguindo o processo novamente

---

## Manutenção

### Renovar sessão a cada 30 dias:
```bash
# Local
python generate_session.py

# Copiar para servidor
scp session_seu_usuario.json usuario@servidor:~/instagram-promo-stories/session/

# Reiniciar no servidor
ssh usuario@servidor "cd ~/instagram-promo-stories && docker-compose restart"
```
