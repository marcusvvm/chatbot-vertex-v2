#!/usr/bin/env python3
"""
Script CLI para gerar tokens JWT.

Uso:
    python scripts/generate_token.py --user admin --purpose admin --hours 720
    python scripts/generate_token.py --user readonly_dashboard --purpose readonly --hours 8760
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.auth import create_access_token
from app.core.config import settings


def main():
    parser = argparse.ArgumentParser(
        description="Gera tokens JWT para autenticação na API"
    )
    
    parser.add_argument(
        "--user",
        "-u",
        required=True,
        help="Identificador do usuário/sistema (ex: 'admin', 'dashboard_readonly')"
    )
    
    parser.add_argument(
        "--purpose",
        "-p",
        default="admin",
        choices=["admin", "readonly", "uploader"],
        help="Propósito do token (default: admin)"
    )
    
    parser.add_argument(
        "--hours",
        type=int,
        default=None,
        help=f"Horas até expiração (default: {settings.JWT_EXPIRATION_HOURS}h)"
    )
    
    args = parser.parse_args()
    
    # Gerar token
    token = create_access_token(
        subject=args.user,
        purpose=args.purpose,
        expiration_hours=args.hours
    )
    
    # Output
    print("\n" + "="*70)
    print("🔑 TOKEN JWT GERADO COM SUCESSO")
    print("="*70)
    print(f"\nUsuário: {args.user}")
    print(f"Propósito: {args.purpose}")
    print(f"Expiração: {args.hours or settings.JWT_EXPIRATION_HOURS} horas")
    print(f"\nToken:\n{token}")
    print("\n" + "="*70)
    print("\n📋 Como Usar:\n")
    print("1. Copie o token acima")
    print("2. Adicione ao header das requisições:")
    print(f"   Authorization: Bearer {token}\n")
    print("3. Exemplo cURL:")
    print(f'''
    curl -X POST "http://localhost:8000/api/v1/management/corpus" \\
      -H "Authorization: Bearer {token}" \\
      -H "Content-Type: application/json" \\
      -d '{{"department_name": "Teste"}}'
    ''')
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
