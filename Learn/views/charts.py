import datetime
import random
from ..backend.backend import State
import reflex as rx
from reflex.components.radix.themes.base import (
    LiteralAccentColor,
)

class StatsState(rx.State):
    area_toggle: bool = True
    selected_tab: str = "arisan"
    # timeframe: str = "Monthly"

    @rx.event
    def set_selected_tab(self, tab: str | list[str]):
        self.selected_tab = tab if isinstance(tab, str) else tab[0]

    @rx.event
    def toggle_areachart(self):
        self.area_toggle = not self.area_toggle
        

def area_toggle() -> rx.Component:
    return rx.cond(
        StatsState.area_toggle,
        rx.icon_button(
            rx.icon("area-chart"),
            size="2",
            cursor="pointer",
            variant="surface",
            on_click=StatsState.toggle_areachart,
        ),
        rx.icon_button(
            rx.icon("bar-chart-3"),
            size="2",
            cursor="pointer",
            variant="surface",
            on_click=StatsState.toggle_areachart,
        ),
    )

def _create_gradient(color: LiteralAccentColor, id: str) -> rx.Component:
    return (
        rx.el.svg.defs(
            rx.el.svg.linear_gradient(
                rx.el.svg.stop(
                    stop_color=rx.color(color, 7), offset="5%", stop_opacity=0.8
                ),
                rx.el.svg.stop(
                    stop_color=rx.color(color, 7), offset="95%", stop_opacity=0
                ),
                x1=0,
                x2=0,
                y1=0,
                y2=1,
                id=id,
            ),
        ),
    )

def _custom_tooltip(color: LiteralAccentColor) -> rx.Component:
    return (
        rx.recharts.graphing_tooltip(
            separator=" : ",
            content_style={
                "backgroundColor": rx.color("gray", 1),
                "borderRadius": "var(--radius-2)",
                "borderWidth": "1px",
                "borderColor": rx.color(color, 7),
                "padding": "0.5rem",
                "boxShadow": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
            },
            is_animation_active=True,
        ),
    )

def arisan_chart() -> rx.Component:
    data = State.get_deduction_data_last_12_months

    return rx.cond(
        StatsState.area_toggle,
        rx.recharts.area_chart(
            _create_gradient("lime", "colorLime"),
            _custom_tooltip("lime"),
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            rx.recharts.area(
                data_key="Arisan",
                stroke=rx.color("lime", 9),
                fill="url(#colorLime)",
                type_="monotone",
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            _custom_tooltip("lime"),
            rx.recharts.bar(
                data_key="Arisan",
                stroke=rx.color("lime", 9),
                fill=rx.color("lime", 7),
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False,  
            ),
            rx.recharts.y_axis(
                tick_line=False,  
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
    )

def iuran_dw_chart() -> rx.Component:
    data = State.get_deduction_data_last_12_months

    return rx.cond(
        StatsState.area_toggle,
        rx.recharts.area_chart(
            _create_gradient("blue", "colorBlue"),
            _custom_tooltip("blue"),
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            rx.recharts.area(
                data_key="Iuran DW",
                stroke=rx.color("blue", 9),
                fill="url(#colorBlue)",
                type_="monotone",
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            _custom_tooltip("blue"),
            rx.recharts.bar(
                data_key="Iuran DW",
                stroke=rx.color("blue", 9),
                fill=rx.color("blue", 7),
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
    )

def simpanan_wajib_koperasi_chart() -> rx.Component:
    data = State.get_deduction_data_last_12_months

    return rx.cond(
        StatsState.area_toggle,
        rx.recharts.area_chart(
            _create_gradient("green", "colorGreen"),
            _custom_tooltip("green"),
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            rx.recharts.area(
                data_key="Simpanan Wajib Koperasi",
                stroke=rx.color("green", 9),
                fill="url(#colorGreen)",
                type_="monotone",
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            _custom_tooltip("green"),
            rx.recharts.bar(
                data_key="Simpanan Wajib Koperasi",
                stroke=rx.color("green", 9),
                fill=rx.color("green", 7),
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
    )

def belanja_koperasi_chart() -> rx.Component:
    data = State.get_deduction_data_last_12_months

    return rx.cond(
        StatsState.area_toggle,
        rx.recharts.area_chart(
            _create_gradient("orange", "colorOrange"),
            _custom_tooltip("orange"),
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            rx.recharts.area(
                data_key="Belanja Koperasi",
                stroke=rx.color("orange", 9),
                fill="url(#colorOrange)",
                type_="monotone",
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            _custom_tooltip("orange"),
            rx.recharts.bar(
                data_key="Belanja Koperasi",
                stroke=rx.color("orange", 9),
                fill=rx.color("orange", 7),
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
    )

def simpanan_pokok_chart() -> rx.Component:
    data = State.get_deduction_data_last_12_months

    return rx.cond(
        StatsState.area_toggle,
        rx.recharts.area_chart(
            _create_gradient("purple", "colorPurple"),
            _custom_tooltip("purple"),
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            rx.recharts.area(
                data_key="Simpanan Pokok",
                stroke=rx.color("purple", 9),
                fill="url(#colorPurple)",
                type_="monotone",
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            _custom_tooltip("purple"),
            rx.recharts.bar(
                data_key="Simpanan Pokok",
                stroke=rx.color("purple", 9),
                fill=rx.color("purple", 7),
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
    )

def kredit_khusus_chart() -> rx.Component:
    data = State.get_deduction_data_last_12_months

    return rx.cond(
        StatsState.area_toggle,
        rx.recharts.area_chart(
            _create_gradient("brown", "colorBrown"),
            _custom_tooltip("brown"),
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            rx.recharts.area(
                data_key="Kredit Khusus",
                stroke=rx.color("brown", 9),
                fill="url(#colorBrown)",
                type_="monotone",
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            _custom_tooltip("brown"),
            rx.recharts.bar(
                data_key="Kredit Khusus",
                stroke=rx.color("brown", 9),
                fill=rx.color("brown", 7),
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
    )

def kredit_barang_chart() -> rx.Component:
    data = State.get_deduction_data_last_12_months

    return rx.cond(
        StatsState.area_toggle,
        rx.recharts.area_chart(
            _create_gradient("pink", "colorPink"),
            _custom_tooltip("pink"),
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            rx.recharts.area(
                data_key="Kredit Barang",
                stroke=rx.color("pink", 9),
                fill="url(#colorPink)",
                type_="monotone",
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(
                stroke_dasharray="3 3",
            ),
            _custom_tooltip("pink"),
            rx.recharts.bar(
                data_key="Kredit Barang",
                stroke=rx.color("pink", 9),
                fill=rx.color("pink", 7),
            ),
            rx.recharts.x_axis(
                data_key="month", 
                scale="auto",
                tick_line=False, 
            ),
            rx.recharts.y_axis(
                tick_line=False, 
                width=100,
            ),
            rx.recharts.legend(),
            data=data,
            height=425,
        ),
    )


def timeframe_select() -> rx.Component:
    return rx.select(
        ["Monthly", "Yearly"],
        default_value="Monthly",
        value=State.timeframe,
        variant="surface",
        on_change=State.set_timeframe,
    )
    
def pie_chart() -> rx.Component:
    return rx.recharts.pie_chart(
        rx.recharts.pie(
            data=State.payment_status_data,
            data_key="value",
            name_key="name",
            cx="50%",
            cy="50%",
            padding_angle=2,
            inner_radius="60%",
            outer_radius="80%",
            label=True,
        ),
        rx.recharts.graphing_tooltip(),
        rx.recharts.legend(),
        width="100%",
        height=300,
    )