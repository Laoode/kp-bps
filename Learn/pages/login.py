import reflex as rx
from Learn.states import State, LoginState, Authentication

@rx.page(route="/")
def login_default_icons() -> rx.Component:
    return rx.center(  # Tambahkan center container di sini
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
                        "Sign in to your account",
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
                        value=LoginState.email, 
                        on_change=LoginState.update_email 
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
                        rx.link(
                            "Forgot password?",
                            href="#",
                            size="3",
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
                        value=LoginState.password,  
                        on_change=LoginState.update_password  
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.button(
                    "Sign in", 
                    size="3", 
                    width="100%",
                    on_click = Authentication.user_login,
                ),
                rx.center(
                    rx.text("New here?", size="3"),
                    rx.link("Sign up", href="/register", size="3"),
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