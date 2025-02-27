import reflex as rx
from datetime import datetime, timedelta
import json
from .api import user_login_endpoint, user_registration_endpoint, is_user_authenticated

class State(rx.State):
    def void_event(self):
        pass

class LoginState(State):
    email: str = ""
    password: str = ""
    
    def update_email(self, email):
        self.email = email
        
    def update_password(self, password):
        self.password = password
        
    def handle_login(self):
        print(f"Attempting login with email: {self.email}")
        if self.email and self.password:
            print("Processing login...")
        else:
            print("Email and password are required")

class RegisterState(State):
    email: str = ""
    password: str = ""
    invitation_code: str = ""
    
    def update_email(self, email):
        self.email = email
        
    def update_password(self, password):
        self.password = password

    def update_invitation_code(self, code: str):
        self.invitation_code = code

class Registration(RegisterState):
    error_message: str = ""
    success_message: str = ""
    
    async def resend_confirmation(self):
        result = await resend_confirmation_email(self.email)
        if "berhasil" in result:
            self.success_message = result
        else:
            self.error_message = result
    
    async def user_registration(self):
        self.error_message = ""
        self.success_message = ""
        
        result = await user_registration_endpoint(
            self.email, 
            self.password,
            self.invitation_code
        )
        
        if result is True:
            self.success_message = "Registrasi berhasil! Silakan cek email Anda untuk konfirmasi"
            return rx.redirect("/login")
        else:
            self.error_message = result
            return

class Authentication(LoginState):
    access_token: str = ""
    user_id: str = ""
    user_email: str = ""
    session_exp: int = 0 
    
    user_session: str = rx.LocalStorage(
        name="user_session",
    )
    
    async def user_login(self):
        # Get authentication data from endpoint
        auth_data = await user_login_endpoint(self.email, self.password)
        print(f"Received auth_data: {auth_data}") 
        
        if auth_data:
            self.access_token, expires_in, self.user_id, self.user_email = auth_data
            self.session_exp = expires_in 
            
            session_data = {
                "user_id": self.user_id,
                "user_email": self.user_email,
                "access_token": self.access_token,
                "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            }
            self.user_session = json.dumps(session_data)  # ✅ Simpan sebagai string
            
            # testing the validation...
            # we can test this by using the user thats already logged in and user will create... 
            if await is_user_authenticated(self.access_token) is True:
                print("Valid Session")
                return rx.redirect("/")
            else:
                print("Session Expired")
                return rx.redirect("/login") 
        
        return rx.window_alert("Login failed. Please check your credentials.")
    def check_auth(self):
        """Jika pengguna sudah terautentikasi, redirect ke halaman utama; jika belum, biarkan tetap di halaman login/register."""
        if self.user_session:
            try:
                session_data = json.loads(self.user_session)
                expires_at = datetime.fromisoformat(session_data["expires_at"])
                if datetime.now() < expires_at:
                    # Jika session valid, redirect ke halaman utama
                    return rx.redirect("/")
            except Exception as e:
                print("Error saat parsing session:", e)
                pass

    def require_auth(self):
        """Memastikan bahwa pengguna harus login untuk mengakses halaman tertentu.
        Jika tidak ada session atau session sudah kedaluwarsa, redirect ke /login."""
        if self.user_session:
            try:
                session_data = json.loads(self.user_session)
                expires_at = datetime.fromisoformat(session_data["expires_at"])
                if datetime.now() > expires_at:
                    return rx.redirect("/login")
            except Exception as e:
                print("Error saat parsing session:", e)
                return rx.redirect("/login")
        else:
            return rx.redirect("/login")
    def handle_logout(self):
        """Handle logout"""
        self.user_session = ""
        self.access_token = ""
        self.user_id = ""
        self.user_email = ""
        return rx.redirect("/login")