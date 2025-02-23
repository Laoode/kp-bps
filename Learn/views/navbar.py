import reflex as rx
from Learn.states import State, LoginState, Authentication

def navbar():
    return rx.flex(
        rx.badge(
            rx.icon(tag="table-2", size=28),
            rx.heading("Employees Data App", size="6"),
            color_scheme="green",
            radius="large",
            align="center",
            variant="surface",
            padding="0.65rem",
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                "Logout",
                on_click=Authentication.handle_logout,
                color_scheme="red"
            ),
            rx.color_mode.button(),
            align="center",
            spacing="3",
        ),
        spacing="2",
        flex_direction=["column", "column", "row"],
        align="center",
        width="100%",
        top="0px",
        padding_top="2em",
    )

def navbar_dashboard():
    return rx.flex(
        rx.badge(
            rx.icon(tag="layout-dashboard", size=28),
            rx.heading("Dashboard Analytics", size="6"),
            color_scheme="green",
            radius="large",
            align="center",
            variant="surface",
            padding="0.65rem",
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                "Logout",
                on_click=Authentication.handle_logout,
                color_scheme="red"
            ),
            rx.color_mode.button(),
            align="center",
            spacing="3",
        ),
        spacing="2",
        flex_direction=["column", "column", "row"],
        align="center",
        width="100%",
        top="0px",
        padding_top="2em",
    )