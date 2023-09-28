import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import time
import threading
from collections import deque
#Autor:juan carlos fernandez calvo
#Funcionalidad: Lectura de datos por el puerto COM3 e impresion en pantalla.
#Version final del programa desarrollado durante las practicas profesionales en la empresa Omanxus.

class Form1:
    def __init__(self, root):
        self.root = root
        self.root.title("Conexión en directo")
        self.root.geometry("1400x1160")
        #self.root.iconbitmap('icono.ico')

        self.canvas = tk.Canvas(root, width=300, height=82)
        self.canvas.pack(side="top")
        #self.canvas.place(x=10, y=40)

        self.load_and_display_image("imagen_fondo.png")

        self.right_frame = tk.Frame(root)
        self.right_frame.pack(side="top")

        self.label1 = tk.Label(self.right_frame, text="Datos de la balanza:", font=("Helvetica", 20))
        self.label1.pack()

        self.data_label = tk.Label(self.right_frame, text="0.00", font=("Helvetica", 30))
        self.data_label.pack()

        self.kg_label = tk.Label(self.right_frame, text="Kg", font=("Helvetica", 15))
        self.kg_label.pack()

        self.max_weight_label = tk.Label(self.right_frame, text="Peso máximo aceptado:", font=("Helvetica", 15))
        self.max_weight_label.pack()
        self.max_weight_entry = ttk.Entry(self.right_frame, font=("Helvetica", 15))
        self.max_weight_entry.pack()

        self.min_weight_label = tk.Label(self.right_frame, text="Peso mínimo aceptado:", font=("Helvetica", 15))
        self.min_weight_label.pack()
        self.min_weight_entry = ttk.Entry(self.right_frame, font=("Helvetica", 15))
        self.min_weight_entry.pack()

        self.confirm_button = tk.Button(self.right_frame, text="Validar", command=self.validate_values, font=("Helvetica", 15,"bold"))
        self.confirm_button.pack()

        self.serial_port = serial.Serial("COM3", 19200, bytesize=8, parity='N', stopbits=1, timeout=0)
        self.serial_port.timeout = 1

        self.tree = ttk.Treeview(self.right_frame, columns=("Cantidad", "Fecha", "Time", "Weight", "Ajuste"), show="headings")

        tree_scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side="right", fill="y", padx=15)

        num_visible_rows = 15  # Ajusta este valor según tus necesidades

        # Ajusta la altura de las filas
        row_height = 10  # Ajusta este valor según tus preferencias
        self.tree["height"] = num_visible_rows
        self.tree["show"] = "headings"  # Muestra solo las cabeceras

        self.tree.column("Cantidad", width=225,anchor="center")
        self.tree.column("Fecha", width=225, anchor="center")
        self.tree.column("Time", width=210,anchor="center")
        self.tree.column("Weight", width=225,anchor="center")
        self.tree.column("Ajuste", width=225,anchor="center")

        self.tree.heading("Cantidad", text="Cantidad")
        self.tree.heading("Fecha", text="Fecha")
        self.tree.heading("Time", text="Hora")
        self.tree.heading("Weight", text="Peso (Kg)")
        self.tree.heading("Ajuste", text="Se ajusta al Rango")
        self.tree.pack(side="bottom")

        self.thread = threading.Thread(target=self.read_serial_data)
        self.thread.daemon = True
        self.thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.max_weight = None
        self.min_weight = None
        self.row_counter = 1
        self.above_max_count = 0
        self.below_min_count = 0

        self.last_three_weights = deque(maxlen=3)  # Deque para almacenar los últimos 3 pesos iguales.

        generate_file_button = tk.Button(self.right_frame, text="Generar Archivo", command=self.generate_file, font=("Helvetica", 15, "bold"))
        generate_file_button.pack( padx=30)
        generate_file_button.place(x=250, y=230)

        # Botón para borrar la selección
        self.delete_button = tk.Button(self.right_frame, text="Borrar Selección", command=self.delete_selected_item, font=("Helvetica", 15,"bold"))
        self.delete_button.pack( padx=30)
        self.delete_button.place(x=800, y=230)

        # Inicia el temporizador para verificar la falta de datos
        #self.start_data_timer()

    def load_and_display_image(self, image_path):
        try:
            self.image = tk.PhotoImage(file="imagen_fondo.png")
            self.canvas.create_image(0, 0, anchor="nw", image=self.image)
        except Exception as ex:
            print(f"Error al cargar la imagen: {ex}")

    def read_serial_data(self):
        # Variable para mantener el peso anterior.
        previous_weight = None

        while True:
            try:
                if self.serial_port.isOpen():
                    data = self.serial_port.read_all().decode('utf-8').strip()
                    data = data.replace("$", "0")
                    data = data.replace("000", "")
                    data = data.replace("100", "")
                    #data = data.replace("1000", "")
                    #data = data.replace("10000", "")
                    #data = data.replace("1", "1")
                    data = ''.join(filter(str.isdigit, data))

                    if data:
                        weight = float(data) / 100
                        current_date = time.strftime("%Y-%m-%d")

                        # Verifica si el peso actual es diferente al peso anterior.
                        if weight != previous_weight or weight == 0:
                            self.last_three_weights.append(weight)  # Agrega el peso a la deque

                            if len(self.last_three_weights) == 3 and all(w == weight for w in self.last_three_weights):
                                # Si son iguales, agrégalo al TreeView para no imprimir pesos oscilantes.
                                if weight != 0:  # Verifica que el peso no sea igual a 0 antes de agregarlo al TreeView
                                    ajuste = self.check_weight_range(weight)
                                    self.add_to_tree(self.row_counter, current_date, time.strftime("%H:%M:%S"), f'{weight:.2f}', ajuste)
                                    self.row_counter += 1

                                previous_weight = weight

                        self.update_label(f'{weight:.2f}')
                            #self.serial_port.flush()
                    

            except Exception as ex:
                print(ex)
            time.sleep(0.2)

    def update_label(self, data):
        self.data_label.config(text=data)
        self.root.update()
        

    def on_closing(self):
        if self.serial_port.isOpen():
            self.serial_port.close()
        self.root.destroy()

    def validate_values(self):
        max_weight_str = self.max_weight_entry.get()
        min_weight_str = self.min_weight_entry.get()

        if max_weight_str == "" or min_weight_str == "":
            messagebox.showerror("Error", "Por favor, ingrese valores para peso máximo y mínimo.")
        else:
            try:
                self.max_weight = float(max_weight_str)
                self.min_weight = float(min_weight_str)
            except ValueError:
                messagebox.showerror("Error", "Por favor, ingrese valores válidos para peso máximo y mínimo.")

    def check_weight_range(self, data):
        try:
            if self.max_weight is not None and self.min_weight is not None:
                if self.min_weight <= data <= self.max_weight:
                    self.data_label.config(text=f'{data:.2f} (Dentro del rango)')
                    return "Si"
                elif data > self.max_weight:
                    self.above_max_count += 1
                    self.data_label.config(text=f'{data:.2f} (Por encima del rango)')
                    return "Por encima del rango"
                elif data < self.min_weight:
                    self.below_min_count += 1
                    self.data_label.config(text=f'{data:.2f} (Por debajo del rango)')
                    return "Por debajo del rango"

            if self.max_weight is None or self.min_weight is None:
                return "No especificado"

        except ValueError:
            pass
            return "Error"

    def add_to_tree(self, cantidad, date_str, time_str, weight_str, ajuste):
        if ajuste == "Dentro del rango":
            bg_color = "green"
        else:
            bg_color = "red"

        self.tree.insert("", "end", values=(cantidad, date_str, time_str, weight_str, ajuste), tags=(bg_color,))

    def generate_file(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])

            if file_path:
                with open(file_path, "w") as file:
                    file.write("Cantidad\tFecha\t\t\tHora\t\t\tPeso (Kg)\t\tSe ajusta al Rango\n")

                    for item in self.tree.get_children():
                        values = self.tree.item(item, "values")
                        file.write(f"{values[0]}\t\t{values[1]}\t\t{values[2]}\t\t{values[3]}\t\t\t{values[4]}\n")

                messagebox.showinfo("Archivo Generado", "Se ha generado el archivo de texto correctamente.")
        except Exception as ex:
            messagebox.showerror("Error", f"Error al generar el archivo: {ex}")

    def delete_selected_item(self):
        selected_item = self.tree.selection()
        if selected_item:
            self.tree.delete(selected_item)
        else:
            messagebox.showinfo("Nada seleccionado", "Por favor, seleccione un elemento para borrar.")


if __name__ == "__main__":
    root = tk.Tk()
    app = Form1(root)
    root.mainloop()
