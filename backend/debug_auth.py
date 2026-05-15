import asyncio
from app.db.session import async_session_factory
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest

async def main():
    try:
        async with async_session_factory() as session:
            service = AuthService(session)
            req = RegisterRequest(
                email="debug_auth@knowledgeos.ai",
                password="SecurePass123!",
                full_name="Debug Auth User"
            )
            user, tokens = await service.register(req)
            await session.commit()
            print(f"Registered user: {user.email}")
            print(f"Tokens: {tokens.access_token[:30]}...")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
