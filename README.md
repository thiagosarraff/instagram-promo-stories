# 📱 Instagram Stories Automation API

Sistema automatizado para criar e publicar stories promocionais no Instagram via API HTTP.

## ⚡ Deploy Rápido (4 passos)

### 1. Configure Variáveis de Ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais do Instagram
```

### 2. Gere Sessões de Autenticação

**⚠️ IMPORTANTE:** Antes de iniciar o container, você precisa gerar as sessões de autenticação.

#### 🔐 Sessão do Instagram (Obrigatório)

```bash
# Criar diretórios necessários
mkdir -p sessions logs

# Gerar sessão do Instagram
python3 generate_instagram_session.py

# Seguir instruções no terminal:
# - Login será feito automaticamente
# - Sessão salva em sessions/
```

#### 🛒 Cookies do Mercado Livre (Opcional - para links afiliados)

```bash
# Instalar dependências (se necessário)
pip3 install -r requirements.txt
playwright install chromium

# Gerar cookies do Mercado Livre
python3 generate_ml_cookies.py

# Seguir instruções:
# 1. Browser abrirá automaticamente
# 2. Faça login manualmente no Mercado Livre
# 3. Navegue para o programa de afiliados
# 4. Cookies serão salvos automaticamente em sessions/
```

**📝 Nota:** Os cookies do Mercado Livre expiram em ~30 dias. Execute `generate_ml_cookies.py` novamente quando necessário.

### 3. Inicie o Container

```bash
docker-compose up -d
```

### 4. Teste

```bash
curl http://localhost:5000/health
```

---

## 📋 Requisitos

### Ambiente de Produção (Docker)
- Docker + Docker Compose
- Credenciais Instagram
- 2GB RAM, 2 CPU cores
- Porta 5000 disponível

### Geração de Sessões (Local/Host)
- Python 3.11+
- Playwright (para cookies ML)
- Dependências: `pip install -r requirements.txt`

---

## 🔧 Configuração (.env)

```env
# OBRIGATÓRIO
INSTAGRAM_USERNAME=seu_usuario
INSTAGRAM_PASSWORD=sua_senha

# OPCIONAL
API_PORT=5000
LOG_LEVEL=INFO
```

**Instagram com 2FA:** Gere senha de app em Configurações → Segurança → Senhas de Apps

---

## 🔗 Sistema de Links Afiliados

O sistema converte automaticamente links de produtos em links afiliados do Mercado Livre.

### Configuração

**1. Gere os Cookies do Mercado Livre:**

```bash
# Instalar dependências
pip3 install -r requirements.txt
playwright install chromium

# Executar gerador de cookies
python3 generate_ml_cookies.py
```

**2. Faça Login Manualmente:**
- Browser abrirá automaticamente
- Faça login na sua conta do Mercado Livre
- Acesse o programa de afiliados
- Aguarde confirmação (cookies salvos em `sessions/ml_cookies.json`)

**3. Reinicie o Container:**

```bash
docker-compose restart
```

### Funcionamento

**Com Cookies Válidos:**
```
Link original:  https://produto.mercadolivre.com.br/MLB-123456...
Link afiliado:  https://mercadolivre.com/sec/XXXXXXX ✅
```

**Sem Cookies (Fallback):**
```
Link original:  https://produto.mercadolivre.com.br/MLB-123456...
Link usado:     https://produto.mercadolivre.com.br/MLB-123456... ⚠️
```

### Renovação de Cookies

Os cookies expiram em ~30 dias. Quando expirar:

```bash
python3 generate_ml_cookies.py
docker-compose restart
```

**Monitoramento:**
```bash
# Ver logs de conversão
docker logs insta-stories-api | grep -i "conversion"

# Sucesso
✅ Conversion successful for mercadolivre

# Fallback (cookies expirados)
⚠️  Conversion failed for mercadolivre, using fallback
```

---

## 🚀 API

### POST /post-story

Cria e publica um story promocional no Instagram.

#### 📥 Request Body (JSON)

| Campo | Tipo | Obrigatório | Formato | Descrição | Exemplo |
|-------|------|-------------|---------|-----------|---------|
| `product_name` | string | ✅ Sim | 1-200 caracteres | Nome do produto | `"Carregador Apple USB-C 20W"` |
| `price` | string | ✅ Sim | 1-50 caracteres | Preço atual do produto | `"R$ 35,41"` ou `"35.41"` |
| `product_image_url` | string | ✅ Sim | URL válida | URL da imagem do produto (HTTP/HTTPS) | `"https://exemplo.com/produto.jpg"` |
| `affiliate_link` | string | ✅ Sim | URL válida | Link de afiliado ou produto para swipe-up | `"https://mercadolivre.com.br/MLB-123456"` |
| `marketplace_name` | string | ✅ Sim | 1-50 caracteres | Nome do marketplace (texto do botão) | `"mercadolivre"`, `"amazon"`, `"magalu"` |
| `headline` | string | ⚪ Opcional | 1-100 caracteres | Texto do título no topo do story | `"OFERTA RELÂMPAGO"` (padrão: `"OFERTA IMPERDÍVEL"`) |
| `template_scenario` | integer | ⚪ Opcional | 1, 2, 3 ou 4 | Cenário do template (auto-selecionado se omitido) | `1` |
| `price_old` | string | ⚪ Opcional | 1-50 caracteres | Preço antigo/riscado (mostra desconto) | `"R$ 48,50"` ou `"48.50"` |
| `coupon_code` | string | ⚪ Opcional | 1-50 caracteres | Código do cupom promocional | `"PROMO10"` |

#### 📋 Formatos Esperados

**`price`** e **`price_old`**: Formatos flexíveis - aceita ponto ou vírgula
- ✅ `"R$ 35,41"` → normalizado para `R$ 35,41`
- ✅ `"R$ 35.41"` → normalizado para `R$ 35,41`
- ✅ `"35.41"` → normalizado para `R$ 35,41`
- ✅ `"35,41"` → normalizado para `R$ 35,41`
- ✅ `"35"` → normalizado para `R$ 35,00`
- ⚡ Sistema converte automaticamente para formato brasileiro (vírgula decimal)

**`product_image_url`**: URL pública acessível
- ✅ Formatos: JPG, JPEG, PNG, WebP
- ✅ Tamanho recomendado: 800x800px a 1500x1500px
- ⚠️ URL deve ser pública (sem autenticação)

**`marketplace_name`**: Valores suportados com mapeamento automático
- `"mercadolivre"` → LINK MERCADO LIVRE
- `"amazon"` → LINK AMAZON
- `"magalu"` → LINK MAGALU
- `"americanas"` → LINK AMERICANAS
- `"shopee"` → LINK SHOPEE
- `"aliexpress"` → LINK ALIEXPRESS
- `"casasbahia"` → LINK CASAS BAHIA
- `"extra"` → LINK EXTRA
- `"pontofrio"` → LINK PONTO FRIO
- `"submarino"` → LINK SUBMARINO
- Outros valores → `LINK {NOME_CUSTOMIZADO}`

**`template_scenario`**: Seleção automática de template (OPCIONAL)
- **AUTO** (padrão se omitido): Sistema escolhe baseado em dados fornecidos
  - Cenário 1: Apenas preço
  - Cenário 2: Preço + cupom
  - Cenário 3: Preço + preço antigo (desconto)
  - Cenário 4: Preço + preço antigo + cupom (completo)
- **Manual**: `1`, `2`, `3`, ou `4` para forçar cenário específico

**`price_old`**: Preço anterior/riscado (OPCIONAL)
- ✅ Formato igual ao `price`: `"R$ 48,50"`
- ⚡ Ativa cálculo automático de desconto percentual
- 🎨 Renderiza com texto riscado + badge de % OFF

**`coupon_code`**: Código do cupom (OPCIONAL)
- ✅ Texto simples: `"PROMO10"`, `"BLACK50"`
- 🎨 Renderiza em destaque com fundo colorido

**`headline`**: Título do story (OPCIONAL)
- ✅ Texto em MAIÚSCULAS recomendado
- 📏 Máximo 100 caracteres (ajuste automático de fonte)
- 🎨 Padrão: `"OFERTA IMPERDÍVEL"`
- 💡 Exemplos: `"OFERTA RELÂMPAGO"`, `"BLACK FRIDAY"`, `"MEGA PROMOÇÃO"`

#### 📤 Response

**Sucesso (200 OK):**
```json
{
  "status": "success",
  "message": "Story posted successfully",
  "story_id": "3758456134287145845",
  "error_code": null
}
```

**Erro de Validação (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Invalid template_scenario. Must be 1, 2, 3, or 4",
  "story_id": null,
  "error_code": "VALIDATION_ERROR"
}
```

**Erro de Renderização (500 Internal Server Error):**
```json
{
  "status": "error",
  "message": "Failed to create story image from product data",
  "story_id": null,
  "error_code": "RENDERING_FAILED"
}
```

**Erro de Postagem (500 Internal Server Error):**
```json
{
  "status": "error",
  "message": "Failed to post story to Instagram",
  "story_id": null,
  "error_code": "POSTING_FAILED"
}
```

#### 🔑 Códigos de Erro

| Código | Descrição | Ação Recomendada |
|--------|-----------|------------------|
| `VALIDATION_ERROR` | Dados inválidos no request | Verifique formato dos campos obrigatórios |
| `CONFIG_ERROR` | Credenciais Instagram ausentes | Configure `INSTAGRAM_USERNAME` e `INSTAGRAM_PASSWORD` no `.env` |
| `RENDERING_FAILED` | Falha ao gerar imagem do story | Verifique se `product_image_url` é acessível |
| `POSTING_FAILED` | Falha ao postar no Instagram | Verifique credenciais e sessão do Instagram |
| `INTERNAL_ERROR` | Erro inesperado no servidor | Verifique logs do container |

#### 📝 Exemplo Completo (cURL)

```bash
curl -X POST http://localhost:5000/post-story \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Carregador Fonte Apple iPad iPhone Turbo Original USB-C 20W",
    "price": "35.41",
    "price_old": "48.50",
    "product_image_url": "https://minio.exemplo.com/products/carregador-apple.png",
    "affiliate_link": "https://mercadolivre.com.br/MLB-3456789012",
    "marketplace_name": "mercadolivre",
    "headline": "OFERTA RELÂMPAGO",
    "coupon_code": "PROMO10"
  }'
```

#### 📝 Exemplo n8n HTTP Request Node

```json
{
  "method": "POST",
  "url": "http://localhost:5000/post-story",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "product_name": "={{ $json.productName }}",
    "price": "={{ $json.price }}",
    "price_old": "={{ $json.priceOld }}",
    "product_image_url": "={{ $json.imageUrl }}",
    "affiliate_link": "={{ $json.affiliateLink }}",
    "marketplace_name": "={{ $json.marketplace }}",
    "headline": "={{ $json.headline || 'OFERTA IMPERDÍVEL' }}",
    "coupon_code": "={{ $json.couponCode }}"
  }
}
```

---

### GET /health

Verifica status da API (health check).

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-04T13:28:11.123456+00:00"
}
```

---

### GET /docs

Documentação Swagger interativa (FastAPI auto-generated).

Acesse em: `http://localhost:5000/docs`

---

## 🐳 Comandos Docker

```bash
docker-compose up -d              # Iniciar
docker-compose down               # Parar
docker-compose logs -f            # Ver logs
docker-compose restart            # Reiniciar
docker-compose up --build         # Rebuild
docker stats insta-stories-api    # Monitorar recursos
```

---

## 🔗 Integração n8n

**HTTP Request Node:**
- Method: POST
- URL: `http://localhost:5000/post-story`
- Headers: `Content-Type: application/json`
- Body: JSON com dados do produto

**Workflow:**
```
[Trigger] → [Get Data] → [POST /post-story] → [IF success] → [Handler]
```

---

## 📦 Deploy VPS

### Passo a Passo Completo

#### 1. Clone e Configure

```bash
# No VPS
git clone <repo-url>
cd insta-stories

# Configure variáveis de ambiente
cp .env.example .env
nano .env  # Edite INSTAGRAM_USERNAME e INSTAGRAM_PASSWORD

# Crie diretórios necessários
mkdir -p sessions logs
```

#### 2. Gere Sessão do Instagram

```bash
# Instalar dependências Python
pip3 install -r requirements.txt

# Gerar sessão do Instagram
python3 generate_instagram_session.py

# Seguir instruções no terminal
# Sessão será salva em sessions/
```

#### 3. (Opcional) Gere Cookies do Mercado Livre

**⚠️ Apenas se precisar de conversão de links afiliados:**

```bash
# Instalar Playwright
playwright install chromium
playwright install-deps chromium

# Gerar cookies (requer X11/display ou VNC)
python3 generate_ml_cookies.py

# Alternativamente: gere no PC local e copie via SCP
# scp sessions/ml_cookies.json usuario@servidor:~/insta-stories/sessions/
```

#### 4. Inicie o Container

```bash
docker-compose up -d
```

#### 5. Valide o Deploy

```bash
# Verificar se container está rodando
docker ps | grep insta-stories

# Testar health check
curl http://localhost:5000/health

# Verificar logs
docker logs insta-stories-api --tail 50

# Verificar conversão de links (se configurado)
docker logs insta-stories-api | grep -i "mercado.*converter"
```

### Requisitos VPS

- **OS:** Ubuntu 20.04+ (ou Debian 11+)
- **RAM:** 2GB mínimo
- **CPU:** 2 cores
- **Disco:** 10GB
- **Portas:** 5000 (ou conforme `.env`)

### Estrutura de Diretórios

```
~/insta-stories/
├── sessions/                    ← Sessões e cookies (NÃO versionado)
│   ├── ml_cookies.json         ← Cookies Mercado Livre (opcional)
│   └── session_*.json          ← Sessão Instagram (obrigatório)
├── logs/                        ← Logs da aplicação
├── .env                         ← Credenciais (NÃO versionado)
└── docker-compose.yml           ← Configuração Docker
```

### Troubleshooting VPS

**Container não inicia:**
```bash
docker logs insta-stories-api
# Verificar se sessão do Instagram existe
ls -la sessions/
```

**Conversão de links não funciona:**
```bash
# Verificar se cookies existem
docker exec insta-stories-api ls -la /app/sessions/ml_cookies.json

# Regenerar cookies
python3 generate_ml_cookies.py
docker-compose restart
```

**Porta já em uso:**
```bash
# Verificar processo usando a porta
sudo lsof -i :5000

# Alterar porta no .env
echo "API_PORT=5001" >> .env
docker-compose up -d
```

---

## 🐛 Troubleshooting

### 🔐 Problemas de Autenticação

**Sessão do Instagram não encontrada:**
```bash
# Erro: "Instagram session not found"
# Solução: Gerar sessão
python3 generate_instagram_session.py
docker-compose restart
```

**Cookies do Mercado Livre expirados:**
```bash
# Erro: "Conversion failed for mercadolivre, using fallback"
# Solução: Regenerar cookies
python3 generate_ml_cookies.py
docker-compose restart

# Verificar se funcionou
docker logs insta-stories-api | grep -i "conversion successful"
```

**Credenciais faltando no .env:**
```bash
cat .env  # Verifique INSTAGRAM_USERNAME e INSTAGRAM_PASSWORD
```

**Instagram Login Failed:**
- Use senha de app se tiver 2FA ativado
- Faça login manual no app do Instagram
- Aguarde 24-48h antes de tentar novamente
- Verifique se a conta não está bloqueada

### 🐳 Problemas com Docker

**Container reinicia constantemente:**
```bash
docker-compose logs insta-stories  # Ver erro específico
docker logs insta-stories-api --tail 100
```

**Porta em uso:**
```bash
# Verificar o que está usando a porta
sudo lsof -i :5000

# Usar porta diferente
echo "API_PORT=5001" >> .env
docker-compose down && docker-compose up -d
```

**API não responde:**
```bash
docker-compose ps                   # Container rodando?
curl http://localhost:5000/health   # Teste health
docker-compose logs --tail=50       # Ver logs
docker stats insta-stories-api      # Ver recursos
```

**Volume não montado (sessões não acessíveis):**
```bash
# Verificar volumes montados
docker inspect insta-stories-api | grep -A 10 "Mounts"

# Verificar se sessões estão acessíveis no container
docker exec insta-stories-api ls -la /app/sessions/

# Recriar container se necessário
docker-compose down && docker-compose up -d
```

### 📝 Logs e Debug

**Ver logs em tempo real:**
```bash
docker-compose logs -f insta-stories
```

**Filtrar logs de conversão:**
```bash
docker logs insta-stories-api | grep -i "conversion"
docker logs insta-stories-api | grep -i "affiliate"
docker logs insta-stories-api | grep -i "mercadolivre"
```

**Ver últimas 100 linhas:**
```bash
docker-compose logs --tail=100 insta-stories
```

**Logs de requests específicos:**
```bash
# Ver requests recebidos
docker logs insta-stories-api | grep "POST /post-story"

# Ver erros
docker logs insta-stories-api | grep -i "error"
```

### 🔄 Renovação Periódica

**Cookies do Mercado Livre (a cada 30 dias):**
```bash
python3 generate_ml_cookies.py
docker-compose restart
```

**Sessão do Instagram (se expirar):**
```bash
python3 generate_instagram_session.py
docker-compose restart
```

**Verificar validade:**
```bash
# Ver data de geração dos cookies
docker exec insta-stories-api cat /app/sessions/ml_cookies.json | grep "generated_at"

# Testar conversão
curl -X POST http://localhost:5000/post-story \
  -H "Content-Type: application/json" \
  -d '{"product_name": "Teste", "price": "10", "product_image_url": "https://via.placeholder.com/800", "affiliate_link": "https://produto.mercadolivre.com.br/MLB-123", "marketplace_name": "mercadolivre"}'
```

---

## 📊 Monitoramento

```bash
# Logs tempo real
docker-compose logs -f insta-stories

# Últimas 100 linhas
docker-compose logs --tail=100 insta-stories

# Métricas
docker stats insta-stories-api

# Health check contínuo
watch -n 5 'curl -s http://localhost:5000/health'
```

---

## 🛡️ Segurança

✅ Senhas mascaradas nos logs  
✅ Container non-root (UID 1000)  
✅ `.env` no .gitignore  
✅ Resource limits configurados  
✅ Health checks implementados  

**Checklist:**
- [ ] `.env` nunca commitado
- [ ] Credenciais rotacionadas
- [ ] Logs revisados
- [ ] Firewall configurado

---

## 🧪 Testes

```bash
pytest test_api.py -v
```

**Status:** 28 testes, 100% aprovados ✅

---

## 📚 Documentação Completa

- FastAPI: https://fastapi.tiangolo.com/
- Instagrapi: https://subzeroid.github.io/instagrapi/
- Docker: https://docs.docker.com/

---

## 📝 Versão 2.0.0

✅ HTTP API com FastAPI
✅ Docker + Docker Compose
✅ Environment variables
✅ 4 templates de story
✅ Sistema de conversão de links afiliados (Mercado Livre)
✅ Geração automática de sessões (Instagram + ML)
✅ Fallback automático para links sem conversão
✅ Logs estruturados com fallback para console

**Features:**
- ✅ Stories 1.1, 1.2, 1.3
- ✅ Story 4.1 - Links afiliados Mercado Livre
- ✅ Story 4.2 - Links afiliados Amazon Associates
- ✅ Story 4.3 - Shopee (preparado, não implementado)

---

## 🔗 Sistema de Links Afiliados Amazon Associates

O sistema converte automaticamente links de produtos Amazon em links afiliados com rastreamento por fonte.

### Configuração Amazon Associates

**1. Obtenha suas Tags Amazon:**

1. Acesse: https://associados.amazon.com.br/
2. Faça login ou cadastre-se
3. Vá em **Tools** → **Manage Your Tracking IDs**
4. Anote seu **Store ID** (ex: `baroneamz-20`)
5. Crie **Tracking IDs** específicos:
   - `promozone.stories-20` (Instagram Stories)
   - `promozone.posts-20` (Instagram Posts)
   - `promozone.reels-20` (Instagram Reels)
   - `promozone.bio-20` (Link na Bio)

**2. Configure o `.env`:**

```bash
# Store ID (conta principal Amazon Associates)
AMAZON_ASSOCIATE_TAG=baroneamz-20

# Tracking ID (fonte específica - opcional)
AMAZON_TRACKING_ID=promozone.stories-20
```

**Como funciona:**
- **Store ID**: Vendas creditadas na sua conta principal
- **Tracking ID**: Rastreamento individual por fonte no painel Amazon
- Se `AMAZON_TRACKING_ID` não for definido, usa `AMAZON_ASSOCIATE_TAG`

**3. Reinicie o Container:**

```bash
docker-compose restart
```

### Funcionamento Amazon

**Link Original:**
```
https://www.amazon.com.br/Apple-iPhone-13/dp/B09T4YK6QK/...
```

**Link Afiliado:**
```
https://amazon.com.br/dp/B09T4YK6QK?tag=promozone.stories-20
```

### Rastreamento por Fonte

Crie múltiplos Tracking IDs para rastrear vendas por fonte:

| Tracking ID | Uso | Configuração |
|-------------|-----|--------------|
| `promozone.stories-20` | Instagram Stories | `AMAZON_TRACKING_ID=promozone.stories-20` |
| `promozone.posts-20` | Instagram Posts | `AMAZON_TRACKING_ID=promozone.posts-20` |
| `promozone.reels-20` | Instagram Reels | `AMAZON_TRACKING_ID=promozone.reels-20` |
| `promozone.bio-20` | Link na Bio | `AMAZON_TRACKING_ID=promozone.bio-20` |

**Benefício**: Ver estatísticas separadas no painel Amazon Associates por fonte de tráfego.

**Como trocar**: Edite `.env` e reinicie o app conforme a fonte de publicação.

### Monitoramento de Vendas Amazon

**Acessar Relatórios:**
1. Login: https://associados.amazon.com.br/
2. Menu: **Reports** → **Earnings Report**
3. Filtrar por Tracking ID para ver vendas por fonte

**Métricas Disponíveis:**
- Cliques por Tracking ID
- Conversões por fonte
- Receita por campanha
- Performance comparativa

### Testes Amazon

**Teste Rápido:**
```bash
python test_tracking_id.py
```

**Suite Completa:**
```bash
pytest tests/test_affiliate/test_amazon.py -v
```

**Resultado esperado**: `27 passed, 1 skipped`

### Troubleshooting Amazon

**"AMAZON_ASSOCIATE_TAG not set"**
- **Causa**: Variável não configurada no `.env`
- **Solução**: Adicione `AMAZON_ASSOCIATE_TAG=seu-tag-20` no `.env`

**"Invalid Associate Tag format"**
- **Formato correto**: `nome-tag-20` ou `nome.categoria-tag-20`
- **Exemplos válidos**: `baroneamz-20`, `promozone.stories-20`

**Links não estão convertendo**
- Verifique logs: `docker-compose logs app | grep -i amazon`
- Execute teste manual: `python test_tracking_id.py`
- Confirme que `.env` está configurado corretamente

**Validação de Tag:**

Formato aceito: `^[a-zA-Z0-9.]+(-[a-zA-Z0-9.]+)*-\d+$`

**Exemplos válidos:**
- `baroneamz-20` ✅
- `promozone.stories-20` ✅
- `tech-store-21` ✅

**Exemplos inválidos:**
- `baroneamz` ❌ (falta o `-20`)
- `promo zone-20` ❌ (espaço não permitido)
- `store@tech-20` ❌ (caractere especial não permitido)

### Arquivos do Sistema Amazon

**Código Principal:**
```
app_modules/affiliate/converters/amazon.py (336 linhas)
├── Conversor principal de links Amazon
├── Validação de tags e ASINs
└── Construção de links afiliados

app_modules/affiliate/exceptions.py (modificado)
└── 6 exceções específicas Amazon

app.py (modificado - linhas 59-88)
└── Registro do conversor Amazon com suporte a Tracking ID
```

**Testes:**
```
tests/test_affiliate/test_amazon.py (330 linhas)
└── 27 testes automatizados (100% cobertura)

test_tracking_id.py (107 linhas)
└── Script de teste rápido manual
```

**Status**: ✅ 100% funcional e em produção com 27/27 testes passando

---

**🚀 Pronto para deploy!**
