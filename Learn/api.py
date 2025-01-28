import jwt
import httpx

import os
from dotenv import load_dotenv

load_dotenv()

PUBLIC_KEY: str = os.environ("SUPABASE_KEY")

# first API endpoint: user login...
async def user_login_endpoint(email:str, password: str):
    url = "https://acsyvbepkaxpmeupvfxl.supabase.co/auth/v1/token?grant_type=password"
    
    #headers
    headers = {
        "apikey": PUBLIC_KEY,
        "Content-Type": "application/json",
    }
    
    #data
    data = {
        "email": email,
        "password": password
    }
    
    #send request...
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=url, headers=headers, json=data
        )
        
        data = response.json()
        
        print(data)