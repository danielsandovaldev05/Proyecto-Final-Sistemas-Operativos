# Simulador de Planificador de Procesos (CPU Scheduler)
 
Proyecto final de Sistemas Operativos. Python 3.9+ y solo librería estándar (tkinter).

En este segundo commit en GitHub se agregaron los siguientes archivos para el funcionamiento del programa:

### 1) Schedulers.py:
el archivo ya existente desde el primer commit, este algoritmo se encarga de la definicion y la función de los diferentes algoritmos de planificación que hará el programa basado en los parámetros establecidos en las instrucciones de la tarea, estos algoritmos son el First-Come, First-Served (FCFS), el Shortest Job First (SJF), el Shortest Remaining Time First (SRTF), el Round Robin (RR) y los de prioridad (ya sean apropiativos o no aprotiativos).

### 2) Gui.py:
este nuevo archivo no esta completado actualmente, pero este archivo se encargará de proporcionar la interfaz para que el usuario interectue con el programa para probar la simulación de los algoritmos de planificación, proporcionando una interfaz intuitiva y atractiva para la vista del usuario.

### 3) Metric.py:
archivo que es de suma importancia para la interfaz de usuario, se tratara de un indicador cuantitativo que medira el rendimiento, la eficiencia y el cumplimiento de planificación de los diferentes Scheduers.

### 4) Models:
archivo que se encargara del programa en la parte del PCB (Process Control Block), en este se establece las multimples caracteristicas del proceso que quiere ingresar el usuario, es decir, que aqui se encuentra la lógica de los datos de entrada del usuario para que pueda ejecutarlos el programa.

## Estructura del Proyecto

```text
└── Proyecto Final Sistemas Operativos/ # Carpeta que almacena los archivos realizados en Python 
    ├── Gui.py              # Interfaz de usuario hecho en tkinter
    ├── Metrics.py          # Métricas de los algortimos de planificacion
    ├── Models.py           # Modelo del PCB
    ├── README.md           # Documentación acerca del programa (Donde estas leyendo esto actualmente)
    └── Schedulers.py       # Lógica de los algoritmo s de planificación (Schedulers)
```