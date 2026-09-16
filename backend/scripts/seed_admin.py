"""Crea el usuario administrador inicial si no existe.

Uso: python -m scripts.seed_admin
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import hash_password  # noqa: E402
from app.database import AsyncSessionLocal  # noqa: E402
from app.repositories.usuario_repository import UsuarioRepository  # noqa: E402

ADMIN_EMAIL = os.environ.get("SEED_ADMIN_EMAIL", "admin@escuela.com")
ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "admin123")


async def main():
    async with AsyncSessionLocal() as db:
        repo = UsuarioRepository(db)
        existente = await repo.get_by_email(ADMIN_EMAIL)
        if existente:
            print(f"El admin '{ADMIN_EMAIL}' ya existe.")
            return

        await repo.create(
            {
                "email": ADMIN_EMAIL,
                "nombre": "Administrador",
                "rol": "admin",
                "password_hash": hash_password(ADMIN_PASSWORD),
                "activo": True,
            }
        )
        await db.commit()
        print(f"Admin creado: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
