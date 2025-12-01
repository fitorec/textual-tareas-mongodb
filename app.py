#!/usr/bin/env python3.14
import sys
import argparse
from textual.app import App
from MainScreen import MainScreen
from TareaService import TareaService


class TareasApp(App):
    CSS_PATH = "style.css" 
    BINDINGS = [
        ("q", "app.quit", "Quit")
    ]

    def on_mount(self):
        # Pantalla Pricipal e Inicial
        self.push_screen(MainScreen())

    def action_quit(self):
        self.exit()

def show_conky():
    tareas = TareaService.list()
    font = "DejaVu Sans Mono";
    color_date = "white"

    for t in tareas:
        sp = 30 - len(t['titulo'])
        if sp < 1:
            sp = 1
        sp = "." * sp
        print(
            f"${{color green}}{t['id']}${{color}} "
            f"${{color yellow}}{t['titulo']}${{color}}"
            f"${{color gray}}{sp}${{color}}"
        )
        sp = (" " * 30)
        print(
            f"   ${{font {font}:size=10}}{sp}"
            f"${{color {color_date}}}{t['fecha']}${{color}}${{font}}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gestor de Tareas')
    parser.add_argument('--conky', action='store_true', help='Modo salida para Conky')
    args = parser.parse_args()
    if args.conky:
        # Modo Conky completo
        show_conky()
    else:
        # Modo aplicación Textual normal
        try:
            TareasApp().run()
        except Exception as e:
            print(f"\nFATAL: La aplicación ha fallado al iniciarse: {e}")
            print("Asegúrate de que MongoDB esté corriendo y tu archivo .env sea correcto.")
            sys.exit(1)
