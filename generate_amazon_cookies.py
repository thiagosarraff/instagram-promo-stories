#!/usr/bin/env python3
"""
Script para gerar cookies de autenticação do Amazon Associates

INSTRUÇÕES:
1. Execute este script: python generate_amazon_cookies.py
2. Uma janela do browser será aberta
3. Faça login manualmente no Amazon Associates
4. Após login bem-sucedido, aguarde 5 segundos
5. Digite seu Associate Tag (Tracking ID) quando solicitado
6. Os cookies serão salvos automaticamente em sessions/amazon_cookies.json

IMPORTANTE:
- Cookies são OPCIONAIS para Amazon (usados apenas para validação avançada)
- Conversão de links funciona SEM cookies
- Este script é fornecido para validação opcional de produtos

Amazon Associates Dashboard:
https://affiliate-program.amazon.com.br/
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright


async def generate_amazon_cookies():
    print("=" * 70)
    print("🔐 GERADOR DE COOKIES DO AMAZON ASSOCIATES")
    print("=" * 70)
    print()
    print("⚠️  ATENÇÃO: Cookies são OPCIONAIS para Amazon!")
    print("   Conversão de links funciona SEM cookies.")
    print("   Este script é para validação avançada opcional.")
    print()

    # Solicitar Associate Tag
    print("=" * 70)
    print("📝 ANTES DE COMEÇAR")
    print("=" * 70)
    print()
    print("Você precisa do seu Amazon Associate Tag (Tracking ID).")
    print()
    print("Como encontrar seu Associate Tag:")
    print("1. Acesse: https://affiliate-program.amazon.com.br/")
    print("2. Faça login no Amazon Associates")
    print("3. Clique em 'Tools' > 'Product Links'")
    print("4. Seu Associate Tag está no formato: nome-tag-20")
    print()
    print("Exemplo de formato válido: promozone-20")
    print()

    associate_tag = input("👉 Digite seu Associate Tag: ").strip()

    if not associate_tag:
        print()
        print("❌ Associate Tag é obrigatória!")
        print("   Execute o script novamente e forneça sua tag.")
        return

    # Validate format
    import re
    pattern = r'^[a-z0-9]+-[a-z0-9]+-\d+$'
    if not re.match(pattern, associate_tag):
        print()
        print("❌ Formato de Associate Tag inválido!")
        print(f"   Tag fornecida: {associate_tag}")
        print("   Formato esperado: nome-tag-20 (exemplo: promozone-20)")
        return

    print()
    print("✅ Associate Tag válida!")
    print()

    # Create sessions directory
    sessions_dir = Path('sessions')
    sessions_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        print("=" * 70)
        print("🌐 ABRINDO BROWSER")
        print("=" * 70)
        print()

        # Launch browser (visible)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            locale='pt-BR',
        )
        page = await context.new_page()

        # Navigate to Amazon Associates
        print("📱 Navegando para Amazon Associates...")
        await page.goto('https://affiliate-program.amazon.com.br/', wait_until='load')
        print()

        print("=" * 70)
        print("👤 FAÇA LOGIN MANUALMENTE")
        print("=" * 70)
        print()
        print("Por favor, faça login no browser que foi aberto.")
        print("Aguardando login...")
        print()
        print("⏳ Esperando até 3 minutos...")
        print()

        # Wait for login redirect to dashboard
        login_successful = False
        try:
            # Wait for URL to contain 'home' (indicates dashboard)
            await page.wait_for_url('**/home**', timeout=180000)  # 3 minutes
            login_successful = True
            print("✅ Login detectado! Dashboard carregado.")

        except Exception:
            # If timeout, check if user is on dashboard manually
            current_url = page.url
            if 'home' in current_url or 'dashboard' in current_url:
                login_successful = True
                print("✅ Login detectado! Você está no dashboard.")
            else:
                print()
                print("❌ Timeout aguardando login.")
                print(f"   URL atual: {current_url}")
                print()
                print("Possíveis causas:")
                print("- Você não fez login no tempo esperado (3 minutos)")
                print("- Você está em uma página diferente do dashboard")
                print("- Amazon está solicitando autenticação adicional (2FA, CAPTCHA)")
                print()
                await browser.close()
                return

        if not login_successful:
            await browser.close()
            return

        print()
        print("=" * 70)
        print("🍪 EXPORTANDO COOKIES")
        print("=" * 70)
        print()

        # Wait a bit to ensure all cookies are set
        print("⏳ Aguardando 5 segundos para garantir que cookies foram setados...")
        await asyncio.sleep(5)

        # Export cookies
        cookies = await context.cookies()
        print(f"📦 {len(cookies)} cookies capturados")
        print()

        # Structure cookie data
        cookie_data = {
            'marketplace': 'amazon',
            'associate_tag': associate_tag,
            'generated_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=90)).isoformat(),  # Amazon cookies ~90 days
            'note': 'Cookies são opcionais para Amazon. Usados apenas para validação avançada.',
            'cookies': cookies
        }

        # Save to file
        cookie_file = sessions_dir / 'amazon_cookies.json'
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookie_data, f, indent=2, ensure_ascii=False)

        print("=" * 70)
        print("✅ COOKIES SALVOS COM SUCESSO!")
        print("=" * 70)
        print()
        print(f"📁 Arquivo: {cookie_file}")
        print(f"🏷️  Associate Tag: {associate_tag}")
        print(f"📅 Data de geração: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"⏰ Expiração estimada: ~90 dias")
        print()

        print("=" * 70)
        print("📋 PRÓXIMOS PASSOS")
        print("=" * 70)
        print()
        print("1. ✅ Cookies foram salvos localmente")
        print(f"2. 📝 Configure AMAZON_ASSOCIATE_TAG={associate_tag} no arquivo .env")
        print("3. 🔧 Reinicie o aplicativo para carregar a configuração")
        print("4. 🚀 O AmazonConverter usará a tag para gerar links de afiliados")
        print()
        print("⚠️  LEMBRE-SE:")
        print("   - Cookies expiram em ~90 dias")
        print("   - Execute este script novamente quando necessário")
        print("   - Cookies são OPCIONAIS - conversão funciona sem eles")
        print()

        await browser.close()


def main():
    """Main entry point"""
    try:
        asyncio.run(generate_amazon_cookies())
        print()
        print("✅ Script finalizado com sucesso!")
        print()

    except KeyboardInterrupt:
        print()
        print()
        print("⚠️  Script interrompido pelo usuário (Ctrl+C)")
        print()
        sys.exit(1)

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERRO DURANTE EXECUÇÃO")
        print("=" * 70)
        print()
        print(f"Erro: {e}")
        print()
        print("Possíveis soluções:")
        print("- Verifique sua conexão com a internet")
        print("- Tente executar o script novamente")
        print("- Verifique se o Playwright está instalado: pip install playwright")
        print("- Execute: playwright install chromium")
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()
