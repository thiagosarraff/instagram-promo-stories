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

```json
{
  "product_name": "Carregador USB-C 20W",
  "price": "R$ 35,41",
  "product_image_url": "https://exemplo.com/produto.jpg",
  "affiliate_link": "https://link.com",
  "marketplace_name": "Mercado Livre",
  "template_scenario": 1
}
```

**Resposta:**
```json
{
  "status": "success",
  "message": "Story posted successfully"
}
```

### GET /health

Verifica status da API

### GET /docs

Documentação Swagger interativa

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
