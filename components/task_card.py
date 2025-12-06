import flet as ft

def TaskCard(title: str, due_date: str, completed: bool = False):
    """
    Reusable task card component
    Displays a checkbox, task title, and due date
    """
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Checkbox(value=completed),
                ft.Text(title, size=14, expand=True),
                ft.Text(due_date, size=12, color=ft.Colors.RED_400),
            ],
        ),
        bgcolor=ft.Colors.WHITE,
        border_radius=8,
        padding=12,
        margin=ft.margin.only(bottom=8),
    )
