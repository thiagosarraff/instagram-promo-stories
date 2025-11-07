"""
Criar Instagram Story promocional usando HTML + Playwright
Abordagem mais flexível e fácil de manter que manipulação de imagens
"""
from playwright.async_api import async_playwright
from pathlib import Path
import base64
import requests
from io import BytesIO


async def create_html_story(
    product_image_path: str,
    headline: str,
    product_name: str,
    price_new: str,
    price_old: str = None,
    coupon_code: str = None,
    source: str = None,
    output_path: str = "story_promo_html.jpg"
) -> tuple:
    """
    Cria story promocional usando HTML/CSS e captura screenshot com Playwright

    Args:
        product_image_path: Caminho para imagem do produto
        headline: Título principal (aparece no topo)
        product_name: Nome do produto
        price_new: Preço atual (obrigatório)
        price_old: Preço antigo (opcional, se fornecido mostra desconto)
        coupon_code: Código do cupom (opcional)
        source: Origem da oferta (mercadolivre, amazon, magalu, etc.) - usado para gerar o texto do botão
        output_path: Caminho para salvar a imagem final

    Returns:
        tuple: (caminho_da_imagem, coordenadas_do_botao)
    """

    print(f"\nCriando story HTML...")

    # Gerar texto do botão baseado na origem
    source_mapping = {
        "mercadolivre": "🔗 LINK MERCADO LIVRE",
        "amazon": "🔗 LINK AMAZON",
        "magalu": "🔗 LINK MAGALU",
        "americanas": "🔗 LINK AMERICANAS",
        "shopee": "🔗 LINK SHOPEE",
        "aliexpress": "🔗 LINK ALIEXPRESS",
        "casasbahia": "🔗 LINK CASAS BAHIA",
        "extra": "🔗 LINK EXTRA",
        "pontofrio": "🔗 LINK PONTO FRIO",
        "submarino": "🔗 LINK SUBMARINO"
    }

    # Se source foi fornecido, usar mapeamento, senão usar padrão
    if source:
        button_text = source_mapping.get(source.lower(), f"🔗 LINK {source.upper()}")
    else:
        button_text = "🔗 LINK DO PRODUTO"

    # Converter imagem para base64
    try:
        # Verificar se é URL ou caminho local
        if product_image_path.startswith(('http://', 'https://')):
            # Baixar imagem da URL
            print(f"   INFO - Baixando imagem de: {product_image_path}")
            response = requests.get(product_image_path, timeout=10)
            response.raise_for_status()
            image_bytes = response.content

            # Detectar extensão pelo content-type ou pela URL
            content_type = response.headers.get('content-type', '')
            if 'png' in content_type:
                image_ext = 'png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                image_ext = 'jpeg'
            elif 'webp' in content_type:
                image_ext = 'webp'
            else:
                # Fallback: tentar extrair da URL
                image_ext = Path(product_image_path).suffix[1:] or 'jpeg'

            image_data = base64.b64encode(image_bytes).decode('utf-8')
            print(f"   OK - Imagem baixada ({len(image_bytes)} bytes)")
        else:
            # Abrir arquivo local
            with open(product_image_path, 'rb') as f:
                image_bytes = f.read()
                image_data = base64.b64encode(image_bytes).decode('utf-8')
                image_ext = Path(product_image_path).suffix[1:]
            print(f"   OK - Imagem carregada")

        image_base64 = f"data:image/{image_ext};base64,{image_data}"

    except requests.RequestException as e:
        print(f"   ERRO - Falha ao baixar imagem: {e}")
        return None
    except Exception as e:
        print(f"   ERRO - Erro ao carregar imagem: {e}")
        return None

    # Função auxiliar para normalizar preços (aceita ponto ou vírgula)
    def normalize_price(price_str):
        """
        Normaliza string de preço para formato brasileiro com vírgula
        Aceita: "R$ 35,41", "R$ 35.41", "35,41", "35.41", "35"
        Retorna: "R$ 35,41"
        """
        if not price_str:
            return ""

        # Remove R$ e espaços
        clean = price_str.replace('R$', '').replace(' ', '').strip()

        # Se não tem separador decimal, adiciona ,00
        if ',' not in clean and '.' not in clean:
            return f"R$ {clean},00"

        # Substitui ponto por vírgula (normaliza para formato BR)
        if '.' in clean:
            # Verifica se é separador decimal (último ponto na string)
            if clean.count('.') == 1 and len(clean.split('.')[1]) <= 2:
                clean = clean.replace('.', ',')

        # Garante 2 casas decimais
        if ',' in clean:
            partes = clean.split(',')
            inteiros = partes[0]
            decimais = partes[1] if len(partes) > 1 else '00'
            # Preenche ou trunca para 2 dígitos
            decimais = (decimais + '00')[:2]
            return f"R$ {inteiros},{decimais}"

        return f"R$ {clean},00"

    # Normalizar preços
    price_new_normalized = normalize_price(price_new)
    price_old_normalized = normalize_price(price_old) if price_old else None

    # Calcular desconto se houver preço antigo
    discount_percent = 0
    discount_text = ""

    if price_old_normalized:
        try:
            old_value = float(price_old_normalized.replace('R$', '').replace(' ', '').replace(',', '.'))
            new_value = float(price_new_normalized.replace('R$', '').replace(' ', '').replace(',', '.'))
            discount_percent = round(((old_value - new_value) / old_value) * 100)
            discount_text = f"{discount_percent}% OFF"
            print(f"   OK - Desconto calculado: {discount_text}")
        except Exception as e:
            print(f"   ⚠️  Erro ao calcular desconto: {e}")
            discount_percent = 0
            discount_text = ""

    # Separar inteiros e centavos apenas do preço novo
    def format_price_with_cents(price_str):
        """Separa inteiros e centavos para estilização diferenciada com separador de milhar"""
        if not price_str:
            return "", ""
        # Remove R$ e espaços
        clean = price_str.replace('R$', '').strip()
        if ',' in clean:
            inteiros, centavos = clean.split(',')
            # Adicionar separador de milhar se ≥ 1000
            inteiros_num = int(inteiros)
            if inteiros_num >= 1000:
                inteiros = f"{inteiros_num:,}".replace(',', '.')
            return f"R$ {inteiros}", centavos
        else:
            # Adicionar separador de milhar se ≥ 1000
            inteiros_num = int(clean)
            if inteiros_num >= 1000:
                clean = f"{inteiros_num:,}".replace(',', '.')
            return f"R$ {clean}", "00"

    price_new_int, price_new_cents = format_price_with_cents(price_new_normalized)

    # Ajustar tamanho da headline baseado no comprimento para caber em 2 linhas
    # Todos os tamanhos aumentados em 20%
    # Margem superior ajustável para manter proporção 9:16 (1080x1920px)
    headline_length = len(headline)
    if headline_length > 45:
        headline_size = "46px"  # Headline muito longa (38px * 1.2)
        headline_padding = "20px 50px"
        headline_max_width = "750px"
        headline_margin_top = "120px"  # Reduzida para compensar texto maior
    elif headline_length > 35:
        headline_size = "54px"  # Headline longa (45px * 1.2)
        headline_padding = "22px 55px"
        headline_max_width = "700px"
        headline_margin_top = "130px"  # Reduzida para compensar texto maior
    elif headline_length > 25:
        headline_size = "66px"  # Headline média-longa (55px * 1.2)
        headline_padding = "24px 60px"
        headline_max_width = "650px"
        headline_margin_top = "140px"  # Reduzida para compensar texto maior
    elif headline_length > 20:
        headline_size = "72px"  # Headline média (60px * 1.2)
        headline_padding = "25px 60px"
        headline_max_width = "600px"
        headline_margin_top = "150px"  # Reduzida para compensar texto maior
    else:
        headline_size = "84px"  # Headline curta - fonte padrão (70px * 1.2)
        headline_padding = "25px 60px"
        headline_max_width = "90%"
        headline_margin_top = "170px"  # Margem padrão

    # Template HTML com CSS inline
    html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Story</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@400;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: Proxima Nova, -apple-system, Roboto, Arial, sans-serif;
            background: white;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
        }}

        /* Container principal com dimensões fixas 9:16 */
        .story-container {{
            width: 1080px;
            height: 1920px;
            background: white;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow: hidden;
            position: relative;
        }}

        /* Espaçador superior flexível */
        .top-spacer {{
            flex: 0 1 {headline_margin_top};
            min-height: 80px;
        }}

        /* Headline - largura ajustada ao conteúdo */
        .headline {{
            background: #DC143C;
            color: white;
            font-size: {headline_size};
            font-weight: bold;
            text-align: center;
            padding: {headline_padding};
            border-radius: 15px;
            text-transform: uppercase;
            line-height: 1.2;
            max-width: {headline_max_width};
            width: fit-content;
            width: -moz-fit-content;
            flex-shrink: 0;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.25), 0 4px 8px rgba(0, 0, 0, 0.15);
            position: relative;
            z-index: 10;
        }}

        /* Espaçador entre headline e imagem - flexível */
        .image-spacer {{
            flex: 0 1 50px;
            min-height: -30px;
        }}

        /* Imagem do produto - âncora em 85% com altura máxima */
        .product-image {{
            width: 85%;
            max-width: 918px;
            max-height: 800px;
            height: auto;
            object-fit: contain;
            flex-shrink: 0;
            position: relative;
            z-index: 5;
        }}

        /* Nome do produto - sem negrito */
        .product-name {{
            width: 85%;
            font-size: 42px;
            color: rgba(0, 0, 0, 0.9);
            font-weight: 400;
            line-height: 1.25;
            word-break: break-word;
            margin-top: 32px;
            text-align: left;
            flex-shrink: 0;
        }}

        /* Container de preços */
        .price-container {{
            width: 85%;
            margin-top: 24px;
            flex-shrink: 0;
        }}

        /* Preço antigo - inteiros */
        .price-old {{
            font-size: 45px;
            font-weight: 400;
            color: rgba(0, 0, 0, 0.55);
            text-decoration: line-through;
            text-decoration-thickness: 2px;
            letter-spacing: normal;
            line-height: 1;
            margin-bottom: 8px;
        }}

        /* Preço antigo - centavos menores */
        .price-old-cents {{
            font-size: 27px;
            vertical-align: super;
        }}

        /* Container preço novo + desconto */
        .price-new-container {{
            display: flex;
            align-items: baseline;
            gap: 20px;
            margin-top: 8px;
        }}

        /* Preço novo - inteiros */
        .price-new {{
            font-size: 95px;
            font-weight: 300;
            color: rgba(0, 0, 0, 0.9);
            letter-spacing: normal;
            line-height: 1;
        }}

        /* Preço novo - centavos menores */
        .price-new-cents {{
            font-size: 57px;
            vertical-align: super;
        }}

        /* Desconto - maior */
        .discount {{
            font-size: 50px;
            font-weight: 400;
            color: #00a650;
            line-height: 1;
        }}

        /* Container do cupom - mesma largura dos outros elementos */
        .coupon-container {{
            width: 85%;
            margin-top: 32px;
            flex-shrink: 0;
        }}

        /* Cupom - largura automática, alinhado à esquerda */
        .coupon {{
            display: inline-block;
            background-color: rgba(65, 137, 230, 0.2);
            color: #3483fa;
            padding: 14px 20px;
            border-radius: 4px;
            font-size: 36px;
            font-weight: 600;
            line-height: 1.2;
        }}

        .coupon-emoji {{
            display: none;
        }}

        .coupon-label {{
            font-weight: 600;
            color: #3483fa;
        }}

        .coupon-code {{
            font-weight: 600;
            color: #3483fa;
        }}

        /* Botão - fonte Prompt condensed */
        .button {{
            margin-top: 45px;
            margin-bottom: 60px;
            background: #1E90FF;
            color: white;
            font-family: 'Prompt', 'Arial Narrow', 'Arial Condensed', Arial, sans-serif;
            font-size: 50px;
            font-weight: bold;
            padding: 30px 70px;
            border-radius: 25px;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 6px 6px 0 #C8C8C8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            flex-shrink: 0;
        }}

        /* Esconder elementos opcionais */
        .hidden {{
            display: none !important;
        }}
    </style>
</head>
<body>
    <div class="story-container">
        <!-- Espaçador superior flexível -->
        <div class="top-spacer"></div>

        <!-- Headline -->
        <div class="headline">{headline}</div>

        <!-- Espaçador flexível entre headline e imagem -->
        <div class="image-spacer"></div>

        <!-- Imagem do produto -->
        <img src="{image_base64}" alt="Produto" class="product-image">

        <!-- Nome do produto -->
        <div class="product-name">{product_name}</div>

        <!-- Preços -->
        <div class="price-container">
            <!-- Preço antigo (se houver) -->
            <div class="price-old {'hidden' if not price_old_normalized else ''}">{price_old_normalized if price_old_normalized else ''}</div>

            <!-- Preço novo + Desconto -->
            <div class="price-new-container">
                <div class="price-new">
                    {price_new_int}<span class="price-new-cents">{price_new_cents}</span>
                </div>
                <div class="discount {'hidden' if not discount_text else ''}">{discount_text}</div>
            </div>
        </div>

        <!-- Cupom (se houver) -->
        <div class="coupon-container {'hidden' if not coupon_code else ''}">
            <div class="coupon">
                <span class="coupon-label">USE O CUPOM: </span><span class="coupon-code">{coupon_code if coupon_code else ''}</span>
            </div>
        </div>

        <!-- Botão -->
        <a href="#" class="button">
            {button_text}
        </a>
    </div>
</body>
</html>
"""

    # Salvar HTML temporário
    html_path = Path(output_path).stem + "_temp.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"   OK - HTML gerado: {html_path}")

    # Capturar screenshot com Playwright
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                viewport={'width': 1080, 'height': 1920},
                device_scale_factor=2  # Alta qualidade
            )

            # Carregar HTML
            await page.goto(f"file:///{Path(html_path).absolute()}")

            # Aguardar carregamento
            await page.wait_for_load_state('networkidle')

            # Obter coordenadas reais do botão
            try:
                button = page.locator('.button').first
                box = await button.bounding_box()

                if box:
                    # Coordenadas normalizadas (0-1) para compatibilidade Instagram
                    # Usando o centro do botão como referência
                    button_coords = {
                        'x': (box['x'] + box['width'] / 2) / 1080,  # Centro X
                        'y': (box['y'] + box['height'] / 2) / 1920,  # Centro Y
                        'width': box['width'] / 1080,
                        'height': box['height'] / 1920
                    }
                    print(f"   OK - Coordenadas do botão capturadas")
                    print(f"        x: {button_coords['x']:.3f}, y: {button_coords['y']:.3f}")
                    print(f"        width: {button_coords['width']:.3f}, height: {button_coords['height']:.3f}")
                else:
                    # Fallback se não encontrar o botão
                    button_coords = {
                        'x': 0.5,
                        'y': 0.85,
                        'width': 0.6,
                        'height': 0.08
                    }
                    print(f"   ⚠️  Usando coordenadas estimadas")
            except:
                button_coords = {
                    'x': 0.5,
                    'y': 0.85,
                    'width': 0.6,
                    'height': 0.08
                }
                print(f"   ⚠️  Usando coordenadas estimadas")

            # Capturar screenshot com proporção 9:16 fixa (1080x1920px)
            await page.screenshot(
                path=output_path,
                type='jpeg',
                quality=95,
                full_page=False,
                clip={'x': 0, 'y': 0, 'width': 1080, 'height': 1920}
            )

            await browser.close()
            print(f"   OK - Screenshot capturado")

    except Exception as e:
        print(f"   ERRO - Erro ao capturar screenshot: {e}")
        return None

    print(f"SUCESSO - Story criado: {output_path}")

    return (output_path, button_coords)


async def create_bulk_stories_html(
    stories_data: list,
    options: dict = None
) -> list:
    """
    Cria múltiplos stories de uma vez

    Args:
        stories_data: Lista de dicionários com dados de cada story
        options: Opções de processamento (batch_size, concurrency, etc)

    Returns:
        list: Lista de resultados [(caminho, coordenadas), ...]
    """
    results = []

    print(f"\n{'='*70}")
    print(f"CRIANDO {len(stories_data)} STORIES EM LOTE")
    print(f"{'='*70}")

    for i, story_data in enumerate(stories_data, 1):
        print(f"\n[{i}/{len(stories_data)}] Processando...")

        result = await create_html_story(**story_data)
        results.append(result)

    print(f"\n{'='*70}")
    print(f"CONCLUÍDO: {len([r for r in results if r])} sucessos, {len([r for r in results if not r])} erros")
    print(f"{'='*70}")

    return results


if __name__ == "__main__":
    import asyncio

    # Teste básico
    print("Testando geração de story HTML...")

    async def test():
        story, coords = await create_html_story(
            product_image_path="placeholder_product.png",
            headline="OFERTA IMPERDÍVEL",
            product_name="Carregador Fonte Apple iPad iPhone Turbo Original USB-C 20W",
            price_new="R$ 35,41",
            price_old="R$ 48,50",
            coupon_code="PROMO10",
            source="mercadolivre",  # Agora com origem da oferta
            output_path="story_html_test.jpg"
        )

        if story:
            print(f"\nStory gerado com sucesso: {story}")
            print(f"Coordenadas do botão: {coords}")

    asyncio.run(test())
