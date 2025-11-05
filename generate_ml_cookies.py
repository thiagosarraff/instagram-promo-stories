#!/usr/bin/env python3
"""
Script para gerar cookies de autenticação do Mercado Livre

INSTRUÇÕES DE USO:
1. Execute: python generate_ml_cookies.py
2. Uma janela do browser será aberta
3. Faça login manualmente no programa de afiliados do Mercado Livre
4. Após login bem-sucedido, aguarde alguns segundos
5. Os cookies serão salvos automaticamente em sessions/ml_cookies.json

IMPORTANTE:
- Cookies expiram em aproximadamente 30 dias
- Execute este script novamente quando os cookies expirarem
- Mantenha o arquivo sessions/ml_cookies.json em local seguro
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright


async def generate_ml_cookies():
    """Generate Mercado Livre authentication cookies"""

    print("=" * 70)
    print("🔐 GERADOR DE COOKIES DO MERCADO LIVRE")
    print("=" * 70)
    print()

    async with async_playwright() as p:
        # Launch visible browser
        print("🌐 Abrindo navegador...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to ML affiliate program
        print("📱 Navegando para página de login do programa de afiliados...")
        print()

        # Try to go to affiliate dashboard directly (will redirect to login if needed)
        await page.goto('https://produto.mercadolivre.com.br/', wait_until='domcontentloaded')

        print("=" * 70)
        print("👤 INSTRUÇÕES:")
        print("   1. Faça login manualmente na janela do browser")
        print("   2. Acesse o dashboard de afiliados (se não estiver lá)")
        print("   3. Aguarde alguns segundos após o login")
        print("   4. Os cookies serão capturados automaticamente")
        print("=" * 70)
        print()
        print("⏳ Aguardando login... (timeout: 5 minutos)")
        print()

        # Wait for user to login (check for cookies)
        max_wait_time = 300  # 5 minutes
        start_time = asyncio.get_event_loop().time()

        while True:
            # Check if critical cookies are present
            cookies = await context.cookies()
            cookie_names = [c['name'] for c in cookies]

            # Look for ML auth cookies
            if 'ssid' in cookie_names and 'nsa_rotok' in cookie_names:
                print("✅ Login detectado!")
                break

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait_time:
                print("❌ Timeout aguardando login. Tente novamente.")
                await browser.close()
                return

            await asyncio.sleep(2)

        # Give extra time for all cookies to be set
        print("⏳ Aguardando cookies adicionais...")
        await asyncio.sleep(5)

        # Export all cookies
        cookies = await context.cookies()
        print(f"📦 {len(cookies)} cookies capturados")

        # Analyze JWT token to get expiration
        jwt_cookie = next((c for c in cookies if c['name'] == 'nsa_rotok'), None)
        estimated_expiry_days = 30  # Default

        if jwt_cookie:
            try:
                import base64
                token_parts = jwt_cookie['value'].split('.')
                if len(token_parts) >= 2:
                    payload_part = token_parts[1]
                    payload_part += '=' * (4 - len(payload_part) % 4)
                    payload = json.loads(base64.b64decode(payload_part))
                    exp_timestamp = payload.get('exp', 0)
                    now_timestamp = datetime.utcnow().timestamp()
                    estimated_expiry_days = int((exp_timestamp - now_timestamp) / 86400)
                    print(f"📅 Validade estimada: ~{estimated_expiry_days} dias")
            except Exception as e:
                print(f"⚠️  Não foi possível determinar validade exata (usando padrão: 30 dias)")

        # Prepare cookie data structure
        cookie_data = {
            'marketplace': 'mercadolivre',
            'generated_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=estimated_expiry_days)).isoformat(),
            'estimated_validity_days': estimated_expiry_days,
            'cookies': cookies,
            'note': 'Gerado automaticamente via generate_ml_cookies.py'
        }

        # Ensure sessions directory exists
        sessions_dir = Path('sessions')
        sessions_dir.mkdir(exist_ok=True)

        # Save to JSON file
        cookie_file = sessions_dir / 'ml_cookies.json'
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookie_data, f, indent=2, ensure_ascii=False)

        print()
        print("=" * 70)
        print("✅ COOKIES SALVOS COM SUCESSO!")
        print("=" * 70)
        print(f"📁 Arquivo: {cookie_file}")
        print(f"📅 Gerado em: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"⏰ Expira em: ~{estimated_expiry_days} dias")
        print()
        print("📋 PRÓXIMOS PASSOS:")
        print("   1. Cookies foram salvos em sessions/ml_cookies.json")
        print("   2. Use-os para autenticar conversões de links do ML")
        print("   3. Execute este script novamente quando os cookies expirarem")
        print("   4. Mantenha o arquivo em local seguro (não commit no git!)")
        print()
        print("🧪 Para testar a conversão:")
        print("   python -m pytest tests/test_affiliate/test_mercadolivre.py")
        print("=" * 70)

        await browser.close()


if __name__ == '__main__':
    asyncio.run(generate_ml_cookies())
