# Learn\api.py:
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
        "used_by": str(user_id),
        "used_at": datetime.now().isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        await client.patch(url=url, headers=headers, json=data)


async def resend_confirmation_email(email: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://acsyvbepkaxpmeupvfxl.supabase.co/auth/v1/recover",
                headers={
                    "apikey": PUBLIC_KEY,
                    "Content-Type": "application/json"
                },
                json={"email": email}
            )
            
            if response.status_code == 200:
                return "Email konfirmasi telah dikirim ulang! Cek inbox Anda."
            return "Gagal mengirim ulang email konfirmasi"
            
    except Exception as e:
        return f"Error: {str(e)}"

async def user_registration_endpoint(   
    email: str,
    password: str,
    invitation_code: str,
):
    try:
        # Validasi dasar sebelum request
        if len(password) < 6:
            return "Password harus minimal 6 karakter"
        # Validasi invitation code
        if not await is_invitation_code_valid(invitation_code):
            return "Invalid or expired invitation code!"

        url = "https://acsyvbepkaxpmeupvfxl.supabase.co/auth/v1/signup"
        
        #headers & data
        headers = {
            "apikey": PUBLIC_KEY,
            "Content-Type": "application/json",
        }
        data = {
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "role": "employee"  # Set role otomatis
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            # Registrasi user
            response = await client.post(url=url, headers=headers, json=data)
            
            if response.status_code not in [200, 201]:
                return f"Registration failed. Status: {response.status_code}, Error: {response.text}"
                        
            user_data = response.json()
            user_id = user_data['user']['id']
            
            # Update role berdasarkan kode undangan
            await client.patch(
                url=f"https://acsyvbepkaxpmeupvfxl.supabase.co/rest/v1/profiles?id=eq.{user_id}",
                headers=headers,
                json={"role": "employee"}
            )
            
            # Tandai kode digunakan
            await mark_code_used(invitation_code, user_id)
            
            return True
        
    except httpx.HTTPStatusError as e:
        error_messages = {
            400: "Email sudah terdaftar atau format tidak valid",
            401: "Autentikasi gagal",
            422: "Data tidak valid"
        }
        return error_messages.get(e.response.status_code, f"Error: {str(e)}")
    
    except Exception as e:
        return f"Error: {str(e)}"

async def get_user_role(user_id: str):
    url = f"https://acsyvbepkaxpmeupvfxl.supabase.co/rest/v1/profiles?id=eq.{user_id}"
    
    headers = {
        "apikey": PUBLIC_KEY,
        "Authorization": f"Bearer {PUBLIC_KEY}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url=url, headers=headers)
        return response.json()[0]['role']

# endpoint to check if JWT is valid
async def is_user_authenticated(access_token: str):
    if access_token:
        result: dict = jwt.decode(jwt=access_token, options={"verify_signature": False})
        result: int = result["exp"]
        
        # we check if the exp. session time has passed
        if datetime.now() > datetime.fromtimestamp(result):
            return False
        else:
            return True
        
    else:
        return False
        


async def generate_invitation_code(role: str, expiry_days: int = 7):
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
        "expired_at": expired_at.isoformat(),
        "role": role
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url=url, headers=headers, json=data)
        if response.status_code == 201:
            return code
        return None