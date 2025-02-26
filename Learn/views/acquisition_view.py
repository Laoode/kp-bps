from dataclasses import dataclass, field
from ..wrappers.state import ComponentWrapperState
import reflex as rx
from ..backend.backend import State

@dataclass
class TooltipStyles:
    is_animation_active: bool = False
    separator: str = ""
    cursor: bool = False
    item_style: dict = field(
        default_factory=lambda: {
            "color": "currentColor",
            "display": "flex",
            "paddingBottom": "0px",
            "justifyContent": "space-between",
            "textTransform": "capitalize",
        },
    )
    label_style: dict = field(
        default_factory=lambda: {
            "color": rx.color("slate", 9),
            "fontWeight": "500",
        },
    )
    content_style: dict = field(
        default_factory=lambda: {
            "background": rx.color("slate", 1),
            "borderColor": rx.color("slate", 5),
            "borderRadius": "5px",
            "fontFamily": "var(--font-instrument-sans)",
            "fontSize": "0.875rem",
            "lineHeight": "1.25rem",
            "fontWeight": "500",
            "letterSpacing": "-0.01rem",
            "minWidth": "8rem",
            "width": "175px",
            "padding": "0.375rem 0.625rem ",
            "position": "relative",
        }
    )
    general_style: str = "[&_.recharts-tooltip-item-separator]:w-full"


tooltip_styles = TooltipStyles()

def month_navigation() -> rx.Component:
    """Komponen navigasi bulan."""
    return rx.hstack(
        rx.icon_button(
            rx.icon("chevron-left"),
            variant="ghost",
            on_click=State.prev_month_page,
        ),
        rx.badge(
            rx.center(
                rx.text(State.month_page_display),
                width="100%",
            ),
            variant="surface",
            min_width="150px",
            text_align="center",
            size="3",
        ),
        rx.icon_button(
            rx.icon("chevron-right"),
            variant="ghost",
            on_click=State.next_month_page,
        ),
        spacing="3",
    )
    
def barchart_v2()-> rx.Component:
    """Komponen visualisasi Recap Employees."""
    return rx.center(
        rx.vstack(
            rx.hstack(
                rx.input(
                    placeholder="Input NIP...",
                    width="250px",
                    value=State.nip_input,
                    on_change=State.set_nip_input,
                ),
                rx.button(
                    rx.icon("send-horizontal"),
                    variant="outline",
                    disabled=~State.is_nip_valid,
                    on_click=State.search_employee,
                ),
                rx.select(
                    ["Arisan", "Iuran DW", "Simpanan Wajib Koperasi", "Belanja Koperasi", 
                     "Simpanan Pokok", "Kredit Khusus", "Kredit Barang"],
                    placeholder="Deductions",
                    value=State.selected_deduction,
                    color_scheme="grass",
                    on_change=State.set_selected_deduction,
                ),
                rx.menu.root(
                    rx.menu.trigger(rx.icon("ellipsis-vertical")),
                    rx.menu.content(
                        rx.menu.item(
                            "Download this employee", 
                            shortcut="⌘ E",
                            on_click=State.download_employee_recap,
                        ),
                        rx.menu.item(
                            "Download all employees", 
                            shortcut="⌘ D",
                            on_click=State.download_all_recap,
                        ),
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            rx.recharts.bar_chart( 
                rx.recharts.graphing_tooltip(**vars(tooltip_styles)),
                rx.recharts.bar(
                    data_key="amount",
                    fill=ComponentWrapperState.default_theme[0],
                    radius=6,
                ),
                rx.recharts.x_axis(type_="number", hide=True, tick_size=0),
                rx.recharts.y_axis(
                    data_key="month",
                    type_="category",
                    axis_line=False,
                    tick_size=10,
                    tick_line=False,
                    custom_attrs={"fontSize": "12px"},
                ),
                data=State.monthly_data,
                layout="vertical",
                width="100%",
                height=250,
                bar_gap=2,
                margin={"left": -20},
            ),
            rx.hstack(
                rx.text(f"Recap by {State.selected_employee_name}"),
                month_navigation(),
                justify="between",
                spacing="3",
                wrap="wrap",
                width="100%",
            ),
            width="100%",
            class_name=tooltip_styles.general_style,
            on_mount=State.refresh_chart_data,
        ),
        width="100%",
        padding="0.5em",
    )
