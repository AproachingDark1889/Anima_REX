import tkinter as tk
from tkinter import messagebox

class AnimaGUI:
    """
    Interfaz gráfica para monitorizar el estado de conexión y estrategia de Ánima REX.
    """
    def __init__(self, master, reconectar_callback=None, obtener_nivel_callback=None):
        self.master = master
        self.reconectar_callback = reconectar_callback
        self.obtener_nivel_callback = obtener_nivel_callback

        # Configuración de ventana
        self.master.title("Ánima - Estado de Conexión y Estrategia")

        # Etiqueta de estado de conexión
        self.label_estado = tk.Label(
            self.master,
            text="Estado: Desconectado",
            fg="red",
            font=("Arial", 12)
        )
        self.label_estado.pack(pady=10)

        # Etiqueta de nivel de Martingala
        self.label_nivel = tk.Label(
            self.master,
            text="Nivel Actual: 0",
            font=("Arial", 12)
        )
        self.label_nivel.pack(pady=10)

        # Botón de reconexión
        self.boton_reconectar = tk.Button(
            self.master,
            text="🔄 Reconectar",
            command=self.reconectar,
            font=("Arial", 12)
        )
        self.boton_reconectar.pack(pady=20)

    def actualizar_nivel(self):
        """
        Actualiza el nivel de Martingala mostrado en la GUI cada 3 segundos.
        """
        if self.obtener_nivel_callback:
            try:
                nivel = self.obtener_nivel_callback()
                self.label_nivel.config(text=f"Nivel Actual: {nivel}")
            except Exception:
                # En caso de error, no interrumpe el bucle de actualización
                pass
        self.master.after(3000, self.actualizar_nivel)

    def reconectar(self):
        """
        Intenta reconectar usando el callback proporcionado y actualiza el estado.
        """
        if self.reconectar_callback:
            try:
                exito = self.reconectar_callback()
            except Exception as e:
                exito = False
            if exito:
                self.set_estado("Reconectado", "green")
                messagebox.showinfo("Reconexión", "Reconexión completada exitosamente.")
            else:
                self.set_estado("Desconectado", "red")
                messagebox.showerror("Reconexión", "La reconexión falló.")
        else:
            self.set_estado("Reconectado", "green")
            messagebox.showinfo("Reconexión", "Reconexión completada exitosamente.")

    def set_estado(self, estado, color):
        """
        Actualiza la etiqueta de estado con un texto y color específicos.
        """
        self.label_estado.config(text=f"Estado: {estado}", fg=color)
