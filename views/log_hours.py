import flet as ft

def LogHoursPage(page: ft.Page):
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Log Hours", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("This is a placeholder for the Log Hours page."),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        expand=True,
        padding=20,
    )
