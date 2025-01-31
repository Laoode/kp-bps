# Learn/pages/admin.py
import reflex as rx
from Learn.states import State
from Learn.api import generate_invitation_code


class AdminState(State):
    selected_role: str = "employee"
    new_code: str = ""
    generated_code: str = ""
    
    async def generate_code(self):
        code = await generate_invitation_code(role=self.selected_role)
        if code:
            self.generated_code = f"Kode: {code} (Role: {self.selected_role})"
        else:
            self.generated_code = "Gagal generate kode"

@rx.page(route="/admin")
def admin_dashboard():
    return rx.vstack(
        rx.heading("Admin Dashboard"),
        rx.select(
            ["employee", "admin_one", "admin_two"],  # Sesuaikan dengan enum di database
            placeholder="Pilih Role",
            on_change=AdminState.set_selected_role,
        ),
        rx.button(
            "Generate Kode Undangan",
            on_click=AdminState.generate_code
        ),
        rx.text(AdminState.generated_code),
        spacing="4"
    )
# def admin_dashboard():
#     return rx.vstack(
#         rx.heading("Admin Dashboard"),
#         rx.input(
#             placeholder="Jumlah hari berlaku",
#             type="number",
#             on_change=AdminState.set_new_code
#         ),
#         rx.button(
#             "Generate Kode Undangan",
#             on_click=AdminState.generate_code
#         ),
#         rx.text(AdminState.generated_code),
#         spacing="4"
#     )