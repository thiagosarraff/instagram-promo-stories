"""
Script para gerar arquivo de sessão do Instagram
Execute localmente no seu computador para criar o arquivo de sessão
"""

import os
from instagrapi import Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def generate_session():
    """Gera arquivo de sessão para uso no servidor"""

    print("="*70)
    print("🔐 GERADOR DE SESSÃO DO INSTAGRAM")
    print("="*70)

    # Obter credenciais
    username = os.getenv('INSTAGRAM_USERNAME')
    password = os.getenv('INSTAGRAM_PASSWORD')

    if not username or not password:
        print("\n❌ ERRO: Configure o arquivo .env com:")
        print("INSTAGRAM_USERNAME=seu_usuario")
        print("INSTAGRAM_PASSWORD=sua_senha")
        return

    print(f"\n👤 Usuário: {username}")
    print("🔑 Tentando fazer login...")

    cl = Client()
    session_file = f"session_{username}.json"

    try:
        # Fazer login
        cl.login(username, password)
        print("✅ Login bem-sucedido!")

        # Salvar sessão
        cl.dump_settings(session_file)
        print(f"\n✅ Sessão salva em: {session_file}")

        print("\n📋 PRÓXIMOS PASSOS:")
        print(f"   1. Copie o arquivo '{session_file}' para o servidor")
        print(f"   2. No servidor, coloque o arquivo na pasta raiz do projeto")
        print(f"   3. O Docker montará este arquivo automaticamente")
        print(f"\n💡 Comando para copiar (exemplo):")
        print(f"   scp {session_file} usuario@servidor:~/instagram-promo-stories/")

    except Exception as e:
        print(f"\n❌ ERRO no login: {e}")
        print("\n💡 Se o Instagram pedir verificação:")
        print("   1. Verifique seu email ou SMS")
        print("   2. Digite o código quando solicitado")
        print("   3. Execute este script novamente")

if __name__ == "__main__":
    generate_session()
