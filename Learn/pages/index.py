import datetime

import reflex as rx
from dateutil.relativedelta import relativedelta  # Impor ditambahkan
from .. import styles
from ..templates import template
from ..components.card import card
from ..views.acquisition_view import barchart_v2
from ..views.charts import (
    StatsState,
    area_toggle,
    arisan_chart,
    iuran_dw_chart,
    simpanan_wajib_koperasi_chart,
    belanja_koperasi_chart,
    simpanan_pokok_chart,
    kredit_khusus_chart,
    kredit_barang_chart,
    timeframe_select,
    pie_chart,
)

def _time_data() -> rx.Component:
    """
    Menghasilkan komponen yang menampilkan rentang tanggal 12 bulan terakhir.
    """
    now = datetime.datetime.now()
    # Hitung tanggal awal sebagai awal bulan 11 bulan lalu (total 12 bulan termasuk bulan berjalan)
    start_date = now.replace(day=1) - relativedelta(months=11)
    date_range = f"{start_date.strftime('%b %Y')} - {now.strftime('%b %Y')}"
    
    return rx.hstack(
        rx.tooltip(
            rx.icon("info", size=20),
            content=date_range,
        ),
        rx.text("Last 12 months", size="4", weight="medium"),
        align="center",
        spacing="2",
        display=["none", "none", "flex"],
    )

def tab_content_header() -> rx.Component:
    return rx.hstack(
        _time_data(),
        area_toggle(),
        align="center",
        width="100%",
        spacing="4",
    )

@template(route="/", title="Overview")
def index() -> rx.Component:
    """The overview page.

    Returns:
        The UI for the overview page.

    """
    return rx.vstack(
        rx.heading(f"Welcome, Admin", size="5"),
        card(
            rx.hstack(
                tab_content_header(),
                rx.segmented_control.root(
                    rx.segmented_control.item("Arisan", value="arisan"),
                    rx.segmented_control.item("Iuran DW", value="iuran_dw"),
                    rx.segmented_control.item("S. Wajib", value="simpanan_wajib_koperasi"),
                    rx.segmented_control.item("B. Koperasi", value="belanja_koperasi"),
                    rx.segmented_control.item("S. Pokok", value="simpanan_pokok"),
                    rx.segmented_control.item("K. Khusus", value="kredit_khusus"),
                    rx.segmented_control.item("K. Barang", value="kredit_barang"),
                    margin_bottom="1.5em",
                    default_value="arisan",
                    on_change=StatsState.set_selected_tab,
                ),
                width="100%",
                justify="between",
            ),
            rx.match(
                StatsState.selected_tab,
                ("arisan", arisan_chart()),
                ("iuran_dw", iuran_dw_chart()),
                ("simpanan_wajib_koperasi", simpanan_wajib_koperasi_chart()),
                ("belanja_koperasi", belanja_koperasi_chart()),
                ("simpanan_pokok", simpanan_pokok_chart()),
                ("kredit_khusus", kredit_khusus_chart()),
                ("kredit_barang", kredit_barang_chart()),
            ),
        ),
        rx.grid(
            card(
                rx.hstack(
                    rx.hstack(
                        rx.icon("banknote", size=20),
                        rx.text("Payment Status Overview", size="4", weight="medium"),
                        align="center",
                        spacing="2",
                    ),
                    align="center",
                    width="100%",
                    justify="between",
                ),
                pie_chart(),
            ),
            # Card kosong untuk visualisasi lain
            card(
                rx.hstack(
                    rx.icon("chart-bar-big", size=20),
                    rx.text("Recap Employees", size="4", weight="medium"),
                    align="center",
                    spacing="2",
                ),
                barchart_v2(),
            ),
            gap="1rem",
            grid_template_columns=[
                "1fr",
                "repeat(1, 1fr)",
                "repeat(2, 1fr)",
                "repeat(2, 1fr)",
                "repeat(2, 1fr)",
            ],
            width="100%",
        ),
        spacing="8",
        width="100%",
    )