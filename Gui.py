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
EJEMPLO = [("P1", 0, 8, 2), ("P2", 1, 4, 1), ("P3", 2, 9, 3), ("P4", 3, 5, 2)]

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
        superior.pack(fill="x", padx=10, pady=(10, 4))
        self._panel_procesos(superior)
        self._panel_algoritmo(superior)
        self._panel_gantt()
        self._panel_metricas()
 
    def _panel_procesos(self, padre):
        marco = ttk.LabelFrame(padre, text="1. Procesos")
        marco.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.v_pid = tk.StringVar(value="P1")
        self.v_llegada = tk.StringVar(value="0")
        self.v_rafaga = tk.StringVar()
        self.v_prio = tk.StringVar(value="0")
 
        campos = [("PID", self.v_pid), ("Llegada", self.v_llegada), ("Ráfaga", self.v_rafaga), ("Prioridad (opc.)", self.v_prio)]
        for i, (texto, var) in enumerate(campos):
            ttk.Label(marco, text=texto).grid(row=0, column=i, padx=4, pady=(6, 0))
            entrada = ttk.Entry(marco, textvariable=var, width=10, justify="center")
            entrada.grid(row=1, column=i, padx=4)
            entrada.bind("<Return>", lambda _e: self.agregar())
        ttk.Button(marco, text="Agregar", command=self.agregar).grid(row=1, column=4, padx=6)

        columnas = ("pid", "llegada", "rafaga", "prioridad")
        self.tv_proc = ttk.Treeview(marco, columns=columnas, show="headings", height=5)
        for col, texto in zip(columnas, ("PID", "Llegada", "Ráfaga", "Prioridad")):
            self.tv_proc.heading(col, text=texto)
            self.tv_proc.column(col, width=90, anchor="center")
        self.tv_proc.grid(row=2, column=0, columnspan=5, sticky="ew", padx=6, pady=6)
 
        botones = ttk.Frame(marco)
        botones.grid(row=3, column=0, columnspan=5, pady=(0, 6))
        ttk.Button(botones, text="Eliminar seleccionado", command=self.eliminar).pack(side="left", padx=4)
        ttk.Button(botones, text="Limpiar todo", command=self.limpiar).pack(side="left", padx=4)
        ttk.Button(botones, text="Cargar ejemplo", command=self.cargar_ejemplo).pack(side="left", padx=4)
 
    def _panel_algoritmo(self, padre):
        marco = ttk.LabelFrame(padre, text="2. Algoritmo y simulación")
        marco.pack(side="left", fill="y")
 
        ttk.Label(marco, text="Algoritmo:").grid(row=0, column=0, sticky="w", padx=6, pady=(8, 2))
        self.cb_alg = ttk.Combobox(marco, values=Schedulers.ALGORITMOS, state="readonly", width=26)
        self.cb_alg.current(0)
        self.cb_alg.grid(row=1, column=0, columnspan=2, padx=6)
        self.cb_alg.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_quantum())
 
        ttk.Label(marco, text="Quantum (solo Round Robin):").grid(row=2, column=0, sticky="w", padx=6, pady=(8, 2))
        self.v_quantum = tk.StringVar(value="3")
        self.sp_quantum = ttk.Spinbox(marco, from_=1, to=100, width=6, textvariable=self.v_quantum,
                                      state="disabled", justify="center")
        self.sp_quantum.grid(row=2, column=1, padx=6, pady=(8, 2))
 
        ttk.Label(marco, text="Retardo por unidad (ms):").grid(row=3, column=0, sticky="w", padx=6, pady=(8, 2))
        self.v_vel = tk.IntVar(value=250)
        ttk.Scale(marco, from_=30, to=800, variable=self.v_vel, orient="horizontal", length=150).grid(row=3, column=1, padx=6, pady=(8, 2))
 
        botones = ttk.Frame(marco)
        botones.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(botones, text="Simular", command=self.simular).grid(row=0, column=0, padx=3)
        ttk.Button(botones, text="Saltar animación", command=self.saltar).grid(row=0, column=1, padx=3)
        ttk.Button(botones, text="Comparar todos", command=self.comparar).grid(row=1, column=0, columnspan=2, pady=(6, 0))
 
    def _panel_gantt(self):
        marco = ttk.LabelFrame(self, text="3. Diagrama de Gantt")
        marco.pack(fill="x", padx=10, pady=4)
 
        self.canvas = tk.Canvas(marco, height=self.ALTO + 2 * self.MARGEN_Y + 20, background="white", highlightthickness=0)
        barra = ttk.Scrollbar(marco, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=barra.set)
        self.canvas.pack(fill="x", padx=6, pady=(6, 0))
        barra.pack(fill="x", padx=6)
 
        self.v_reloj = tk.StringVar(value="t = 0")
        ttk.Label(marco, textvariable=self.v_reloj, font=("TkDefaultFont", 10, "bold")).pack(anchor="e", padx=8)
 
    def _panel_metricas(self):
        marco = ttk.LabelFrame(self, text="4. Métricas de rendimiento")
        marco.pack(fill="both", expand=True, padx=10, pady=(4, 10))
 
        columnas = ("pid", "llegada", "rafaga", "fin", "retorno", "espera")
        encabezados = ("PID", "Llegada", "Ráfaga", "Finalización",
                       "Retorno = Fin - Llegada", "Espera = Retorno - Ráfaga")
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
        #Habilita el campo quantum solo cuando el algoritmo es Round Robin.
        estado = "normal" if self.cb_alg.get() == "Round Robin" else "disabled"
        self.sp_quantum.configure(state=estado)
 
    def agregar(self):
        pid = self.v_pid.get().strip() or f"P{len(self.procesos) + 1}"
        try:
            llegada = int(self.v_llegada.get())
            rafaga = int(self.v_rafaga.get())
            prioridad = int(self.v_prio.get() or 0)
        except ValueError:
            messagebox.showerror("Dato inválido", "Llegada, ráfaga y prioridad deben ser números enteros.")
            return
        if llegada < 0 or rafaga <= 0:
            messagebox.showerror("Dato inválido", "La llegada debe ser >= 0 y la ráfaga > 0.")
            return
        if pid.upper() == Schedulers.IDLE or any(p.pid == pid for p in self.procesos):
            messagebox.showerror("PID inválido", f"El PID '{pid}' está repetido o reservado.")
            return
 
        self.procesos.append(Proceso(pid, llegada, rafaga, prioridad))
        self._refrescar_tabla()
        self.v_pid.set(f"P{len(self.procesos) + 1}")
        self.v_rafaga.set("")
 
    def eliminar(self):
        seleccion = self.tv_proc.selection()
        if not seleccion:
            return
        pid = self.tv_proc.item(seleccion[0], "values")[0]
        self.procesos = [p for p in self.procesos if p.pid != str(pid)]
        self._refrescar_tabla()
 
    def limpiar(self):
        self._cancelar_animacion()
        self.procesos.clear()
        self._refrescar_tabla()
        self.canvas.delete("all")
        self.tv_res.delete(*self.tv_res.get_children())
        self.lbl_prom.configure(text="Ejecute una simulación para ver los promedios.")
        self.v_pid.set("P1")
 
    def cargar_ejemplo(self):
        self.procesos = [Proceso(*d) for d in EJEMPLO]
        self._refrescar_tabla()
        self.v_pid.set(f"P{len(self.procesos) + 1}")
 
    def _refrescar_tabla(self):
        self.tv_proc.delete(*self.tv_proc.get_children())
        for p in self.procesos:
            self.tv_proc.insert("", "end", values=(p.pid, p.llegada, p.rafaga, p.prioridad))

    # ===== Simulación y animación =========================================================
    def _leer_quantum(self):
        try:
            quantum = int(self.v_quantum.get())
            if quantum <= 0:
                raise ValueError
            return quantum
        except ValueError:
            messagebox.showerror("Quantum inválido", "El quantum debe ser un entero mayor que 0.")
            return None
 
    def simular(self):
        if not self.procesos:
            messagebox.showwarning("Sin procesos", "Agregue al menos un proceso.")
            return
        algoritmo = self.cb_alg.get()
        quantum = None
        if algoritmo == "Round Robin":
            quantum = self._leer_quantum()
            if quantum is None:
                return
 
        self._cancelar_animacion()
        segmentos, simulados = Schedulers.ejecutar(algoritmo, self.procesos, quantum)
        self._resultado = (segmentos, simulados, algoritmo)
        self._colores = {p.pid: PALETA[i % len(PALETA)] for i, p in enumerate(self.procesos)}
 
        self._preparar_lienzo(segmentos, algoritmo, quantum)
        self.tv_res.delete(*self.tv_res.get_children())
        self.lbl_prom.configure(text="Simulando...")
        self._animar()
 
    def _preparar_lienzo(self, segmentos, algoritmo, quantum):
        #Limpia el canvas y descompone los segmentos en unidades de tiempo
        self.canvas.delete("all")
        total = segmentos[-1][2]
        ancho = 2 * self.MARGEN_X + total * self.UNIDAD
        self.canvas.configure(scrollregion=(0, 0, ancho, self.ALTO + 2 * self.MARGEN_Y + 20))
        self.canvas.xview_moveto(0)
 
        # Cada unidad: (pid, t, inicio_segmento, fin_segmento, es_ultimo_segmento)
        self._unidades = [
            (pid, t, ini, fin, idx == len(segmentos) - 1)
            for idx, (pid, ini, fin) in enumerate(segmentos)
            for t in range(ini, fin)
        ]
        self._k = 0
        self.v_reloj.set("t = 0")
 
    def _animar(self):
        #Dibuja una unidad de tiempo y se reprograma hasta terminar
        if self._k >= len(self._unidades):
            self._job = None
            self._finalizar()
            return
        self._dibujar_unidad(self._k)
        self._k += 1
        self.v_reloj.set(f"t = {self._k}")
        self._job = self.after(int(self.v_vel.get()), self._animar)
 
    def saltar(self):
        #Termina de dibujar el Gantt al instante
        if self._job is None:
            return
        self.after_cancel(self._job)
        self._job = None
        while self._k < len(self._unidades):
            self._dibujar_unidad(self._k)
            self._k += 1
        self.v_reloj.set(f"t = {self._k}")
        self._finalizar()
 
    def _cancelar_animacion(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
 
    def _dibujar_unidad(self, k):
        pid, t, ini, fin, es_ultimo = self._unidades[k]
        x = self.MARGEN_X + t * self.UNIDAD
        y0, y1 = self.MARGEN_Y, self.MARGEN_Y + self.ALTO
        color = COLOR_IDLE if pid == Schedulers.IDLE else self._colores[pid]
 
        self.canvas.create_rectangle(x, y0, x + self.UNIDAD, y1, fill=color, outline=color)
 
        if t == ini:  # marca de tiempo al comenzar el segmento
            self.canvas.create_text(x, y1 + 14, text=str(ini))
 
        if t == fin - 1:  # al cerrar el segmento: borde, etiqueta y, si es el último, tiempo final
            xi = self.MARGEN_X + ini * self.UNIDAD
            xf = self.MARGEN_X + fin * self.UNIDAD
            self.canvas.create_rectangle(xi, y0, xf, y1, outline="black", width=2)
            if pid != Schedulers.IDLE or fin - ini >= 2:
                self.canvas.create_text((xi + xf) / 2, (y0 + y1) / 2, text=pid,
                                        font=("TkDefaultFont", 10, "bold"),
                                        fill="black" if pid == Schedulers.IDLE else "white")
            if es_ultimo:
                self.canvas.create_text(xf, y1 + 14, text=str(fin))
 
        # Mantiene visible la unidad que se está dibujando
        region = self.canvas.cget("scrollregion").split()
        ancho_total = float(region[2]) if len(region) == 4 else 1
        if x + self.UNIDAD > self.canvas.winfo_width() - 40:
            self.canvas.xview_moveto(max(0.0, (x - self.canvas.winfo_width() + 120) / ancho_total))

    # Métricas y resultados finales
    def _finalizar(self):
        #Al terminar la simulación muestra la tabla de métricas con sus cálculos
        _segmentos, simulados, algoritmo = self._resultado
        datos = Metrics.calcular(simulados)
 
        self.tv_res.delete(*self.tv_res.get_children())
        for f in datos["filas"]:
            self.tv_res.insert("", "end", values=(f["pid"], f["llegada"], f["rafaga"], f["fin"],
                                                  f["f_retorno"], f["f_espera"]))
        self.lbl_prom.configure(text=(
            f"Algoritmo: {algoritmo}\n"
            f"Espera promedio   = {datos['f_prom_espera']}\n"
            f"Retorno promedio  = {datos['f_prom_retorno']}\n"
            f"Utilización CPU   = {datos['utilizacion']:.1f} %"))
 
    def comparar(self):
        #Ejecuta todos los algoritmos con la misma lista y compara sus promedios
        if not self.procesos:
            messagebox.showwarning("Sin procesos", "Agregue al menos un proceso.")
            return
        quantum = self._leer_quantum()
        if quantum is None:
            return
 
        ventana = tk.Toplevel(self)
        ventana.title("Comparación de algoritmos")
        columnas = ("alg", "espera", "retorno")
        tabla = ttk.Treeview(ventana, columns=columnas, show="headings", height=len(Schedulers.ALGORITMOS))
        for col, texto, ancho in zip(columnas, ("Algoritmo", "Espera promedio", "Retorno promedio"),
                                     (220, 140, 140)):
            tabla.heading(col, text=texto)
            tabla.column(col, width=ancho, anchor="center")
        tabla.pack(padx=10, pady=10)
 
        mejor = None
        for nombre in Schedulers.ALGORITMOS:
            _seg, simulados = Schedulers.ejecutar(nombre, self.procesos, quantum)
            datos = Metrics.calcular(simulados)
            etiqueta = f"Round Robin (q={quantum})" if nombre == "Round Robin" else nombre
            tabla.insert("", "end", values=(etiqueta, f"{datos['prom_espera']:.2f}",
                                            f"{datos['prom_retorno']:.2f}"))
            if mejor is None or datos["prom_espera"] < mejor[1]:
                mejor = (etiqueta, datos["prom_espera"])
        ttk.Label(ventana, text=f"Menor espera promedio: {mejor[0]} ({mejor[1]:.2f})").pack(pady=(0, 10))
    

    

