# MainScreen.py
from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, DataTable, Static, Button
from textual.containers import Container
from textual.binding import Binding

# Módulos locales del proyecto
from TareaFormScreen import TareaFormScreen
from TareaService import TareaService


class MessageScreen(ModalScreen):
    def __init__(self, title, content, **kwargs):
        self.modal_title = title
        self.modal_content = content
        super().__init__(**kwargs)

    def compose(self):
        yield Container(
            Static(self.modal_title, classes="title"),
            Static(self.modal_content, classes="content"),
            Button("Cerrar", variant="primary", id="close_btn"),
            id="modal_container",
        )

    def on_button_pressed(self, event):
        if event.button.id == "close_btn":
            self.dismiss()

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss()


class MainScreen(Screen):
    BINDINGS = [
        Binding("c", "create_task", "Create"),
        Binding("r", "read_task", "Read"),
        Binding("u", "update_task", "Update"),
        Binding("d", "delete_task", "Delete"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        self.table = DataTable(
            id="task_table",
            cursor_type="row",  # Selección por fila completa
            zebra_stripes=True,
        )
        self.table.add_column("ID", key="id")
        self.table.add_column("Título", key="titulo")
        self.table.add_column("Descripción", key="descripcion")
        self.table.add_column("Status", key="status")
        self.table.add_column("Fecha", key="fecha")
        yield self.table
        yield Footer()

    def on_mount(self):
        self.refresh_table()

    # ---------- tabla ----------
    def refresh_table(self):
        """Recarga todos los registros en la tabla."""
        # Limpia la tabla completamente
        self.table.clear()

        # Obtiene todas las tareas desde MongoDB
        tareas = TareaService.list()

        # Inserta cada fila en el DataTable
        for tarea in tareas:
            row_id = str(tarea["id"])  # key de la fila

            self.table.add_row(
                str(tarea["id"]),  # ID como string visible en la primera columna
                tarea["titulo"],
                tarea["descripcion"],
                tarea["status"],
                tarea["fecha"],
                key=row_id,
            )

        # Si hay filas, mueve el cursor al primer renglón
        if self.table.row_count > 0:
            self.table.move_cursor(row=0, column=0)

    def _get_selected_row_id(self):
        """Obtiene el row_key de la fila seleccionada usando la API oficial."""
        try:
            # Obtiene las coordenadas del cursor actual
            cursor_coord = self.table.cursor_coordinate
            if cursor_coord is None:
                self.app.notify("Ninguna tarea seleccionada.", severity="warning")
                return None

            # Usa la API oficial para obtener el row_key desde las coordenadas del cursor
            row_key, _ = self.table.coordinate_to_cell_key(cursor_coord)

            # ← FIX: RowKey se convierte correctamente a string con str()
            row_key_str = str(row_key)

            # Convierte a int si es posible
            try:
                return int(row_key_str)
            except ValueError:
                return row_key_str

        except Exception as e:
            self.app.notify(f"Error obteniendo ID de fila: {str(e)}", severity="error")
            return None


    # ---------- acciones (usando run_worker para poder await push_screen_wait) ----------

    def action_create_task(self):
        """Lanza el worker que abrirá el formulario y esperará su dismiss()."""
        self.app.notify("Abriendo formulario para crear...", severity="info")
        self.app.run_worker(self._worker_create_task(), exclusive=True)

    async def _worker_create_task(self):
        result = await self.app.push_screen_wait(TareaFormScreen(mode="create"))

        if not result or not result.get("ok"):
            self.app.notify("Operación cancelada.")
            return

        data = result["data"]
        nueva = TareaService.insert(data)
        if nueva:
            self.app.notify(f"Tarea {nueva['id']} creada.", severity="success")
        else:
            self.app.notify("Error al crear la tarea.", severity="error")

        self.refresh_table()

    def action_update_task(self):
        """Inicia worker para actualizar (abre modal y espera respuesta)."""
        self.app.run_worker(self._worker_update_task(), exclusive=True)

    async def _worker_update_task(self):
        task_id = self._get_selected_row_id()
        if task_id is None:
            return

        tarea = TareaService.get(task_id)
        if not tarea:
            self.app.notify("Tarea no encontrada.", severity="error")
            return

        result = await self.app.push_screen_wait(TareaFormScreen(mode="update", tarea=tarea))

        if not result or not result.get("ok"):
            self.app.notify("Actualización cancelada.")
            return

        data = result["data"]

        if TareaService.update(task_id, data):
            self.app.notify(f"Tarea {task_id} actualizada.", severity="success")
        else:
            self.app.notify("Error al actualizar.", severity="error")

        self.refresh_table()

    def action_read_task(self):
        """Mostrar modal de solo lectura."""
        task_id = self._get_selected_row_id()
        if task_id is None:
            return

        tarea = TareaService.get(task_id)
        if not tarea:
            self.app.notify("Tarea no encontrada.", severity="error")
            return

        content = (
            f"ID: {tarea['id']}\n"
            f"Título: {tarea['titulo']}\n\n"
            f"Descripción:\n{tarea['descripcion']}\n\n"
            f"Estatus: {tarea['status']}\n"
            f"Fecha: {tarea['fecha']}"
        )

        self.app.push_screen(MessageScreen("Detalles de la Tarea", content))

    def action_delete_task(self):
        """Borrar tarea seleccionada."""
        task_id = self._get_selected_row_id()
        if task_id is None:
            return

        if TareaService.delete(task_id):
            self.app.notify(f"Tarea {task_id} eliminada.", severity="warning")
            self.refresh_table()
        else:
            self.app.notify("Error al eliminar.", severity="error")
