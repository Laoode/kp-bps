import reflex as rx

# from .components.stats_cards import stats_cards_group
from .components.navbar import navbar
from .components.sidebar import sidebar
from .views.table import main_table
from .pages import *
from .states import Authentication
from . import styles
from .pages.index import index as dashboard_index

def index() -> rx.Component:
    return dashboard_index()

def table_page() -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.box(  # Wrapper untuk konten utama
            rx.vstack(
                navbar(),
                rx.box(
                    rx.vstack(
                        # Container untuk table
                        rx.box(
                            main_table(),
                            width="100%",
                            overflow_x="auto",  # Untuk scroll horizontal table
                            padding="1em",
                        ),
                        width="100%",
                        height="calc(100vh - 80px)",  # Kurangi tinggi navbar
                        overflow_y="auto",  # Untuk scroll vertical konten
                    ),
                    width="100%",
                    padding="1em",
                ),
                width="100%",
                height="100vh",
                spacing="4",
                overflow="hidden",  # Mencegah double scrollbar
            ),
            width="100%",
            overflow="hidden",
        ),
        width="100%",
        height="100vh",
        spacing="0",
        overflow="hidden",
    )

def admin_page() -> rx.Component:
    return rx.vstack(
        rx.heading("Admin Page", size="3"),
        width="100%",
        spacing="6",
        padding_x=["1.5em", "1.5em", "3em"],
    )

app = rx.App(
    theme=rx.theme(
        appearance="dark", has_background=True, radius="large", accent_color="grass"
    )
)

app.add_page(
    index,
    title="Dashbord Employee Deductions",
    description="Dashboard analytics employee deductions.",
    on_load=Authentication.require_auth
)

app.add_page(
    table_page,
    title="Employees Data App",
    description="A simple app to manage employees data table.",
    route="/table",
    on_load=Authentication.require_auth
)

app.add_page(
    admin_page,
    title="Admin Page",
    description="Admin management page.",
    route="/admin",
    on_load=Authentication.require_auth
)