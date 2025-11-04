"""
Script de limpeza do diretório
Remove arquivos temporários e desnecessários
"""
import os
from pathlib import Path

print("=" * 70)
print("LIMPEZA DO DIRETORIO")
print("=" * 70)

# Arquivos a remover
files_to_remove = [
    # HTMLs temporários
    "*_temp.html",

    # Arquivos de teste antigos (PIL/Pillow)
    "create_promo_story.py",
    "create_promo_story_v2.2_backup.py",
    "create_minimal_story.py",
    "create_styled_story.py",

    # Stories antigos (PIL/Pillow)
    "story_cenario1_completo.jpg",
    "story_cenario2_com_cupom.jpg",
    "story_cenario3_preco_unico.jpg",
    "story_cenario4_cupom_sem_desconto.jpg",
    "story_carregador_apple.jpg",
    "story_teste_completo.jpg",

    # Testes de headline (intermediários)
    "story_headline_curta.jpg",
    "story_headline_media.jpg",
    "story_headline_longa.jpg",

    # Testes de emoji
    "test_emoji_alternatives.py",
    "test_emoji_alternatives.jpg",
    "test_emoji_fonts.py",
    "test_emoji_fonts.jpg",
    "test_os_emoji_fonts.py",
    "test_os_emoji_fonts.jpg",
    "emoji_comparison_guide.py",
    "emoji_comparison_guide.jpg",

    # Testes de headline antigos
    "test_headline_fix.py",
    "test_headline.jpg",

    # Documentação desatualizada
    "MINIMAL_STORY_GUIDE.md",
    "STYLED_STORY_GUIDE.md",
    "PROMO_STORY_GUIDE.md",
    "CHANGELOG.md",
    "AJUSTES_FINAIS.md",
    "AJUSTES_FINAIS_v2.2.md",

    # Scripts de postagem desatualizados
    "post_story_instagram.py",
    "exemplo_postar_story.py",
    "config_instagram.py",

    # Arquivos de teste obsoletos
    "test_flexible_scenarios.py",
    "create_placeholder_image.py",

    # HTML grande do ML
    "produto_ml.html",

    # Exemplo antigo
    "exemplo.jpeg",
]

removed_count = 0
kept_files = []

for pattern in files_to_remove:
    if "*" in pattern:
        # Padrão com wildcard
        for file in Path(".").glob(pattern):
            try:
                file.unlink()
                print(f"   OK Removido: {file}")
                removed_count += 1
            except Exception as e:
                print(f"   AVISO Erro ao remover {file}: {e}")
    else:
        # Arquivo específico
        file_path = Path(pattern)
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"   OK Removido: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"   AVISO Erro ao remover {file_path}: {e}")

print("\n" + "=" * 70)
print(f"LIMPEZA CONCLUIDA!")
print("=" * 70)
print(f"   {removed_count} arquivos removidos")
print("\nArquivos mantidos (essenciais):")
print("   • create_promo_story_html.py - Gerador principal")
print("   • post_html_story.py - Script de postagem")
print("   • test_html_scenarios.py - Testes dos 4 cenários")
print("   • test_headline_sizes.py - Testes de headline")
print("   • test_story_upload.py - Testes de upload")
print("   • test_story_completo.py - Testes completos")
print("   • placeholder_product.png - Imagem de teste")
print("   • README.md - Documentação principal")
print("   • README_POSTAGEM.md - Guia de postagem")
print("   • QUICKSTART.md - Guia rápido")
print("   • .env.example - Exemplo de configuração")
print("   • requirements.txt - Dependências")
print("\nStories finais (gerados):")
print("   • story_html_cenario1_completo.jpg")
print("   • story_html_cenario2_com_cupom.jpg")
print("   • story_html_cenario3_preco_unico.jpg")
print("   • story_html_cenario4_cupom_sem_desconto.jpg")
print("   • story_posted_instagram.jpg")
print("=" * 70)
