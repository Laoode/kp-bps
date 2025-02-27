import reflex as rx
from Learn.states import State
from Learn.api import generate_invitation_code
from Learn.components.navbar import navbar
from Learn.components.sidebar import sidebar


class AdminState(State):
    selected_role: str = "employee"
    new_code: str = ""
    generated_code: str = ""
    
    async def generate_code(self):
        code = await generate_invitation_code(role=self.selected_role)
        if code:
            self.generated_code = f"Code: {code} (Role: {self.selected_role})"
        else:
            self.generated_code = "Failed to generate code"


def role_selector():
    return rx.select(
        ["employee", "admin_one", "admin_two"],
        placeholder="Select Role",
        on_change=AdminState.set_selected_role,
        width="100%",
        size="3",
        color="rgb(50, 50, 50)",
        _light={
            "color": "rgb(50, 50, 50)",
            "border_color": "rgb(200, 200, 200)"
        },
        _dark={
            "color": "rgb(240, 240, 240)",
            "border_color": "rgba(255, 255, 255, 0.2)"
        }
    )


def generate_button():
    return rx.button(
        "Generate Invitation Code",
        on_click=AdminState.generate_code,
        width="100%",
        size="3",
        background_color="rgb(79, 209, 197)",
        color="white",
        font_weight="medium",
        _hover={"background_color": "rgb(64, 179, 167)"},
    )


def code_display():
    return rx.cond(
        AdminState.generated_code != "",
        rx.box(
            rx.text(
                AdminState.generated_code,
                font_size="1.1em",
                padding="4",
                border_radius="md",
                _light={
                    "color": "rgb(50, 50, 50)",
                    "background": "rgba(240, 240, 240, 0.8)",
                    "border": "1px solid rgb(220, 220, 220)",
                },
                _dark={
                    "color": "rgb(240, 240, 240)",
                    "background": "rgba(0, 0, 0, 0.2)",
                    "border": "1px solid rgba(255, 255, 255, 0.1)",
                },
                margin_top="4",
            ),
            width="100%",
        ),
    )


@rx.page(route="/admin")
def admin_dashboard():
    return rx.hstack(
        sidebar(),
        rx.box(
            rx.vstack(
                navbar(),
                rx.box(
                    rx.center(
                        rx.vstack(
                            rx.heading(
                                "Admin Dashboard",
                                size="4",
                                margin_bottom="6",
                                _light={"color": "rgb(50, 50, 50)"},
                                _dark={"color": "rgb(240, 240, 240)"},
                            ),
                            rx.card(
                                rx.vstack(
                                    rx.heading(
                                        "Generate Invitation Code",
                                        size="3",
                                        margin_bottom="4",
                                        _light={"color": "rgb(50, 50, 50)"},
                                        _dark={"color": "rgb(240, 240, 240)"},
                                    ),
                                    role_selector(),
                                    generate_button(),
                                    code_display(),
                                    width="100%",
                                    spacing="4",
                                    padding="6",
                                    align_items="start",
                                ),
                                width="100%",
                                border_radius="lg",
                                _light={
                                    "background": "white",
                                    "border": "1px solid rgb(230, 230, 230)",
                                    "box_shadow": "0 2px 8px rgba(0, 0, 0, 0.05)",
                                },
                                _dark={
                                    "background": "rgba(30, 30, 30, 0.6)",
                                    "border": "1px solid rgba(255, 255, 255, 0.1)",
                                    "box_shadow": "0 2px 8px rgba(0, 0, 0, 0.2)",
                                },
                            ),
                            width="100%",
                            max_width="600px",
                            spacing="4",
                            padding=["4", "6", "8"],
                        ),
                        width="100%",
                        padding="2em",
                    ),
                    width="100%",
                    height="calc(100vh - 80px)",
                    overflow_y="auto",
                    _light={"background": "rgb(248, 250, 252)"},
                    _dark={"background": "rgb(20, 20, 20)"},
                ),
                width="100%",
                height="100vh",
                spacing="4",
                overflow="hidden",
            ),
            width="100%",
            overflow="hidden",
        ),
        width="100%",
        height="100vh",
        spacing="0",
        overflow="hidden",
    )