import flet as ft

def LogHoursPage(page: ft.Page):
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Coming Soon!", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Look forward to logging your hours ;)"),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        expand=True,
        padding=20,
    )
