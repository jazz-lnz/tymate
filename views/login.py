import flet as ft

def LoginPage(page: ft.Page):
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Login", size=24, weight=ft.FontWeight.BOLD),
                ft.TextField(label="Username"),
                ft.TextField(label="Password", password=True),
                ft.ElevatedButton("Go", on_click=lambda _: page.go("/dashboard")),
                ft.TextButton("Don't have account? Sign up here."),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        expand=True,
        padding=40,
    )
