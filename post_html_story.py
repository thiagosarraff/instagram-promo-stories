"""
Postar Stories HTML no Instagram
Integra create_promo_story_html com test_story_upload
"""

import os
from pathlib import Path
from instagrapi import Client
from instagrapi.types import StoryLink
from dotenv import load_dotenv
from create_promo_story_html import create_html_story

# Carregar variáveis de ambiente
load_dotenv()


async def post_html_story_to_instagram(
    username: str,
    password: str,
    product_image_path: str,
    headline: str,
    product_name: str,
    price_new: str,
    price_old: str = None,
    coupon_code: str = None,
    source: str = None,
    product_url: str = None,
    caption: str = None,
    output_path: str = "story_to_post.jpg"
) -> tuple:
    """
    Cria story HTML e posta no Instagram em uma operação completa

    Args:
        username: Username do Instagram
        password: Senha do Instagram
        product_image_path: Caminho para imagem do produto
        headline: Título principal do story
        product_name: Nome do produto
        price_new: Preço atual (ex: "R$ 35,41")
        price_old: Preço antigo/riscado (opcional)
        coupon_code: Código do cupom (opcional)
        source: Origem da oferta (mercadolivre, amazon, magalu, etc.) - usado no texto do botão
        product_url: URL do produto para link swipe-up (opcional)
        caption: Legenda do story (opcional)
        output_path: Caminho para salvar a imagem gerada

    Returns:
        tuple: (success: bool, story_id: str) - True se criou e postou com sucesso, story ID se disponível
    """

    print("=" * 70)
    print("🚀 CRIAR E POSTAR STORY PROMOCIONAL NO INSTAGRAM")
    print("=" * 70)

    # ETAPA 1: Criar story HTML
    print("\n📝 ETAPA 1: Criando story HTML...")
    story_path, coords = await create_html_story(
        product_image_path=product_image_path,
        headline=headline,
        product_name=product_name,
        price_new=price_new,
        price_old=price_old,
        coupon_code=coupon_code,
        source=source,
        output_path=output_path
    )

    if not story_path:
        print("\n❌ FALHA: Não foi possível criar o story")
        return (False, None)

    print(f"\n✅ Story criado: {story_path}")

    # ETAPA 2: Login no Instagram com persistência de sessão
    print(f"\n🔐 ETAPA 2: Fazendo login como @{username}...")
    cl = Client()

    # Definir caminho para salvar a sessão (usar pasta montada pelo Docker)
    session_dir = os.getenv('INSTAGRAM_SESSION_PATH', '/app/session')
    os.makedirs(session_dir, exist_ok=True)
    session_file = os.path.join(session_dir, f"session_{username}.json")

    try:
        # Tentar carregar sessão existente
        if os.path.exists(session_file):
            print("   📂 Carregando sessão salva...")
            cl.load_settings(session_file)
            cl.login(username, password)
            print("✅ Login bem-sucedido usando sessão salva!")
        else:
            print("   🔑 Primeiro login - salvando sessão para reuso...")
            cl.login(username, password)
            cl.dump_settings(session_file)
            print("✅ Login bem-sucedido e sessão salva!")
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        print("\n💡 SOLUÇÃO NECESSÁRIA:")
        print("   1. Execute o login manualmente no seu computador local primeiro")
        print("   2. Isso gerará o arquivo de sessão")
        print("   3. Copie o arquivo de sessão para o servidor Docker")
        print("   4. O Instagram pediu verificação porque é um novo dispositivo")
        return (False, None)

    # ETAPA 3: Postar story
    print(f"\n📤 ETAPA 3: Postando story no Instagram...")

    try:
        # Preparar caption
        if not caption:
            caption = f"🔥 {headline}"
            if coupon_code:
                caption += f"\n🎟️ Cupom: {coupon_code}"

        # Preparar link se fornecido (com coordenadas do botão)
        links = None
        if product_url:
            # Usar as coordenadas reais retornadas pela função
            links = [StoryLink(
                webUri=product_url,
                x=coords['x'],
                y=coords['y'],
                width=coords['width'],
                height=coords['height']
            )]
            print(f"   🔗 Link adicionado: {product_url}")
            print(f"   📍 Posição: x={coords['x']:.3f}, y={coords['y']:.3f}")

        # Upload do story
        story = cl.photo_upload_to_story(
            story_path,
            caption,
            links=links
        )

        print(f"\n✅ SUCESSO! Story publicado!")
        print(f"   📱 ID do story: {story.pk}")
        print(f"   👤 Usuário: @{username}")
        if product_url:
            print(f"   🔗 Link: {product_url}")

        print("\n" + "=" * 70)
        print("✨ STORY PUBLICADO COM SUCESSO NO INSTAGRAM!")
        print("=" * 70)
        print(f"\n📱 Verifique seu Instagram para ver o story publicado!")

        return (True, str(story.pk))

    except Exception as e:
        print(f"\n❌ ERRO ao postar story: {e}")
        return (False, None)


async def main():
    """
    Exemplo de uso - Posta o cenário 2 (completo com cupom)
    """
    print("=" * 70)
    print("📋 EXEMPLO: POSTAR STORY PROMOCIONAL")
    print("=" * 70)

    # Carregar credenciais do .env
    USERNAME = os.getenv('INSTAGRAM_USERNAME')
    PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
    PRODUCT_URL = os.getenv('PRODUCT_URL', 'https://www.mercadolivre.com.br')

    # Validação
    if not USERNAME or not PASSWORD:
        print("\n❌ ERRO: Configure as variáveis de ambiente!")
        print("\nCrie um arquivo .env com:")
        print("INSTAGRAM_USERNAME=seu_usuario")
        print("INSTAGRAM_PASSWORD=sua_senha")
        print("PRODUCT_URL=https://produto.mercadolivre.com.br/MLB-xxxxx")
        return

    # Confirmar postagem
    print(f"\n⚠️  Você está prestes a postar um story em @{USERNAME}")
    print("\nDetalhes do story:")
    print("  • Headline: OFERTA IMPERDÍVEL")
    print("  • Produto: Carregador Apple USB-C 20W")
    print("  • Preço: DE R$ 48,50 | POR R$ 35,41")
    print("  • Cupom: PROMO10")
    print(f"  • Link: {PRODUCT_URL}")

    confirm = input("\n✅ Confirma a postagem? (s/N): ").strip().lower()

    if confirm != 's':
        print("\n❌ Postagem cancelada pelo usuário")
        return

    # Postar story
    success = await post_html_story_to_instagram(
        username=USERNAME,
        password=PASSWORD,
        product_image_path="placeholder_product.png",
        headline="OFERTA IMPERDÍVEL",
        product_name="Carregador Fonte Apple iPad iPhone Turbo Original USB-C 20W",
        price_new="R$ 35,41",
        price_old="R$ 48,50",
        coupon_code="PROMO10",
        source="mercadolivre",  # Agora com origem da oferta
        product_url=PRODUCT_URL,
        output_path="story_posted_instagram.jpg"
    )

    if success:
        print("\n🎉 Tudo pronto! Story publicado com sucesso!")
    else:
        print("\n😞 Algo deu errado. Verifique os erros acima.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
