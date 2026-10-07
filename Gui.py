#Interfaz de usuario para la simulación de algoritmos de planificación de procesos.

import tkinter as tk
from tkinter import ttk, messagebox

import Metrics
import Schedulers
from Models import Proceso

PALETA = ["#1071d9", "#f26a2b", "#ff0004", "#44f6d5", "#40e32a",
          "#edc948", "#e577c6", "#ff9da7", "#714d37", "#bab0ac"]

COLOR_IDLE = "#e0e0e0"

# Ejemplo (PID, llegada, duracion, prioridad)
EJEMPLO_PROCESOS = [("P1", 0, 8, 2), ("P2", 1, 4, 1), ("P3", 2, 9, 3), ("P4", 3, 5, 2)]

class App(tk.Tk):
    UNIDAD = 34 #Ancho de pixeles de una unidad de tiempo en el Gantt
    MARGEN_X = 20
    MARGEN_Y = 20
    ALTO = 50 # alto de las barras

    def __init__(self):
        super().__init__()
        self.title("Simulador de planificación de procesos (CPU Scheduler)")
        self.geometry("1100x800")
        self.resizable(False, False)

        self.procesos = []  # lista de Proceso ingresados por el usuario
        self._job = None # id del after() de la animación en curso
        self._unidades = [] # lista de rectángulos del Gantt
        self._k = 0 # indice de la unidad de tiempo que se está animando
        self._resultado = None # tupla (segmentos, procesos) devuelta por el planificador
        self._colores = {} # diccionario pid -> color

        self._crear_widgets()

    #==== CONSTRUCCION DE LA INTERFAZ ========================================================== 

    def _crear_widgets(self):
        superior = ttk.Frame(self)
        superior.pack(fill="x", padx = 10, pady = (10, 4))
        self._panel_procesos(superior)
        self._panel_algoritmo(superior)
        self._panel_gantt()
        self._panel_metricas()

    def _panel_procesos(self, contenedor):
        marco = ttk.LabelFrame(contenedor, text="Procesos")
        marco.pack(side="left", fill = "both", expand = True, padx = (0, 8))

        self.v_pid = tk.StringVar(value="P1")
        self.v_llegada = tk.StringVar(value="0")
        self.v_duracion = tk.StringVar()
        self.v_prioridad = tk.StringVar(value="0")

        campos = [("PID", self.v_pid), ("Llegada", self.v_llegada), ("Duracion", self.v_duracion), ("Prioridad", self.v_prioridad)]
        for i, (texto, var) in enumerate(campos):
            ttk.Label(marco, text=texto).grid(row = 0, column = i, padx = 4, pady = (6, 0))
            entrada = ttk.Entry(marco, textvariable = var, width = 10, justify = "center")
            entrada.grid(row = 1, column = i, padx = 4, pady = 4)
            entrada.bind("<Return>", lambda _e: self.agregar())
        ttk.Button(marco, text="Agregar", command=self.agregar).grid(row=1, column=4, padx=6, pady=4)

        columnas = ("PID", "Llegada", "Duracion", "Prioridad")
        self.tv_procesos = ttk.Treeview(marco, columns = columnas, show="headings", height=5)
        for col, texto in zip(columnas, ("PID", "Llegada", "Duracion", "Prioridad")):
            self.tv_procesos.heading(col, text = texto)
            self.tv_procesos.column(col, width = 80, anchor="center")
        self.tv_procesos.grid(row=3, column=0, columnspan=5, stick="ew", padx = 6, pady = 6)

        botones = ttk.Frame(marco)
        botones.grid(row = 3, column = 0, columnspan = 5, pady = (0, 6))
        ttk.Button(botones, text = "Eliminar seleccionado", command = self.eliminar).pack(side="left", padx = 4)
        ttk.Button(botones, text = "Limpiar lista", command = self.limpiar).pack(side="left", padx = 4)
        ttk.Button(botones, text = "Cargar ejemplo", command = self.cargar_ejemplo).pack(side="left", padx = 4)

    def _panel_algoritmico(self, padre):
        marco = ttk.LabelFrame(padre, text="Algoritmo y simulación")
        marco.pack(side="left", fill="y")

        ttk.Label(marco, text="Algoritmo: ").grid(row = 0, column = 0, sticky = "w", padx = 6, pady = (8,2))
        self.cb_alg = ttk.Combobox(marco, values =  Schedulers.ALGORITMOS, state = "readonly", width = 26)
        self.cb_alg.current(0)
        self.cb_alg.grid(row = 1, column = 0, columnspan = 2, padx = 6)
        self.cb_alg.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_quantum())

        ttk.Label(marco, text="Quantum (Round Robin): ").grid(row = 2, column = 0, sticky = "w", padx = 6, pady = (8,2))
        self.v_quantum = tk.StringVar(value="3")
        self.sp_quantum = ttk.Spinbox(marco, from_=1, to=100, textvariable=self.v_quantum, width = 6, state = "disabled", justify = "center")
        self.sp_quantum.grid(row = 2, column = 1, padx = 6, pady = (8, 2))

        ttk.Label(marco, text="Velocidad de animación (ms): ").grid(row = 3, column = 0, sticky = "w", padx = 6, pady = (8,2))
        self.v_velocidad = tk.IntVar(value=250)
        ttk.Scale(marco, from_=30, to=800, variable=self.v_velocidad, orient="horizontal", length = 150).grid(row = 3, column = 1, padx = 6, pady = (8, 2))

        botones = ttk.Frame(marco)
        botones.grid(row = 4, column = 0, columnspan = 2, pady = 10)
        ttk.Button(botones, text = "Simular", command = self.simular).grid(row = 0, column = 0, padx = 3)
        ttk.Button(botones, text = "Saltar animación", command = self.saltar_animacion).grid(row = 0, column = 1, padx = 3)
        ttk.Button(botones, text = "Comparar todos", command = self.comparar).grid(row = 0, column = 0, columnspan = 2, pady = 3)

    def _panel_gantt(self):
        marco = ttk.LabelFrame(self, text="Diagrama de Gantt")
        marco.pack(fill="x", padx = 10, pady = 4)

        self.canvas = tk.Canvas(marco, height = self.ALTO + 2 * self.MARGEN_Y + 20, bg = "white", highlightthickness = 0)
        barra = ttk.Scrollbar(marco, orient="horizontal", command = self.canvas.xview)
        self.canvas.configure(xscrollcommand = barra.set)
        barra.pack(fill="x", padx = 6, pady = (6, 0))
        barra.pack(fill="x", padx = 6)

        self.v_reloj = tk.StringVar(value="t = 0")
        ttk.Label(marco, textvariable = self.v_reloj, font = ("TkDefaultFont", 10, "bold")).pack(anchor = "e", padx = 8)

    def _panel_metricas(self):
        marco = ttk.LabelFrame(self, text="Métricas de rendimiento")
        marco.pack(fill="both", expand = True, padx = 10, pady = (4,10))

        columnas = ("pid", "llegada", "rafaga", "fin", "retorno", "espera")
        encabezados = ("PID", "Llegada", "Ráfaga", "Finalización", "Retorno = Fin - Llegada", "Espera = Retorno - Ráfaga")
        anchos = (70, 80, 80, 100, 200, 220)
        self.tv_res = ttk.Treeview(marco, columns=columnas, show="headings", height=6)
        for col, texto, ancho in zip(columnas, encabezados, anchos):
            self.tv_res.heading(col, text=texto)
            self.tv_res.column(col, width=ancho, anchor="center")
        self.tv_res.pack(fill="both", expand=True, padx=6, pady=6)
 
        self.lbl_prom = ttk.Label(marco, text="Ejecute una simulación para ver los promedios.",
                                  justify="left", font=("TkFixedFont", 10))
        self.lbl_prom.pack(anchor="w", padx=8, pady=(0, 8))

    # ==== Ingreso y gestión de procesos =========================================================

    def _actualizar_quantum(self):
        #Habilita el spinbox de quantum solo cuando el algorimo seleccionado es Round Robin.
        estado = "normal" if self.cb_alg.get() == "Round Robin" else "disabled"
        self.sp_quantum.configure(state = estado)

    def agregar(self):
        pid = self.v_pid.get().strip() or f"P{len(self.procesos) + 1}"
        try:
            llegada = int(self.v_llegada.get())
            duracion = int(self.v_duracion.get())
            prioridad = int(self.v_prioridad.get())
        except ValueError:
            messagebox.showerror("Error", "Llegada, Duración y Prioridad deben ser números enteros.")
            return
        if llegada < 0 or duracion <= 0:
            messagebox.showerror("Error", "Llegada debe ser >= 0 y Duración > 0.")
            return
        if pid.upper() == Schedulers.IDLE or any(p.pid == pid for p in self.procesos):
            messagebox.showerror("Error", f"PID '{pid}' no es válido o ya existe.")
            return

        self.procesos.append(Proceso(pid, llegada, duracion, prioridad))
        self._refresh_procesos()
        self.v_pid.set(f"P{len(self.procesos) + 1}")
        self.v_duracion.set("")

    def eliminar(self):
        seleccion = self.tv_procesos.selection()
        if not seleccion:
            messagebox.showinfo("Info", "Seleccione un proceso para eliminar.")
            return
        pid = self.tv_procesos.item(seleccion[0], "values")[0]
        self.procesos = [p for p in self.procesos if p.pid != str(pid)]
        self._refresh_procesos()

    def limpiar(self):
        self._cancelar_animacion()
        self.procesos.clear()
        self._refresh_procesos()
        self.canvas.delete("all")
        self.tv_res.delete(*self.tv_res.get_children())
        self.lbl_prom.configure(text="Ejecute una simulación para ver los promedios.")
        self.v_pid.set("P1")

    def cargar_ejemplo(self):
        self.procesos = [Proceso(*d) for d in EJEMPLO_PROCESOS]
        self._refresh_procesos()
        self.v_pid.set(f"P{len(self.procesos) + 1}")

    def _refresh_procesos(self):
        self.tv_procesos.delete(*self.tv_procesos.get_children())
        for p in self.procesos:
            self.tv_procesos.insert("", "end", values=(p.pid, p.llegada, p.duracion, p.prioridad))

    # ===== Simulación y animación =========================================================

    

    

