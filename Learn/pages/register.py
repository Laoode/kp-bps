import reflex as rx
from Learn.states import State, RegisterState, Registration

@rx.page(route="/register")
def register_default_icons() -> rx.Component:
    return rx.center(  
        rx.card(
            rx.vstack(
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
                        as_="h2",
                        text_align="center",
                        width="100%",
                    ),
                    direction="column",
                    spacing="5",
                    width="100%",
                ),
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
                        on_change=RegisterState.update_password 
                    ),
                    spacing="2",
                    width="100%",
                ),
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
                rx.button(
                    "Sign up", 
                    size="3", 
                    width="100%",
                    on_click = Registration.user_registration,
                ),
                rx.center(
                    rx.text("Already have an account?", size="3"),
                    rx.link("Sign in", href="/", size="3"),
                    opacity="0.8",
                    spacing="2",
                    direction="row",
                    width="100%",
                ),
                spacing="6",
                width="100%",
            ),
            max_width="28em",
            size="4",
            width="100%",
        ),
        height="100vh",
        width="100%",    
    )