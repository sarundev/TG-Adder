import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # Assuming the local server is running on port 8000
        res = await client.post("http://127.0.0.1:8000/api/accounts/login/request", json={"phone": "+855716229006"})
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")

asyncio.run(test())
