# Learn/pages/admin.py
import reflex as rx
from Learn.states import State
from .api import generate_invitation_code


@rx.page(route="/admin")
class AdminState(State):
    new_code: str = ""
    generated_code: str = ""
    
    async def generate_code(self):
        code = await generate_invitation_code()
        if code:
            self.generated_code = code
        else:
            self.generated_code = "Gagal generate kode"

def admin_dashboard():
    return rx.vstack(
        rx.heading("Admin Dashboard"),
        rx.input(
            placeholder="Jumlah hari berlaku",
            type="number",
            on_change=AdminState.set_new_code
        ),
        rx.button(
            "Generate Kode Undangan",
            on_click=AdminState.generate_code
        ),
        rx.text(AdminState.generated_code),
        spacing="4"
    )