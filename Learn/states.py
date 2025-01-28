# app states

import reflex as rx

class State(rx.State):
    def void_event(self):...

class LoginState(State):
    email:str = ""
    password:str = ""
    
    def update_email(self, email):
        self.email = email
        
    def update_password(self, password):
        self.password = password
        
    def handle_login(self):
        print(f"Attempting login with email: {self.email}")
        if self.email and self.password:
            # Lakukan proses login
            print("Processing login...")
            # Tambahkan logika autentikasi di sini
        else:
            print("Email and password are required")