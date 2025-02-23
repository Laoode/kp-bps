import reflex as rx

# from .components.stats_cards import stats_cards_group
from .views.navbar import navbar, navbar_dashboard
from .views.table import main_table
from .pages import *
from .states import Authentication
from . import styles
from .pages.index import index as dashboard_index

def index() -> rx.Component:
    return dashboard_index()

def table_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            main_table(),
            width="100%",
        ),
        width="100%",
        spacing="6",
        padding_x=["1.5em", "1.5em", "3em"],
        padding_bottom="2em",  # Tambahkan padding bottom
        margin_bottom="2em",   # Tambahkan margin bottom
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