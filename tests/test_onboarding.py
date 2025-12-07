"""
TYMATE - Test Onboarding Wizard
RUN THIS FILE to see the onboarding wizard in action!

Usage: python test_onboarding.py
"""

import flet as ft
from views.onboarding import OnboardingPage

def main(page: ft.Page):
    page.title = "TYMATE - Onboarding Test"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 800
    page.window.height = 700
    page.padding = 0
    
    def on_onboarding_complete(data, budget):
        """Called when user finishes onboarding"""
        
        # Show success message
        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=100, color=ft.Colors.GREEN_600),
                        ft.Container(height=20),
                        ft.Text("Onboarding Complete!", size=32, weight=ft.FontWeight.BOLD),
                        ft.Container(height=20),
                        ft.Text("Your Settings:", size=20, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Text(f"Sleep: {data['sleep_hours']} hours/day"),
                        ft.Text(f"Has Work: {'Yes' if data['has_work'] else 'No'}"),
                        ft.Text(f"Work Hours: {data['work_hours_per_week']} hours/week"),
                        ft.Container(height=20),
                        ft.Text("Calculated Budget:", size=20, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Text(f"Free Time: {budget['free_hours_per_day']:.1f} hours/day", color=ft.Colors.GREEN_600),
                        ft.Text(f"Free Time: {budget['free_hours_per_week']:.1f} hours/week", color=ft.Colors.GREEN_600),
                        ft.Container(height=30),
                        ft.ElevatedButton(
                            "Restart Onboarding",
                            on_click=lambda e: show_onboarding(),
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.BLUE_400,
                                color=ft.Colors.WHITE,
                            ),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                expand=True,
                alignment=ft.alignment.center,
            )
        )
        page.update()
    
    def show_onboarding():
        """Show onboarding wizard"""
        page.controls.clear()
        page.add(OnboardingPage(page, on_onboarding_complete))
        page.update()
    
    # Start with onboarding
    show_onboarding()

if __name__ == "__main__":
    ft.app(target=main)