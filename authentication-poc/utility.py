import asyncio
import logging
from auth import Authentication
from config import AuthConfig

logging.basicConfig(level=logging.INFO)

async def main():
    config = AuthConfig(base_url=os.getenv("BASE_URL"))
    
    async with Authentication(config) as auth:
        try:
            session = await auth.get_session_token(sso=True)
            logging.info("Authentication successful!")
            return session
        except Exception as e:
            logging.error(f"Authentication failed: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(main())