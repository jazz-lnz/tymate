import base64
import io
import math
import wave
import flet as ft
from datetime import datetime, timedelta
import time
import threading
from flet.core.audio import ReleaseMode
from state.task_manager import TaskManager
from state.session_manager import SessionManager
from utils.time_helpers import format_minutes


def TimeItPage(page: ft.Page, session: dict = None):
    """
    Time It page with Timer and Log modes for tracking task sessions
    
    Args:
        page: Flet page
        session: Session with user info
    """
    
    # Check if user is logged in
    if not session or not session.get("user"):
        return ft.Container(
            content=ft.Text("Please login first", size=20),
            alignment=ft.alignment.center,
            expand=True,
        )
    
    task_manager = TaskManager()
    session_manager = SessionManager()
    user_id = session["user"].id
    panel_bg = "#FFFFFF"
    border_color = "#B7C4D8"
    title_color = "#23211E"
    accent_color = "#6E7889"
    timer_start_color = "#4F8A5B"
    timer_pause_color = "#C78A33"
    timer_stop_color = "#C85C55"
    timer_disabled_bg = "#E8EDF5"
    timer_disabled_text = "#8E98A8"
    timer_disabled_border = "#CDD7E5"
    drop_shadow = ft.BoxShadow(
        spread_radius=0,
        blur_radius=3,
        color=ft.Colors.with_opacity(0.24, ft.Colors.BLACK),
        offset=ft.Offset(0, 2),
    )
    
    # Load user tasks
    user_tasks = task_manager.get_user_tasks(user_id, status_filter="Not Started")
    user_tasks.extend(task_manager.get_user_tasks(user_id, status_filter="In Progress"))
    user_tasks.extend(task_manager.get_user_tasks(user_id, status_filter="Started"))

    draft = session.get("time_it_draft", {}) or {}
    
    # Timer state
    timer_running = False
    timer_paused = False
    elapsed_seconds = int(draft.get("elapsed_seconds", 0) or 0)
    countdown_total = 0       # remaining seconds available for the selected task
    countdown_mode = False    # True when the selected task has an estimate
    selected_task_id = None
    timer_thread_active = True
    timeout_alerted = False
    session_start_remaining_seconds = 0
    pending_timer_start_after_estimate = False
    
    # ==================== TIMER MODE ====================
    
    # Timer display (MM:SS format)
    timer_display = ft.Text(
        "00:00",
        size=72,
        weight=ft.FontWeight.W_700,
        color=title_color,
        text_align=ft.TextAlign.CENTER,
    )
    
    # Task dropdown for timer mode
    timer_options = [
        ft.dropdown.Option(f"{task.title} (ID: {task.id})")
        for task in user_tasks
    ] if user_tasks else [ft.dropdown.Option("No active tasks")]
    timer_option_values = {opt.key for opt in timer_options}
    selected_task_id = session.get("selected_task_id")
    selected_task_option = next(
        (
            f"{task.title} (ID: {task.id})"
            for task in user_tasks
            if task.id == selected_task_id
        ),
        None,
    )
    draft_task_value = draft.get("task_dropdown_value")
    initial_task_value = None
    if draft_task_value in timer_option_values:
        initial_task_value = draft_task_value
    elif selected_task_option in timer_option_values:
        initial_task_value = selected_task_option
    elif user_tasks:
        initial_task_value = f"{user_tasks[0].title} (ID: {user_tasks[0].id})"

    timer_task_dropdown = ft.Dropdown(
        label="Select Task",
        width=350,
        options=timer_options,
        value=initial_task_value,
        border_color=border_color,
        bgcolor=panel_bg,
    )

    def extract_task_id(dropdown_value: str):
        if dropdown_value and "(ID:" in dropdown_value:
            try:
                return int(dropdown_value.split("(ID: ")[1].rstrip(")"))
            except (ValueError, IndexError):
                return None
        return None

    def build_timeout_beep_base64() -> str:
        sample_rate = 44100
        duration_seconds = 0.18
        frequency = 880
        amplitude = 0.35
        frame_count = int(sample_rate * duration_seconds)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            frames = bytearray()
            for index in range(frame_count):
                value = int(32767 * amplitude * math.sin(2 * math.pi * frequency * index / sample_rate))
                frames.extend(value.to_bytes(2, byteorder="little", signed=True))
            wav_file.writeframes(bytes(frames))
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    timeout_audio = ft.Audio(
        src_base64=build_timeout_beep_base64(),
        autoplay=False,
        volume=1,
        release_mode=ReleaseMode.STOP,
    )
    page.overlay.append(timeout_audio)

    timeout_snackbar = ft.SnackBar(
        content=ft.Text("Time is up. Add more time or mark the task complete."),
        bgcolor=ft.Colors.RED_700,
        duration=4000,
    )

    def get_task_remaining_seconds(task_id: int) -> int:
        task_obj = task_manager.get_task(task_id)
        if not task_obj or not task_obj.estimated_time:
            return 0
        total_estimated_seconds = int(task_obj.estimated_time) * 60
        logged_seconds = session_manager.get_total_minutes_for_task(task_id) * 60
        return max(total_estimated_seconds - logged_seconds, 0)

    def format_timer_value(minutes_value: float | int) -> str:
        total_seconds = max(int(round(float(minutes_value) * 60)), 0)
        return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"

    def refresh_timer_display_for_task(task_id: int | None = None):
        active_task_id = task_id if task_id is not None else extract_task_id(timer_task_dropdown.value)
        if active_task_id is None:
            timer_display.value = "00:00"
            timer_display.color = title_color
            timer_display.update()
            return

        refresh_timer_budget(active_task_id)
        if countdown_mode:
            timer_display.value = format_timer_value(max(countdown_total - elapsed_seconds, 0) / 60)
            timer_display.color = "#2D7A4F"
        else:
            timer_display.value = "00:00"
            timer_display.color = title_color
        timer_display.update()

    def refresh_timer_budget(task_id: int | None = None):
        nonlocal countdown_total, countdown_mode, session_start_remaining_seconds, timeout_alerted
        active_task_id = task_id if task_id is not None else extract_task_id(timer_task_dropdown.value)
        if active_task_id is None:
            countdown_total = 0
            countdown_mode = False
            session_start_remaining_seconds = 0
            timeout_alerted = False
            return

        remaining = get_task_remaining_seconds(active_task_id)
        countdown_total = remaining
        countdown_mode = remaining > 0
        if elapsed_seconds == 0:
            session_start_remaining_seconds = remaining
        timeout_alerted = False

    def on_timer_task_change(e):
        """Reconfigure remaining time for the selected task."""
        nonlocal elapsed_seconds
        if timer_running:
            return  # don't change mid-session

        task_id = extract_task_id(timer_task_dropdown.value)
        refresh_timer_budget(task_id)

        if countdown_mode:
            display_seconds = max(countdown_total - elapsed_seconds, 0)
            timer_display.value = format_timer_value(display_seconds / 60)
            timer_display.color = "#2D7A4F"
        else:
            timer_display.value = "00:00"
            timer_display.color = title_color
        timer_display.update()

    timer_task_dropdown.on_change = on_timer_task_change

    if elapsed_seconds > 0 and extract_task_id(timer_task_dropdown.value) is not None:
        refresh_timer_budget(extract_task_id(timer_task_dropdown.value))
        timer_display.value = format_timer_value(max(countdown_total - elapsed_seconds, 0) / 60)
        timer_display.color = "#2D7A4F" if countdown_mode else title_color
    elif extract_task_id(timer_task_dropdown.value) is not None:
        refresh_timer_budget(extract_task_id(timer_task_dropdown.value))
        timer_display.value = format_timer_value(countdown_total / 60) if countdown_mode else "00:00"
        timer_display.color = "#2D7A4F" if countdown_mode else title_color
    
    def update_timer_display():
        """Update the countdown every second for the active task."""
        nonlocal timer_running, timer_paused, elapsed_seconds, timeout_alerted

        while timer_thread_active:
            try:
                if timer_running and not timer_paused:
                    elapsed_seconds += 1

                    remaining = max(countdown_total - elapsed_seconds, 0)
                    timer_display.value = format_timer_value(remaining / 60)
                    if remaining == 0:
                        timer_display.color = ft.Colors.RED_700
                        if not timeout_alerted:
                            timeout_alerted = True
                            timer_running = False
                            timer_paused = False
                            try:
                                timeout_audio.play()
                            except Exception:
                                pass
                            try:
                                page.snack_bar = timeout_snackbar
                                timeout_snackbar.open = True
                                page.update()
                            except Exception:
                                pass
                            try:
                                show_message("Time is up. Add more time or mark the task complete.", "warning")
                            except Exception:
                                pass
                    elif remaining <= 60:
                        timer_display.color = ft.Colors.ORANGE_700
                    elif remaining <= max(countdown_total * 0.25, 60):
                        timer_display.color = ft.Colors.AMBER_700
                    else:
                        timer_display.color = "#2D7A4F"

                    timer_display.update()

            except (AssertionError, AttributeError):
                pass
            time.sleep(1)

    
    timer_thread = threading.Thread(target=update_timer_display, daemon=True)
    timer_thread.start()

    def save_timer_draft():
        if elapsed_seconds > 0:
            session["time_it_draft"] = {
                "elapsed_seconds": elapsed_seconds,
                "task_dropdown_value": timer_task_dropdown.value,
            }
        else:
            session.pop("time_it_draft", None)

    def cleanup_time_it(preserve_progress: bool = True):
        nonlocal timer_running, timer_paused, timer_thread_active
        if preserve_progress:
            save_timer_draft()
        else:
            session.pop("time_it_draft", None)
        timer_running = False
        timer_paused = False
        timer_thread_active = False

    def discard_current_session():
        nonlocal timer_running, timer_paused, elapsed_seconds, countdown_mode, countdown_total, timeout_alerted, session_start_remaining_seconds
        timer_running = False
        timer_paused = False
        elapsed_seconds = 0
        timeout_alerted = False
        session_start_remaining_seconds = countdown_total
        session.pop("time_it_draft", None)
        try:
            on_timer_task_change(None)
            sync_timer_controls()
            page.update()
        except (AssertionError, AttributeError):
            pass

    session["time_it_is_timer_running"] = lambda: timer_running and not timer_paused
    session["time_it_is_timer_paused"] = lambda: timer_running and timer_paused
    session["time_it_has_active_progress"] = lambda: elapsed_seconds > 0
    session["time_it_cleanup"] = cleanup_time_it
    session["time_it_discard_current_session"] = discard_current_session

    def parse_timestamp(value: str | None):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def build_session_stamp_lines(logged_at: str | None, created_at: str | None):
        worked_dt = parse_timestamp(logged_at)
        recorded_dt = parse_timestamp(created_at)
        worked_line = f"Worked {worked_dt.strftime('%b %d, %Y %I:%M %p')}" if worked_dt else "Worked time unavailable"
        recorded_line = ""
        if worked_dt and recorded_dt and abs((recorded_dt - worked_dt).total_seconds()) >= 60:
            recorded_line = f"Recorded {recorded_dt.strftime('%b %d, %Y %I:%M %p')}"
        return worked_line, recorded_line

    def format_date_for_input(value: str | None) -> str:
        raw = (value or "").strip()
        if not raw:
            return ""
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%m-%d-%Y")
        except ValueError:
            return raw

    def parse_date_input(value: str | None):
        raw = (value or "").strip()
        if not raw:
            return None
        for fmt in ("%m-%d-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    def build_logged_at_value(date_value: str | None, time_value: str | None):
        date_text = (date_value or "").strip()
        time_text = (time_value or "").strip()
        if not date_text:
            return None, "Please choose the work date"
        if not time_text:
            return None, "Please enter the work time"
        date_part = parse_date_input(date_text)
        if date_part is None:
            return None, "Use date format MM-DD-YYYY"
        try:
            logged_time = datetime.strptime(time_text, "%H:%M")
            logged_dt = datetime(
                date_part.year,
                date_part.month,
                date_part.day,
                logged_time.hour,
                logged_time.minute,
            )
        except ValueError:
            return None, "Use 24-hour time in HH:MM format"
        if logged_dt > datetime.now() + timedelta(minutes=1):
            return None, "Session date and time cannot be in the future"
        return logged_dt.isoformat(), None

    def open_time_picker(initial_time_text: str, on_pick):
        init_hour = 0
        init_minute = 0
        try:
            parsed = datetime.strptime((initial_time_text or "00:00").strip(), "%H:%M")
            init_hour = parsed.hour
            init_minute = parsed.minute
        except ValueError:
            pass

        def handle_change(e):
            if e.control.value is not None:
                picked = e.control.value
                on_pick(f"{picked.hour:02d}:{picked.minute:02d}")
                page.update()

        picker = ft.TimePicker(
            value=datetime(2000, 1, 1, init_hour, init_minute),
            on_change=handle_change,
        )
        page.open(picker)

    def open_date_picker(initial_date_text: str, on_pick):
        def handle_change(e):
            if e.control.value:
                picked = e.control.value
                if hasattr(picked, "date"):
                    on_pick(picked.date().strftime("%m-%d-%Y"))
                else:
                    on_pick(str(picked))
                page.update()

        picker_value = None
        parsed_initial = parse_date_input(initial_date_text)
        if parsed_initial is not None:
            picker_value = parsed_initial

        picker = ft.DatePicker(value=picker_value, on_change=handle_change)
        page.open(picker)

    def apply_timer_button_style(button: ft.ElevatedButton, enabled: bool, active_bg: str):
        button.style = ft.ButtonStyle(
            bgcolor=active_bg if enabled else timer_disabled_bg,
            color=ft.Colors.WHITE if enabled else timer_disabled_text,
            side=ft.BorderSide(1, active_bg if enabled else timer_disabled_border),
        )

    def open_estimate_dialog(is_extension: bool = False, start_after_save: bool = False):
        nonlocal countdown_total, countdown_mode, session_start_remaining_seconds, timer_running, timer_paused, elapsed_seconds, timeout_alerted, pending_timer_start_after_estimate
        task_id = extract_task_id(timer_task_dropdown.value)
        if task_id is None:
            show_message("Please select a task first", "warning")
            return

        existing_task = task_manager.get_task(task_id)
        current_estimate = float(existing_task.estimated_time or 0) if existing_task else 0.0
        pending_timer_start_after_estimate = start_after_save
        prompt_title = "Add More Time" if is_extension and current_estimate > 0 else "Set Estimated Time"
        action_label = "Add Time" if is_extension and current_estimate > 0 else ("Save & Start" if start_after_save else "Save Estimate")
        estimate_field = ft.TextField(
            label="Minutes",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=220,
            hint_text="e.g., 30",
        )
        info_text = ft.Text(
            f"Current estimate: {format_minutes(current_estimate)}",
            size=12,
            color=accent_color,
            visible=current_estimate > 0,
        )

        def save_estimate(_):
            nonlocal countdown_total, countdown_mode, session_start_remaining_seconds, timer_running, timer_paused, elapsed_seconds, timeout_alerted, pending_timer_start_after_estimate
            try:
                add_minutes = int((estimate_field.value or "").strip())
                if add_minutes <= 0:
                    raise ValueError
            except ValueError:
                show_message("Enter a positive whole number of minutes", "warning")
                return

            updated_estimate = int(round(current_estimate + add_minutes))
            ok, msg = task_manager.update_task(task_id, estimated_time=updated_estimate)
            if not ok:
                show_message(msg, "error")
                return

            refresh_timer_budget(task_id)
            session_start_remaining_seconds = countdown_total
            timeout_alerted = False
            dialog.open = False
            if elapsed_seconds > 0 or pending_timer_start_after_estimate:
                timer_running = True
                timer_paused = False
            pending_timer_start_after_estimate = False
            refresh_timer_display_for_task(task_id)
            sync_timer_controls()
            page.update()
            show_message("Estimate updated", "success")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(prompt_title, weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    info_text,
                    estimate_field,
                    ft.Text(
                        "This amount will be added to the task's estimate and used as the timer budget.",
                        size=11,
                        color=accent_color,
                    ),
                ],
                width=320,
                tight=True,
                spacing=8,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
                ft.ElevatedButton(action_label, bgcolor=timer_start_color, color=ft.Colors.WHITE, on_click=save_estimate),
            ],
        )
        page.open(dialog)
        page.update()

    def mark_task_complete_now(e):
        nonlocal timer_running, timer_paused, elapsed_seconds, timeout_alerted
        task_id = extract_task_id(timer_task_dropdown.value)
        if task_id is None:
            show_message("Please select a task first", "warning")
            return

        # Keep completion/session semantics aligned with Task Details:
        # optional duration is passed through TaskManager.mark_complete().
        duration_minutes = (elapsed_seconds / 60.0) if elapsed_seconds > 0 else None

        ok, msg = task_manager.mark_complete(
            task_id,
            duration_minutes=duration_minutes,
            event_date=datetime.now().isoformat(),
        )
        if ok:
            timer_running = False
            timer_paused = False
            elapsed_seconds = 0
            timeout_alerted = False
            session.pop("time_it_draft", None)
            refresh_timer_budget(task_id)
            timer_display.value = "00:00"
            timer_display.color = ft.Colors.GREEN_700
            sync_timer_controls()
            refresh_session_history()
            page.update()
            show_message(msg or "Task marked complete", "success")
        else:
            show_message(msg, "error")

    def sync_timer_controls():
        start_button.disabled = timer_running or elapsed_seconds > 0
        pause_button.disabled = not timer_running
        pause_button.text = "Resume" if timer_paused else "Pause"
        stop_button.disabled = elapsed_seconds == 0
        timer_task_dropdown.disabled = timer_running or elapsed_seconds > 0
        apply_timer_button_style(start_button, not start_button.disabled, timer_start_color)
        apply_timer_button_style(pause_button, not pause_button.disabled, timer_pause_color)
        apply_timer_button_style(stop_button, not stop_button.disabled, timer_stop_color)
    
    def start_timer(e):
        nonlocal timer_running, timer_paused, timeout_alerted, session_start_remaining_seconds
        task_id = extract_task_id(timer_task_dropdown.value)
        if task_id is None:
            show_message("Please select a valid task before starting the timer", "warning")
            return
        refresh_timer_budget(task_id)
        if not countdown_mode or countdown_total <= 0:
            open_estimate_dialog(is_extension=False, start_after_save=True)
            return
        timer_running = True
        timer_paused = False
        timeout_alerted = False
        session_start_remaining_seconds = countdown_total
        sync_timer_controls()
        page.update()
    
    def pause_timer(e):
        nonlocal timer_paused
        timer_paused = not timer_paused
        if timer_paused:
            save_timer_draft()
        sync_timer_controls()
        page.update()

    def open_timer_save_dialog(task_id: int, duration_minutes: float):
        nonlocal timer_running, timer_paused, elapsed_seconds, countdown_total, timeout_alerted
        task_title = next((task.title for task in user_tasks if task.id == task_id), f"Task #{task_id}")

        estimate_minutes = session_start_remaining_seconds / 60.0 if session_start_remaining_seconds > 0 else None
        summary_lines = [
            ft.Text(f"Task: {task_title}", size=14, weight=ft.FontWeight.W_600, color=title_color),
            ft.Text(f"This session: {format_minutes(duration_minutes)}", size=12, color=accent_color),
        ]
        if estimate_minutes is not None:
            summary_lines.append(ft.Text(f"Estimate remaining before start: {format_minutes(estimate_minutes)}", size=12, color=accent_color))
        summary_lines.append(ft.Text("Save this session, or discard it if this was a misclick.", size=11, color=accent_color))
        notes_field = ft.TextField(
            label="Session Notes (optional)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=360,
            border_color=border_color,
            bgcolor=panel_bg,
            hint_text="What did you work on during this session?",
        )

        def close_dialog(restore_paused_state: bool):
            nonlocal timer_running, timer_paused
            dialog.open = False
            if restore_paused_state:
                timer_running = True
                timer_paused = True
                save_timer_draft()
            sync_timer_controls()
            page.update()

        def save_timed_session(include_notes: bool):
            nonlocal timer_running, timer_paused, elapsed_seconds, countdown_mode, countdown_total, timeout_alerted
            notes = (notes_field.value or "").strip() if include_notes else ""
            success, message, logged_session = session_manager.add_session(
                user_id=user_id,
                task_id=task_id,
                duration_minutes=duration_minutes,
                notes=notes or None,
            )

            if not success:
                show_message(message, "error")
                return

            timer_running = False
            timer_paused = False
            elapsed_seconds = 0
            timeout_alerted = False
            session.pop("time_it_draft", None)
            refresh_timer_budget(task_id)
            timer_display.value = format_timer_value(countdown_total / 60) if countdown_mode else "00:00"
            timer_display.color = "#2D7A4F" if countdown_mode else title_color
            timer_display.update()
            close_dialog(restore_paused_state=False)
            show_message(f"Session logged: {format_minutes(duration_minutes)}", "success")
            refresh_session_history()

        def discard_timed_session(_):
            dialog.open = False
            discard_current_session()
            show_message("Session discarded", "info")
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Save Timed Session", weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    *summary_lines,
                    ft.Container(height=4),
                    notes_field,
                ],
                width=360,
                tight=True,
                spacing=8,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(restore_paused_state=True)),
                ft.TextButton("Discard Session", on_click=discard_timed_session),
                ft.TextButton("Skip Notes", on_click=lambda e: save_timed_session(include_notes=False)),
                ft.ElevatedButton(
                    "Save Session",
                    bgcolor=timer_start_color,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: save_timed_session(include_notes=True),
                ),
            ],
        )
        page.open(dialog)
        page.update()
    
    def stop_timer(e):
        nonlocal timer_running, timer_paused, elapsed_seconds, timeout_alerted
        # Extract task ID from dropdown
        nonlocal selected_task_id
        selected_task_id = extract_task_id(timer_task_dropdown.value)
        if selected_task_id is None:
            show_message("Please select a valid task before stopping the timer", "warning")
            return

        timer_running = False
        timer_paused = False
        
        if elapsed_seconds == 0:
            show_message("Timer has no elapsed time", "warning")
            sync_timer_controls()
            page.update()
            return
        
        duration_minutes = elapsed_seconds / 60.0

        save_timer_draft()
        sync_timer_controls()
        open_timer_save_dialog(selected_task_id, duration_minutes)
        page.update()
    
    # Timer buttons
    start_button = ft.ElevatedButton(
        "Start",
        on_click=start_timer,
        width=100,
    )
    
    pause_button = ft.ElevatedButton(
        "Pause",
        on_click=pause_timer,
        width=100,
        disabled=True,
    )
    
    stop_button = ft.ElevatedButton(
        "Stop",
        on_click=stop_timer,
        width=100,
        disabled=True,
    )
    
    add_time_button = ft.ElevatedButton(
        "Set / Add Time",
        on_click=lambda e: open_estimate_dialog(is_extension=True),
        width=140,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_GREY_700,
            color=ft.Colors.WHITE,
        ),
    )

    complete_button = ft.ElevatedButton(
        "Mark Complete",
        on_click=mark_task_complete_now,
        width=140,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
        ),
    )

    timer_buttons_row = ft.Row(
        controls=[start_button, pause_button, stop_button, add_time_button, complete_button],
        spacing=10,
        alignment=ft.MainAxisAlignment.CENTER,
        wrap=True,
    )

    current_timer_task_id = extract_task_id(timer_task_dropdown.value)
    if current_timer_task_id is not None:
        refresh_timer_budget(current_timer_task_id)
        if elapsed_seconds > 0:
            timer_running = True
            timer_paused = True
    sync_timer_controls()

    timer_mode_content = ft.Column(
        controls=[
            ft.Text("Timer Mode", size=20, weight=ft.FontWeight.W_700, color=title_color),
            ft.Container(
                content=ft.Text(
                    "Note: Switching app tabs pauses the timer! Keep this page open to track time AND to stay aware of why you're here ദ്ദി◝ ⩊ ◜.ᐟ",
                    size=12,
                    color="#7F5A2B",
                    italic=True,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor="#FFF7EA",
                border=ft.border.all(1, "#EBCFA4"),
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                width=520,
                alignment=ft.alignment.center,
            ),
            ft.Container(height=12),
            timer_task_dropdown,
            ft.Container(height=20),
            timer_display,
            ft.Container(height=20),
            timer_buttons_row,
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # ==================== LOG MODE ====================
    
    # Task dropdown for log mode
    log_task_dropdown = ft.Dropdown(
        label="Select Task",
        width=350,
        options=[
            ft.dropdown.Option(f"{task.title} (ID: {task.id})") 
            for task in user_tasks
        ] if user_tasks else [ft.dropdown.Option("No active tasks")],
        value=f"{user_tasks[0].title} (ID: {user_tasks[0].id})" if user_tasks else None,
        border_color=border_color,
        bgcolor=panel_bg,
    )
    
    # Minutes input field
    minutes_input = ft.TextField(
        label="Duration (minutes)",
        width=350,
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=border_color,
        bgcolor=panel_bg,
        hint_text="e.g., 45",
    )
    
    # Notes field
    notes_input = ft.TextField(
        label="Notes (optional)",
        width=350,
        border_color=border_color,
        bgcolor=panel_bg,
        multiline=True,
        min_lines=1,
        max_lines=2,
        hint_text="What did you accomplish?",
    )
    manual_logged_date_field = ft.TextField(
        value=datetime.now().strftime("%m-%d-%Y"),
        label="Date",
        read_only=True,
        expand=True,
        border_color=border_color,
        bgcolor=panel_bg,
    )
    manual_logged_time_field = ft.TextField(
        value=datetime.now().strftime("%H:%M"),
        label="Time",
        read_only=True,
        width=76,
        hint_text="HH:MM",
        border_color=border_color,
        bgcolor=panel_bg,
    )

    def reset_manual_logged_when():
        now = datetime.now()
        manual_logged_date_field.value = now.strftime("%m-%d-%Y")
        manual_logged_time_field.value = now.strftime("%H:%M")

    def open_manual_date_picker(_):
        open_date_picker(
            manual_logged_date_field.value,
            lambda value: setattr(manual_logged_date_field, "value", value),
        )

    def open_manual_time_picker(_):
        open_time_picker(
            manual_logged_time_field.value,
            lambda value: setattr(manual_logged_time_field, "value", value),
        )

    def open_edit_session_dialog(session_item):
        logged_dt = parse_timestamp(session_item.logged_at) or datetime.now()
        date_field = ft.TextField(
            label="Date",
            value=logged_dt.strftime("%m-%d-%Y"),
            read_only=True,
            expand=True,
            border_color=border_color,
            bgcolor=panel_bg,
        )
        time_field = ft.TextField(
            label="Time",
            value=logged_dt.strftime("%H:%M"),
            read_only=True,
            width=130,
            border_color=border_color,
            bgcolor=panel_bg,
        )
        minutes_field = ft.TextField(
            label="Duration (minutes)",
            value=str(session_item.duration_minutes or ""),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=border_color,
            bgcolor=panel_bg,
            width=350,
        )
        notes_field = ft.TextField(
            label="Session Notes (optional)",
            value=session_item.notes or "",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=350,
            border_color=border_color,
            bgcolor=panel_bg,
        )
        error_text = ft.Text("", color=ft.Colors.RED_700, size=12)

        def save_changes(_):
            try:
                minutes = int((minutes_field.value or "").strip())
            except ValueError:
                error_text.value = "Duration must be a valid number"
                page.update()
                return
            if minutes <= 0:
                error_text.value = "Duration must be a positive number"
                page.update()
                return

            logged_at, logged_at_error = build_logged_at_value(date_field.value, time_field.value)
            if logged_at_error:
                error_text.value = logged_at_error
                page.update()
                return

            notes = (notes_field.value or "").strip() or None
            ok, message, _updated = session_manager.update_session(
                session_id=session_item.id,
                user_id=user_id,
                duration_minutes=minutes,
                notes=notes,
                logged_at=logged_at,
            )
            if not ok:
                error_text.value = message
                page.update()
                return

            dialog.open = False
            refresh_session_history()
            show_message("Session updated", "success")
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit Session", weight=ft.FontWeight.W_600),
            content=ft.Column(
                controls=[
                    minutes_field,
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, color=ft.Colors.BLUE_GREY_500, size=18),
                                date_field,
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_DROP_DOWN_CIRCLE_OUTLINED,
                                    tooltip="Pick work date",
                                    icon_color=ft.Colors.BLUE_GREY_600,
                                    on_click=lambda e: open_date_picker(date_field.value, lambda v: setattr(date_field, "value", v)),
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor="#F5F8FC",
                        border_radius=10,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ACCESS_TIME, color=ft.Colors.BLUE_GREY_500, size=18),
                                time_field,
                                ft.IconButton(
                                    icon=ft.Icons.ACCESS_TIME,
                                    tooltip="Pick work time",
                                    icon_color=ft.Colors.BLUE_GREY_600,
                                    on_click=lambda e: open_time_picker(time_field.value, lambda v: setattr(time_field, "value", v)),
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor="#F5F8FC",
                        border_radius=10,
                    ),
                    notes_field,
                    error_text,
                ],
                width=380,
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
                ft.ElevatedButton(
                    "Save",
                    bgcolor=timer_start_color,
                    color=ft.Colors.WHITE,
                    on_click=save_changes,
                ),
            ],
        )
        page.open(dialog)
        page.update()

    def confirm_delete_session(session_item):
        title = task_titles_by_id.get(session_item.task_id, f"Task #{session_item.task_id}")

        def perform_delete(_):
            ok, message = session_manager.delete_session(session_item.id)
            dialog.open = False
            if ok:
                refresh_timer_display_for_task(session_item.task_id)
                refresh_session_history()
                show_message("Session deleted", "success")
            else:
                show_message(message, "error")
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Session", weight=ft.FontWeight.W_600),
            content=ft.Text(
                f"Delete this session for {title}? This will remove it from history and activity.",
                size=13,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, "open", False) or page.update()),
                ft.ElevatedButton(
                    "Delete",
                    bgcolor=timer_stop_color,
                    color=ft.Colors.WHITE,
                    on_click=perform_delete,
                ),
            ],
        )
        page.open(dialog)
        page.update()

    user_tasks_for_history = task_manager.get_user_tasks(user_id, include_deleted=False)
    task_titles_by_id = {
        task.id: task.title for task in user_tasks_for_history if task.id is not None
    }
    session_history_container = ft.Column(spacing=8)
    history_filter_mode = "today"
    history_search_query = ""

    history_title_text = ft.Text("Session History (Today)", size=16, weight=ft.FontWeight.W_700, color=title_color)
    history_total_label = ft.Text("Total Session Time", size=13, color=accent_color, weight=ft.FontWeight.W_600)
    history_total_value = ft.Text(format_minutes(0), size=18, color=title_color, weight=ft.FontWeight.W_700)

    history_today_button = ft.ElevatedButton("Today")
    history_week_button = ft.ElevatedButton("This Week")
    history_all_button = ft.ElevatedButton("All")
    history_search_field = ft.TextField(
        label="Search history",
        hint_text="Filter by task or notes",
        width=320,
        border_color=border_color,
        bgcolor=panel_bg,
    )

    def update_history_toggle_buttons():
        is_today = history_filter_mode == "today"
        is_week = history_filter_mode == "week"
        history_today_button.bgcolor = "#6E7889" if is_today else "#EDF2FA"
        history_today_button.color = ft.Colors.WHITE if is_today else title_color
        history_week_button.bgcolor = "#6E7889" if is_week else "#EDF2FA"
        history_week_button.color = ft.Colors.WHITE if is_week else title_color
        history_all_button.bgcolor = "#6E7889" if history_filter_mode == "all" else "#EDF2FA"
        history_all_button.color = ft.Colors.WHITE if history_filter_mode == "all" else title_color

    def refresh_session_history():
        nonlocal history_search_query
        if history_filter_mode == "today":
            sessions = session_manager.get_sessions_for_user_today(user_id)
        elif history_filter_mode == "week":
            all_sessions = session_manager.get_sessions_for_user(user_id)
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            next_week_start = week_start + timedelta(days=7)
            sessions = []
            for session_item in all_sessions:
                if not session_item.logged_at:
                    continue
                try:
                    logged_date = datetime.fromisoformat(session_item.logged_at).date()
                except ValueError:
                    continue
                if week_start <= logged_date < next_week_start:
                    sessions.append(session_item)
        else:
            sessions = session_manager.get_sessions_for_user(user_id)

        q = history_search_query.strip().lower()
        if q:
            filtered_sessions = []
            for session_item in sessions:
                title = task_titles_by_id.get(session_item.task_id, f"Task #{session_item.task_id}")
                notes = session_item.notes or ""
                if q in title.lower() or q in notes.lower():
                    filtered_sessions.append(session_item)
            sessions = filtered_sessions

        session_history_container.controls.clear()
        if history_filter_mode == "today":
            history_title_text.value = "Session History (Today)"
        elif history_filter_mode == "week":
            history_title_text.value = "Session History (This Week)"
        else:
            history_title_text.value = "Session History (All)"
        total_minutes = sum(session.duration_minutes or 0 for session in sessions)
        history_total_value.value = format_minutes(total_minutes)
        update_history_toggle_buttons()

        if not sessions:
            empty_msg = (
                "No sessions logged yet today."
                if history_filter_mode == "today"
                else "No sessions logged yet this week."
                if history_filter_mode == "week"
                else "No sessions logged yet."
            )
            session_history_container.controls.append(
                ft.Text(
                    empty_msg,
                    size=12,
                    color=accent_color,
                )
            )
        else:
            sorted_sessions = sorted(
                sessions,
                key=lambda item: parse_timestamp(item.logged_at) or datetime.min,
                reverse=True,
            )
            for logged_session in sorted_sessions:
                title = task_titles_by_id.get(logged_session.task_id, f"Task #{logged_session.task_id}")
                worked_line, recorded_line = build_session_stamp_lines(
                    logged_session.logged_at,
                    logged_session.created_at,
                )

                notes_preview = (logged_session.notes or "").strip()
                notes_snippet = (notes_preview[:60] + "…") if len(notes_preview) > 60 else notes_preview
                session_history_container.controls.append(
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=title_color, no_wrap=True),
                                            ft.Text(worked_line, size=11, color=accent_color),
                                        ] + (
                                            [ft.Text(notes_snippet, size=11, color="#6E7889", italic=True)]
                                            if notes_snippet else []
                                        ),
                                        spacing=2,
                                        expand=True,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(format_minutes(logged_session.duration_minutes), size=12, color="#4F6795", weight=ft.FontWeight.W_700),
                                            ft.Row(
                                                controls=[
                                                    ft.IconButton(
                                                        icon=ft.Icons.EDIT_OUTLINED,
                                                        tooltip="Edit session",
                                                        icon_size=14,
                                                        padding=ft.padding.all(2),
                                                        on_click=lambda e, item=logged_session: open_edit_session_dialog(item),
                                                    ),
                                                    ft.IconButton(
                                                        icon=ft.Icons.DELETE_OUTLINE,
                                                        tooltip="Delete session",
                                                        icon_color=timer_stop_color,
                                                        icon_size=14,
                                                        padding=ft.padding.all(2),
                                                        on_click=lambda e, item=logged_session: confirm_delete_session(item),
                                                    ),
                                                ],
                                                spacing=0,
                                            ),
                                        ],
                                        spacing=0,
                                        horizontal_alignment=ft.CrossAxisAlignment.END,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                spacing=6,
                            ),
                            ft.Divider(height=1, thickness=1, color=border_color),
                        ],
                        spacing=0,
                    )
                )

        if session_history_container.page is not None:
            session_history_container.update()

    def show_today_history(e):
        nonlocal history_filter_mode
        history_filter_mode = "today"
        refresh_session_history()
        page.update()

    def show_all_history(e):
        nonlocal history_filter_mode
        history_filter_mode = "all"
        refresh_session_history()
        page.update()

    def on_history_search_change(e):
        nonlocal history_search_query
        history_search_query = e.control.value or ""
        refresh_session_history()
        page.update()

    def show_week_history(e):
        nonlocal history_filter_mode
        history_filter_mode = "week"
        refresh_session_history()
        page.update()

    history_today_button.on_click = show_today_history
    history_week_button.on_click = show_week_history
    history_all_button.on_click = show_all_history
    history_search_field.on_change = on_history_search_change
    
    def submit_log(e):
        # Extract task ID
        task_id = extract_task_id(log_task_dropdown.value)
        if task_id is None:
            show_message("Please select a task", "warning")
            return
        
        # Validate minutes
        if not minutes_input.value or minutes_input.value.strip() == "":
            show_message("Please enter duration in minutes", "warning")
            return
        
        try:
            duration_minutes = float(minutes_input.value)
            if duration_minutes <= 0:
                show_message("Duration must be a positive number", "warning")
                return
        except ValueError:
            show_message("Duration must be a valid number", "warning")
            return

        logged_at, logged_at_error = build_logged_at_value(
            manual_logged_date_field.value,
            manual_logged_time_field.value,
        )
        if logged_at_error:
            show_message(logged_at_error, "warning")
            return
        
        # Log session
        notes = notes_input.value.strip() if notes_input.value else None
        success, message, logged_session = session_manager.add_session(
            user_id=user_id,
            task_id=task_id,
            duration_minutes=duration_minutes,
            notes=notes,
            logged_at=logged_at,
        )
        
        if success:
            show_message(f"Session logged: {format_minutes(duration_minutes)}", "success")
            # Clear inputs
            minutes_input.value = ""
            notes_input.value = ""
            reset_manual_logged_when()
            refresh_session_history()
            page.update()
        else:
            show_message(message, "error")
    
    submit_button = ft.ElevatedButton(
        "Submit",
        on_click=submit_log,
        width=200,
        style=ft.ButtonStyle(
            bgcolor="#6E7889",
            color=ft.Colors.WHITE,
            side=ft.BorderSide(1, border_color),
        ),
    )
    
    log_mode_content = ft.Column(
        controls=[
            ft.Text("Log Mode", size=20, weight=ft.FontWeight.W_700, color=title_color),
            ft.Container(height=12),
            log_task_dropdown,
            ft.Container(height=12),
            minutes_input,
            ft.Container(height=12),
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                manual_logged_date_field,
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_DROP_DOWN_CIRCLE_OUTLINED,
                                    tooltip="Pick work date",
                                    icon_color=ft.Colors.BLUE_GREY_600,
                                    on_click=open_manual_date_picker,
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        bgcolor="#F5F8FC",
                        border_radius=10,
                        expand=True,
                    ),
                    manual_logged_time_field,
                    ft.IconButton(
                        icon=ft.Icons.ACCESS_TIME,
                        tooltip="Pick work time",
                        icon_color=ft.Colors.BLUE_GREY_600,
                        on_click=open_manual_time_picker,
                    ),
                ],
                spacing=10,
                width=386,
            ),
            ft.Text(
                "Log when the work actually happened using 24-hour time.",
                size=11,
                color=accent_color,
            ),
            ft.Container(height=12),
            notes_input,
            ft.Container(height=20),
            submit_button,
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    # ==================== MODE TOGGLE ====================
    
    # Create tabs for mode selection
    def on_tabs_change(e):
        nonlocal timer_paused
        if e.control.selected_index == 1 and timer_running and not timer_paused:
            timer_paused = True
            save_timer_draft()
            sync_timer_controls()
            show_message("Timer auto-paused after switching to Log tab", "info")
            page.update()

    tabs = ft.Tabs(
        selected_index=0,
        on_change=on_tabs_change,
        tabs=[
            ft.Tab(
                text="Timer",
                content=ft.Container(
                    content=timer_mode_content,
                    padding=24,
                ),
            ),
            ft.Tab(
                text="Log",
                content=ft.Container(
                    content=log_mode_content,
                    padding=24,
                ),
            ),
        ],
    )

    mode_panel = ft.Container(
        content=tabs,
        expand=True,
        height=620,
        border=ft.border.all(1.5, border_color),
        border_radius=12,
        bgcolor=panel_bg,
        shadow=drop_shadow,
        padding=ft.padding.only(bottom=8),
    )

    history_panel = ft.Container(
        content=session_history_container,
        border=ft.border.all(1.5, border_color),
        border_radius=12,
        bgcolor=panel_bg,
        shadow=drop_shadow,
        padding=10,
    )

    refresh_session_history()
    
    # ==================== STATUS MESSAGE ====================

    status_message = ft.Text(
        "",
        size=14,
        weight=ft.FontWeight.W_500,
        visible=False,
    )

    def show_message(text: str, msg_type: str = "info"):
        """Display a status message above the session history."""
        color_map = {
            "success": ft.Colors.GREEN_700,
            "error": ft.Colors.RED_700,
            "warning": ft.Colors.ORANGE_700,
            "info": ft.Colors.BLUE_700,
        }
        status_message.value = text
        status_message.color = color_map.get(msg_type, ft.Colors.BLUE_700)
        status_message.visible = True
        status_message.update()

        # Auto-hide after 3 seconds
        def hide_message():
            time.sleep(3)
            try:
                status_message.visible = False
                status_message.update()
            except (AssertionError, AttributeError):
                pass

        threading.Thread(target=hide_message, daemon=True).start()
    
    # ==================== MAIN LAYOUT ====================
    
    # Header
    header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Time It", size=32, weight=ft.FontWeight.W_700, color=title_color),
                ft.Text(
                    "Track time on tasks with Timer or Log modes",
                    size=14,
                    color=accent_color,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(
                    height=1,
                    bgcolor=border_color,
                    margin=ft.margin.only(top=20),
                ),
            ],
            spacing=4,
        ),
        padding=ft.padding.only(left=24, top=66, bottom=0, right=24),
    )
    
    # Content area
    content = ft.Container(
        content=ft.Column(
            controls=[
                mode_panel,
                ft.Container(height=24),
                status_message,
                history_title_text,
                ft.Container(height=8),
                ft.Row(
                    controls=[history_today_button, history_week_button, history_all_button],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Container(height=8),
                history_search_field,
                ft.Container(height=10),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            history_total_label,
                            ft.Container(expand=True),
                            history_total_value,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    bgcolor=panel_bg,
                    border_radius=12,
                    border=ft.border.all(1.5, border_color),
                    shadow=drop_shadow,
                ),
                ft.Container(height=8),
                history_panel,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        padding=ft.padding.symmetric(horizontal=24, vertical=12),
    )
    
    # Main page layout
    return ft.Container(
        content=ft.Column(
            controls=[
                header,
                content,
            ],
            spacing=0,
            expand=True,
        ),
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#DDE9FB", "#FFFFFF"],
        ),
    )
