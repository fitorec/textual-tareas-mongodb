# MainScreen.py
from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, DataTable, Static, Button
from textual.containers import Container, Grid
from textual.binding import Binding
from rich.console import Console

# Módulos locales del proyecto
from TareaFormScreen import TareaFormScreen
from TareaService import TareaService


class TareaModal(ModalScreen):
    def __init__(self, title, content, **kwargs):
        self.modal_title = title
        self.modal_content = content
        super().__init__(**kwargs)

    def compose(self):
        yield Container(
            Static(self.modal_title, classes="tarea_title"),
            Static(self.modal_content, classes="tarea_content"),
            Grid(
                Button("🗙  Cerrar", variant="default", id="btn_close", classes="btn_modal"),
                Button("✏️  Editar", variant="warning", id="btn_edit", classes="btn_modal"),
                Button("🗑  Borrar", variant="error", id="btn_delete", classes="btn_modal"),
                id="botones",
            ),
            id="modal_tarea",
        )

    def on_button_pressed(self, event):
        action = event.button.id.split('_').pop()
        self.dismiss({"action": action})

    def on_key(self, event):
        if event.key == "escape" or  event.key == "q":
            self.dismiss({"action": 'close'})


class MainScreen(Screen):
    BINDINGS = [
        Binding("c", "create_task", "Create"),
        Binding("r", "read_task", "Read"),
        Binding("u", "update_task", "Update"),
        Binding("d", "delete_task", "Delete"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(name="Tareas Mongo CRUD")
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
        """Obtiene el ID desde la primera columna (ID) del renglón seleccionado."""
        try:
            # Obtiene las coordenadas del cursor actual
            cursor_coord = self.table.cursor_coordinate
            if cursor_coord is None:
                self.app.notify("Ninguna tarea seleccionada.", severity="warning")
                return None

            cellID = self.table.get_cell_at(cursor_coord)
            try:
                return int(cellID)
            except (ValueError, TypeError):
                self.app.notify(f"ID inválido: {int(cellID)}", severity="error")

        except Exception as e:
            self.app.notify(f"Error obteniendo ID: {str(e)}", severity="error")
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

    async def action_read_task(self):
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

        # self.app.push_screen(
        #     TareaModal("Detalles de la Tarea", content)
        # )
        self.app.run_worker(self._worker_read_task(content), exclusive=True)

    async def _worker_read_task(self, content):
        result = await self.app.push_screen_wait(
            TareaModal("Detalles de la Tarea", content)
        )

        if result and result.get("action"):
            match result.get("action"):
                case 'edit':
                    self.action_update_task()
                case 'delete':
                    self.action_delete_task()


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
