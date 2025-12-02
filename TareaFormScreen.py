# TareaFormScreen.py
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Input, TextArea, Select, Button, Static
from textual.containers import Container, Grid
from datetime import date
import pendulum

# 🔥 Importamos tu modelo Pydantic
from TareaSchema import TareaSchema
from pydantic import ValidationError


class TareaFormScreen(ModalScreen):
    """Formulario para crear/editar tarea — devuelve dict via dismiss(resultado)."""
    CSS_PATH = "style.css"

    BINDINGS = [("escape", "cancel", "Cancelar")]

    STATUS_OPTIONS = [
        ("Pendiente", "pendiente"),
        ("En Proceso", "en_progreso"),
        ("Hecho", "hecho"),
    ]

    def __init__(self, mode: str = "create", tarea: dict | None = None, **kwargs):
        self.mode = mode
        self.tarea = tarea or {}
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        # fecha inicial
        if self.mode == "update" and self.tarea.get("fecha"):
            try:
                initial_date = pendulum.parse(self.tarea["fecha"])
            except:
                initial_date = pendulum.today().add(weeks=1)
        else:
            initial_date = pendulum.today().add(weeks=1)

        initial_title = self.tarea.get("titulo", "")
        initial_desc = self.tarea.get("descripcion", "")
        initial_status = self.tarea.get("status", "pendiente")

        initial_year = str(initial_date.year)
        initial_month = f"{initial_date.month:02}"
        initial_day = f"{initial_date.day:02}"

        yield Grid(
            Input(initial_title, placeholder="Título...", id="titulo_input", classes="input_label"),
            TextArea(initial_desc, placeholder="Descripción...", id="descripcion_textarea"),
            Container(
                Select(self.STATUS_OPTIONS, value=initial_status, prompt="Estatus", id="select_status"),
                Grid(
                    Static("FECHA", id="date_label_static"),
                    Input(initial_year, placeholder="AAAA", id="date_year", classes="fecha_input", type="integer"),
                    Input(initial_month, placeholder="MM", id="date_month", classes="fecha_input", type="integer"),
                    Input(initial_day, placeholder="DD", id="date_day", classes="fecha_input", type="integer"),
                    id="date_container",
                ),
                id="status_date_container",
            ),
            Container(
                Button("Aceptar", variant="default", id="btn_accept", disabled=True),
                Button("Cancelar", variant="error", id="btn_close"),
                id="button_container",
            ),
            id="form_grid",
        )

    def on_mount(self):
        self._check_form_validity()

    def on_input_changed(self, _):
        self._check_form_validity()

    def on_text_area_changed(self, _):
        self._check_form_validity()

    def on_select_changed(self, _):
        self._check_form_validity()

    def _is_date_valid(self, year, month, day) -> bool:
        try:
            date(int(year or 0), int(month or 0), int(day or 0))
            return True
        except ValueError:
            return False

    def _check_form_validity(self):
        title = self.query_one("#titulo_input").value.strip()
        desc = self.query_one("#descripcion_textarea").text.strip()
        status = self.query_one("#select_status").value
        year = self.query_one("#date_year").value
        month = self.query_one("#date_month").value
        day = self.query_one("#date_day").value
        btn = self.query_one("#btn_accept")
        is_valid = bool(title) and bool(desc) and (status is not None) and self._is_date_valid(year, month, day)
        btn.disabled = not is_valid
        btn.variant = "success" if is_valid else "default"

    # ACCIONES
    def action_cancel(self):
        self.dismiss({"ok": False})

    def on_button_pressed(self, event):
        if event.button.id == "btn_close":
            self.action_cancel()
        elif event.button.id == "btn_accept":
            if not self.query_one("#btn_accept").disabled:
                self._submit_form()

    def _submit_form(self):
        # --- 1) Construcción de fecha (sin tocar lo que ya tenía tu implementación)
        try:
            year = int(self.query_one("#date_year").value)
            month = int(self.query_one("#date_month").value)
            day = int(self.query_one("#date_day").value)
            fecha = date(year, month, day).strftime("%Y-%m-%d")
        except Exception:
            self.app.notify("Error en la fecha.", severity="error")
            return

        # --- 2) Construir dict tal como antes
        data = {
            "titulo": self.query_one("#titulo_input").value,
            "descripcion": self.query_one("#descripcion_textarea").text.strip(),
            "status": str(self.query_one("#select_status").value),
            "fecha": fecha,
        }

        if self.mode == "update":
            data["id"] = self.tarea.get("id")
        else:
            # Pydantic exige id en tu modelo, para creación usamos 0 (lo asignas luego)
            data["id"] = 0
        try:
            TareaSchema(**data)   # si falla: entra al except
        except ValidationError as e:
            # Convertimos errores en líneas legibles
            mensajes = "\n".join(err["msg"] for err in e.errors())
            self.app.notify(mensajes, severity="error")
            return

        # --- 4) Si todo es correcto, se devuelve tal como antes
        self.dismiss({"ok": True, "data": data})
