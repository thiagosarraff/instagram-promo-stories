# 📱 Instagram Stories Automation API

Sistema automatizado para criar e publicar stories promocionais no Instagram via API HTTP.

## ⚡ Deploy Rápido (3 passos)

### 1. Configure

```bash
cp .env.example .env
# Edite .env com suas credenciais do Instagram
```

### 2. Execute

```bash
mkdir -p templates logs session
docker-compose up -d
```

### 3. Teste

```bash
curl http://localhost:5000/health
```

---

## 📋 Requisitos

- Docker + Docker Compose
- Credenciais Instagram
- 2GB RAM, 2 CPU cores
- Porta 5000 disponível

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

```bash
# No VPS
git clone <repo-url>
cd insta-stories
cp .env.example .env
nano .env  # Configure credenciais
mkdir -p templates logs session
docker-compose up -d
curl http://localhost:5000/health
```

**Requisitos VPS:** Ubuntu 20.04+, 2GB RAM, 2 CPU, 10GB disco

---

## 🐛 Troubleshooting

### Credenciais faltando
```bash
cat .env  # Verifique INSTAGRAM_USERNAME e INSTAGRAM_PASSWORD
```

### Porta em uso
```env
API_PORT=5001  # Use porta diferente
```

### Login failed
- Use senha de app (se 2FA)
- Login manual no Instagram app
- Aguarde 24-48h

### Container reinicia
```bash
docker-compose logs insta-stories  # Veja o erro
```

### API não responde
```bash
docker-compose ps                  # Container rodando?
curl http://localhost:5000/health  # Teste health
docker-compose logs --tail=50      # Ver logs
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

## 📝 Versão 1.0.0

✅ HTTP API com FastAPI  
✅ Docker + Docker Compose  
✅ Environment variables  
✅ 4 templates de story  
✅ 28 testes unitários  

**Stories implementados:** 1.1, 1.2, 1.3 ✅

---

**🚀 Pronto para deploy!**
