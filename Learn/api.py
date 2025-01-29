import jwt
import httpx
from datetime import datetime, timedelta
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

PUBLIC_KEY: str = os.environ["SUPABASE_KEY"]

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
        
        # get the data that we need ...
        access_token =  data["access_token"]
        expires_in = data["expires_in"]
        user_id = data["user"]["id"]
        user_email = data["user"]["email"]
        
        return access_token, expires_in, user_id, user_email
    
    


# second API endpoint: user registration

async def username_registration_endpoint(user_id: str, username: str):
    url = "https://acsyvbepkaxpmeupvfxl.supabase.co/rest/v1/users"
    
    headers = {
        "apikey": PUBLIC_KEY,
        "Authorization": f"Bearer {PUBLIC_KEY}",
        "Content-Type": "application/json"
    }
    
    data: dict = {
        "id": user_id,
        "username": username,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, headers=headers, json=data)
    
        return response.status_code # 201 NOT 200

async def is_usernamae_taken(username: str):
    url ="https://acsyvbepkaxpmeupvfxl.supabase.co/rest/v1/users?select=*"
    
    headers ={
        "apikey": PUBLIC_KEY,
        "Authorization": f"Bearer {PUBLIC_KEY}",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers)
        
        return any(username == user.get("username") for user in response.json())
    
    # This will  return True if the username is within the JSON object


async def is_invitation_code_valid(code: str):
    url = f"https://acsyvbepkaxpmeupvfxl.supabase.co/rest/v1/invitation_codes?code=eq.{code}&select=*"
    
    headers = {
        "apikey": PUBLIC_KEY,
        "Authorization": f"Bearer {PUBLIC_KEY}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers)
        data = response.json()
        
        if len(data) == 0:
            return False
            
        code_data = data[0]
        return (
            not code_data['is_used'] and 
            datetime.fromisoformat(code_data['expired_at']) > datetime.now()
        )


async def mark_code_used(code: str, user_id: str):
    url = f"https://acsyvbepkaxpmeupvfxl.supabase.co/rest/v1/invitation_codes?code=eq.{code}"
    
    headers = {
        "apikey": PUBLIC_KEY,
        "Authorization": f"Bearer {PUBLIC_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "is_used": True,
        "used_by": user_id,
        "used_at": datetime.now().isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        await client.patch(url=url, headers=headers, json=data)



async def user_registration_endpoint(
    username: str,
    email: str,
    password: str,
    invitation_code: str,
):
    # Validasi invitation code
    if not await is_invitation_code_valid(invitation_code):
        return "Invalid or expired invitation code!"

    url = "https://acsyvbepkaxpmeupvfxl.supabase.co/auth/v1/signup"
    
    #headers & data
    headers = {
        "apikey": PUBLIC_KEY,
        "Content-Type": "application/json",
    }
    # data = {
    #     "email": email,
    #     "password": password,
    # }
    data = {
        "email": email,
        "password": password,
        "options": {
            "data": {
                "role": "employee"  # Set role otomatis
            }
        }
    }
    try:
        async with httpx.AsyncClient() as client:
            # Registrasi user
            response = await client.post(url=url, headers=headers, json=data)
            
            if response.status_code != 200:
                return "Registration failed"
            
            user_data = response.json()
            user_id = user_data['user']['id']
            
            # Tandai kode digunakan
            await mark_code_used(invitation_code, user_id)
            
            return True
            
    except Exception as e:
        return f"Error: {str(e)}"
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(url=url, headers=headers, json=data)
        
    #     # print(response.json())
        
    #     if response.status_code == 400:
    #         msg = "Email Already Taken!"
    #         return msg
    #     else:
    #         if await is_usernamae_taken(username) is False:
    #             data = response.json()
    #             await username_registration_endpoint(data["user"]["id"], username)
                
    #             return True
    #         else:
    #             msg = "Username Already Taken!"
    #             return msg
        

# endpoint to check if JWT is valid
async def is_user_authenticated(access_token: str):
    if access_token:
        # print("Token:", access_token)  # debug token
        result: dict = jwt.decode(jwt=access_token, options={"verify_signature": False})
        # print("Decoded result:", result)  # debug hasil decode
        
        result: int = result["exp"]
        
        # we check if the exp. session time has passed
        if datetime.now() > datetime.fromtimestamp(result):
            return False
        else:
            return True
        
    else:
        return False
        
    #     return result
    # print("No token provided")  # debug jika tidak ada token
    # return None


async def generate_invitation_code(expiry_days: int = 7):
    code = str(uuid.uuid4())[:8].upper()  # Generate 8 karakter
    expired_at = datetime.now() + timedelta(days=expiry_days)
    
    url = "https://acsyvbepkaxpmeupvfxl.supabase.co/rest/v1/invitation_codes"
    
    headers = {
        "apikey": PUBLIC_KEY,
        "Authorization": f"Bearer {PUBLIC_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "code": code,
        "expired_at": expired_at.isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, headers=headers, json=data)
        if response.status_code == 201:
            return code
        return None