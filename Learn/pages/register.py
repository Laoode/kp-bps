# Learn/pages/register.py
import reflex as rx
from Learn.states import RegisterState, Registration
from Learn.api import resend_confirmation_email
from Learn.styles import input_error_style, success_message_style

def password_requirements():
    return rx.box(
        rx.text("The password must contain:", size="1", color="gray", spacing="1",),
        rx.spacer(height="0.5em"),
        rx.vstack(
            rx.hstack(
                rx.icon(tag="circle-check", size=12, color="green.500"),
                rx.text("At least 6 characters", size="1")
            ),
            rx.hstack(
                rx.icon(tag="circle-check", size=12, color="green.500"),
                rx.text("At least 1 number", size="1")
            ),
            spacing="1",
        ),
        padding_left="1em"
    )

@rx.page(route="/register")
def register_default_icons() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                # Error/Success Messages
                rx.cond(
                    Registration.error_message != "",
                    rx.text(
                        Registration.error_message,
                        color="red.600",
                        bg="red.50",
                        padding="2",
                        border_radius="md",
                        width="100%",
                        text_align="center"
                    )
                ),
                rx.cond(
                    Registration.success_message != "",
                    rx.box(
                        rx.vstack(
                            rx.text(
                                Registration.success_message,
                                color="green.600",
                                text_align="center"
                            ),
                            rx.link(
                                "Kirim ulang email konfirmasi",
                                on_click=Registration.resend_confirmation,
                                color="blue.600",
                                hover={"text_decoration": "underline"},
                                size="1"
                            ),
                            spacing="2",
                            align_items="center"
                        ),
                        bg="green.50",
                        padding="3",
                        border_radius="md",
                        width="100%"
                    )
                ),
                
                # Form Content
                rx.center(
                    rx.image(
                        src="/logo.png",
                        width="2.5em",
                        height="auto",
                        border_radius="25%",
                    ),
                    rx.heading(
                        "Sign up to create your account",
                        size="6",
                        margin_top="2",
                        text_align="center"
                    ),
                    direction="column",
                    spacing="4",
                    width="100%"
                ),
                
                # Email Input
                rx.vstack(
                    rx.text(
                        "Email address",
                        size="3",
                        weight="medium",
                        text_align="left",
                        width="100%",
                    ),
                    rx.input(
                        rx.input.slot(rx.icon("mail")),
                        placeholder="user@gmail.com",
                        type="email",
                        size="3",
                        width="100%",
                        value=RegisterState.email, 
                        on_change=RegisterState.update_email 
                    ),
                    spacing="2",
                    width="100%",
                ),
                
                # Password Input
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            "Password",
                            size="3",
                            weight="medium",
                        ),
                        justify="between",
                        width="100%",
                    ),
                    rx.input(
                        rx.input.slot(rx.icon("lock")),
                        placeholder="Enter your password",
                        type="password",
                        size="3",
                        width="100%",
                        value=RegisterState.password, 
                        on_change=RegisterState.update_password ,
                        min_length=6,
                    ),
                    password_requirements(),
                    spacing="2",
                    width="100%",
                ),
                
                #Invitation Code
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            "Invitation Code",
                            size="3",
                            weight="medium",
                        ),
                        justify="between",
                        width="100%",
                    ),
                    rx.input(
                        rx.input.slot(rx.icon("key-round")),
                        placeholder="Enter invitation code",
                        type="text",
                        size="3",
                        width="100%",
                        value=RegisterState.invitation_code, 
                        on_change=RegisterState.update_invitation_code 
                    ),
                    spacing="2",
                    width="100%",
                ),
                
                # Submit Button
                rx.button(
                    "Sign up",
                    size="3",
                    width="100%",
                    on_click=Registration.user_registration,
                ),
                
                # Login Link
                rx.center(
                    rx.text("Already have an account?", size="3"),
                    rx.link("Sign in", href="/", size="3"),
                    opacity="0.8",
                    spacing="2",
                    direction="row",
                    width="100%",
                ),
                
                spacing="6",
                width="100%"
            ),
            max_width="28em",
            width="100%",
            padding="4",
        ),
        height="100vh",
        width="100%",
    )