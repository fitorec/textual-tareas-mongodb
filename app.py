# app.py
from textual.app import App
from MainScreen import MainScreen

class TareasApp(App):

    CSS_PATH = "style.css" 

    BINDINGS = [
        ("q", "app.quit", "Quit")
    ]

    def on_mount(self):
        # Pantalla inicial
        self.push_screen(MainScreen())

    def action_quit(self):
        self.exit()


if __name__ == "__main__":
        import sys
        try:
            TareasApp().run()
        except Exception as e:
            print(f"\nFATAL: La aplicación ha fallado al iniciarse: {e}")
            print("Asegúrate de que MongoDB esté corriendo y tu archivo .env sea correcto.")
            sys.exit(1)
