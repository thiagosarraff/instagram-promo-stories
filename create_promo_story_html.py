"""
Criar Instagram Story promocional usando HTML + Playwright
Abordagem mais flexível e fácil de manter que manipulação de imagens
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import base64


def create_html_story(
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
        with open(product_image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            image_ext = Path(product_image_path).suffix[1:]  # Remove o ponto
            image_base64 = f"data:image/{image_ext};base64,{image_data}"
        print(f"   OK - Imagem carregada")
    except Exception as e:
        print(f"   ERRO - Erro ao carregar imagem: {e}")
        return None

    # Calcular desconto se houver preço antigo
    discount_percent = 0
    discount_text = ""

    if price_old:
        try:
            old_value = float(price_old.replace('R$', '').replace(' ', '').replace(',', '.'))
            new_value = float(price_new.replace('R$', '').replace(' ', '').replace(',', '.'))
            discount_percent = round(((old_value - new_value) / old_value) * 100)
            discount_text = f"{discount_percent}% OFF"
            print(f"   OK - Desconto calculado: {discount_text}")
        except:
            discount_percent = 0
            discount_text = ""

    # Separar inteiros e centavos apenas do preço novo
    def format_price_with_cents(price_str):
        """Separa inteiros e centavos para estilização diferenciada"""
        if not price_str:
            return "", ""
        # Remove R$ e espaços, remove vírgula
        clean = price_str.replace('R$', '').strip()
        if ',' in clean:
            inteiros, centavos = clean.split(',')
            return f"R$ {inteiros}", centavos
        else:
            return f"R$ {clean}", ""

    price_new_int, price_new_cents = format_price_with_cents(price_new)

    # Ajustar tamanho da headline baseado no comprimento para caber em 2 linhas
    headline_length = len(headline)
    if headline_length > 45:
        headline_size = "38px"  # Headline muito longa
        headline_padding = "20px 50px"
        headline_max_width = "750px"
    elif headline_length > 35:
        headline_size = "45px"  # Headline longa
        headline_padding = "22px 55px"
        headline_max_width = "700px"
    elif headline_length > 25:
        headline_size = "55px"  # Headline média-longa
        headline_padding = "24px 60px"
        headline_max_width = "650px"
    elif headline_length > 20:
        headline_size = "60px"  # Headline média
        headline_padding = "25px 60px"
        headline_max_width = "600px"
    else:
        headline_size = "70px"  # Headline curta - fonte padrão
        headline_padding = "25px 60px"
        headline_max_width = "90%"

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
            width: 1080px;
            height: 1920px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            -webkit-font-smoothing: antialiased;
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
            margin-top: 170px;
            text-transform: uppercase;
            line-height: 1.2;
            max-width: {headline_max_width};
            width: fit-content;
            width: -moz-fit-content;
        }}

        /* Imagem do produto - âncora em 85% */
        .product-image {{
            width: 85%;
            max-width: 918px;
            height: auto;
            object-fit: contain;
            margin-top: 50px;
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
        }}

        /* Container de preços */
        .price-container {{
            width: 85%;
            margin-top: 24px;
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
        }}

        /* Esconder elementos opcionais */
        .hidden {{
            display: none !important;
        }}
    </style>
</head>
<body>
    <!-- Headline -->
    <div class="headline">{headline}</div>

    <!-- Imagem do produto -->
    <img src="{image_base64}" alt="Produto" class="product-image">

    <!-- Nome do produto -->
    <div class="product-name">{product_name}</div>

    <!-- Preços -->
    <div class="price-container">
        <!-- Preço antigo (se houver) -->
        <div class="price-old {'hidden' if not price_old else ''}">{price_old if price_old else ''}</div>

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
            <span class="coupon-label">CUPOM: </span><span class="coupon-code">{coupon_code if coupon_code else ''}</span>
        </div>
    </div>

    <!-- Botão -->
    <a href="#" class="button">
        {button_text}
    </a>
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
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={'width': 1080, 'height': 1920},
                device_scale_factor=2  # Alta qualidade
            )

            # Carregar HTML
            page.goto(f"file:///{Path(html_path).absolute()}")

            # Aguardar carregamento
            page.wait_for_load_state('networkidle')

            # Obter coordenadas reais do botão
            try:
                button = page.locator('.button').first
                box = button.bounding_box()

                if box:
                    # Coordenadas normalizadas (0-1) para compatibilidade Instagram
                    button_coords = {
                        'x': (box['x'] + box['width'] / 2) / 1080,  # Centro X
                        'y': (box['y'] + box['height'] / 2) / 1920,  # Centro Y
                        'width': box['width'] / 1080,
                        'height': box['height'] / 1920
                    }
                    print(f"   OK - Coordenadas do botão capturadas")
                    print(f"        x: {button_coords['x']:.3f}, y: {button_coords['y']:.3f}")
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

            # Capturar screenshot
            page.screenshot(
                path=output_path,
                type='jpeg',
                quality=95,
                full_page=False
            )

            browser.close()
            print(f"   OK - Screenshot capturado")

    except Exception as e:
        print(f"   ERRO - Erro ao capturar screenshot: {e}")
        return None

    print(f"SUCESSO - Story criado: {output_path}")

    return (output_path, button_coords)


def create_bulk_stories_html(
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

        result = create_html_story(**story_data)
        results.append(result)

    print(f"\n{'='*70}")
    print(f"CONCLUÍDO: {len([r for r in results if r])} sucessos, {len([r for r in results if not r])} erros")
    print(f"{'='*70}")

    return results


if __name__ == "__main__":
    # Teste básico
    print("Testando geração de story HTML...")

    story, coords = create_html_story(
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
