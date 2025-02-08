import reflex as rx

def form_field(
    label: str,
    placeholder: str,
    type: str,
    name: str,
    icon: str,
    # value: any = None,
    default_value: str = "",
) -> rx.Component:
    # Jika default_value bukan None dan bukan string, konversi ke string.
    # Konversi None menjadi string kosong
    # default_value = str(default_value) if default_value is not None else ""

    return rx.form.field(
        rx.flex(
            rx.hstack(
                rx.icon(icon, size=16, stroke_width=1.5),
                rx.form.label(label),
                align="center",
                spacing="2",
            ),
            rx.form.control(
                rx.input(
                    placeholder=placeholder, type=type, default_value=default_value, id=name, name=name,is_required=False,
                ),
                as_child=True,
            ),
            direction="column",
            spacing="1",
        ),
        name=name,
        width="100%",
    )
