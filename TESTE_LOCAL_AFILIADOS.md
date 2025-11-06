# 🧪 Guia de Teste Local - Conversão de Links Afiliados

Este guia explica como testar a conversão de links do Mercado Livre localmente antes do deploy.

---

## 📋 Pré-requisitos

1. Python 3.11+ instalado
2. Dependências instaladas: `pip install -r requirements.txt`
3. Conta ativa no programa de afiliados do Mercado Livre

---

## 🚀 Passo a Passo

### **Passo 1: Gerar Cookies de Autenticação**

Os cookies são necessários para autenticar as chamadas à API do Mercado Livre.

```bash
python generate_ml_cookies.py
```

**O que vai acontecer:**
1. 🌐 Uma janela do Chrome vai abrir automaticamente
2. 👤 Faça login manualmente na sua conta do Mercado Livre
3. 📱 Navegue até o dashboard de afiliados
4. ⏳ Aguarde alguns segundos (o script detecta o login automaticamente)
5. ✅ Os cookies serão salvos em `sessions/ml_cookies.json`

**Resultado Esperado:**
```
✅ COOKIES SALVOS COM SUCESSO!
📁 Arquivo: session/ml_cookies.json
📅 Gerado em: 2025-11-05 17:30:00 UTC
⏰ Expira em: ~30 dias
```

---

### **Passo 2: Testar Conversão de Link**

Agora vamos testar se a conversão está funcionando:

```bash
python test_affiliate_conversion.py "https://produto.mercadolivre.com.br/MLB-4558937712-calca-legging-max-lupo-cintura-alta-academia-lupo-_JM"
```

**Resultado Esperado (Sucesso):**
```
✅ CONVERSÃO BEM-SUCEDIDA!
🔗 Link original:  https://produto.mercadolivre.com.br/MLB-4558937712...
🎯 Link afiliado:  https://mercadolivre.com/sec/XXXXXXX
🏪 Marketplace:    mercadolivre
📊 Status:         success
```

**Resultado Esperado (Falha - Cookies Inválidos):**
```
❌ ERRO NA CONVERSÃO
Erro: Cookies expirados ou inválidos. Execute generate_ml_cookies.py

💡 DICA: Parece ser um problema com os cookies.
   Execute novamente: python generate_ml_cookies.py
```

---

## 🔍 Verificações Importantes

### ✅ Checklist Pré-Deploy

Execute cada teste e confirme o resultado:

- [ ] Cookies gerados com sucesso (`session/ml_cookies.json` existe)
- [ ] Conversão de link funciona localmente
- [ ] Link afiliado retornado é diferente do original
- [ ] Link afiliado contém o domínio `mercadolivre.com` ou similar

### 🚨 Possíveis Problemas

| Problema | Causa | Solução |
|----------|-------|---------|
| `ModuleNotFoundError: bs4` | beautifulsoup4 não instalado | `pip install beautifulsoup4` |
| `Arquivo de cookies não encontrado` | Cookies não gerados | Execute `python generate_ml_cookies.py` |
| `Cookies expirados ou inválidos` | Sessão expirou (~30 dias) | Gere novos cookies |
| `InvalidLinkError` | Link não é do Mercado Livre | Verifique o formato do link |
| `MLRateLimitError` | Muitas requisições | Aguarde alguns minutos |

---

## 📝 Exemplos de Links para Testar

```bash
# Link de produto padrão
python test_affiliate_conversion.py "https://produto.mercadolivre.com.br/MLB-4558937712-calca-legging-max-lupo-cintura-alta-academia-lupo-_JM"

# Link de produto curto
python test_affiliate_conversion.py "https://www.mercadolivre.com.br/100-whey-protein-refil-900g-sabor-chocolate-ftw/p/MLB22813942"

# Link com código MLB
python test_affiliate_conversion.py "https://produto.mercadolivre.com.br/MLB-3967173105"
```

---

## 🎯 Após Testes Bem-Sucedidos

Quando todos os testes passarem localmente:

1. ✅ Commit dos arquivos modificados
2. 🚀 Deploy no servidor
3. 📦 Copiar `session/ml_cookies.json` para o servidor

---

## 🔐 Segurança

⚠️ **IMPORTANTE:**

- **NÃO** faça commit do arquivo `session/ml_cookies.json`
- Arquivo já protegido pelo `.gitignore` (padrão `*.json` e `session/`)
- Mantenha os cookies em local seguro
- Renove os cookies a cada ~30 dias

---

## 💡 Dicas

1. **Cookies Expiram:** Marque no calendário quando precisará renovar (~30 dias)
2. **Rate Limit:** Evite fazer muitas conversões em sequência (a API do ML tem limites)
3. **Logs:** Use os logs para diagnosticar problemas (`app_modules/affiliate/logger.py`)
4. **Fallback:** Se a conversão falhar, o sistema usa o link original automaticamente

---

## 🆘 Precisa de Ajuda?

Se os testes falharem:

1. Verifique os logs detalhados
2. Confirme que está logado no programa de afiliados
3. Valide que os cookies foram gerados corretamente
4. Teste com outro link de produto

---

## 📚 Documentação Adicional

- **Discovery do Mercado Livre:** `docs/discovery/mercadolivre-discovery.md`
- **Código do Conversor:** `app_modules/affiliate/converters/mercadolivre.py`
- **Manager de Afiliados:** `app_modules/affiliate/manager.py`
