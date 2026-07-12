from __future__ import annotations

import flet as ft

from .state import AppState


class ShareView(ft.Column):
    """Publish a text snippet or files to this device's board."""

    def __init__(self, page: ft.Page, state: AppState):
        super().__init__(expand=True, scroll=ft.ScrollMode.AUTO)
        self._page = page
        self._state = state

        self._text_field = ft.TextField(
            label="Text to publish",
            multiline=True,
            min_lines=4,
            max_lines=10,
        )
        self._file_picker = ft.FilePicker(on_result=self._on_files_picked)
        page.overlay.append(self._file_picker)

        self.controls = [
            ft.Container(
                ft.Column(
                    [
                        ft.Text("Share text", theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                        self._text_field,
                        ft.FilledButton(
                            "Publish text",
                            icon=ft.Icons.SEND,
                            on_click=self._publish_text,
                        ),
                        ft.Divider(),
                        ft.Text("Share files", theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                        ft.FilledTonalButton(
                            "Choose files…",
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=lambda _: self._file_picker.pick_files(
                                allow_multiple=True
                            ),
                        ),
                    ],
                    spacing=16,
                ),
                padding=16,
            )
        ]

    def _snack(self, message: str) -> None:
        self._page.open(ft.SnackBar(ft.Text(message)))

    def _publish_text(self, _event: ft.ControlEvent) -> None:
        text = (self._text_field.value or "").strip()
        if not text:
            self._snack("Enter some text")
            return
        self._state.board.add_text(text)
        self._text_field.value = ""
        self.update()
        self._snack("Text published")
        self._page.run_task(self._state.refresh)

    def _on_files_picked(self, event: ft.FilePickerResultEvent) -> None:
        if not event.files:
            return
        published = 0
        for file in event.files:
            if file.path:
                self._state.board.add_file(file.path)
                published += 1
        if published:
            self._snack(f"Files published: {published}")
            self._page.run_task(self._state.refresh)
