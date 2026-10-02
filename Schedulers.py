#Algoritmos de planificación de CPU

# Todas las funciones son puras: es decir que reciben la lista original de procesos,
#trabajan sobre copias y devuelven una tupla de segmentos y procesos:

#Segmentos: lista de (pid, inicio, fin) en orden cronológico. Es la base del diagrama de Gantt. Los huecos sin trabajo se marcan con "IDLE".

#Procesos: copias con `finalizacion` ya calculada, en el orden original.

from collections import deque

IDLE = "IDLE"

ALGORITMOS = [
    "FCFS",
    "SJF",
    "SRTF",
    "RR",
    "Prioridad (no apropiativo)",
    "Prioridad (apropiativo)"
]

def _fusionar(segmentos):
    # Une segmentos contiguos del mismo proceso: (P1,0,1)+(P1,1,3) -> (P1,0,3).
    resultado = []
    for pid, inicio, fin in segmentos:
        if resultado and resultado [-1][0] == pid and resultado [-1][2] == inicio:
            resultado[-1] = (pid, resultado[-1][1], fin)
        else:
            resultado.append((pid, inicio, fin))
    return resultado

def fcfs(procesos):
    # Algoritmo First-Come, First-Served (no apropiativo).
    #Los procesos se atienden estrictamente por orden de llegada y cada uno corre hasta terminar.
    # #Si la CPU queda libre esperando una llegada, se registra un segmento IDLE.

    ps = [p.copia() for p in procesos]
    t, segmentos = 0, []
    #sorted() es estable: ante igual llegada se respeta el orden de ingreso
    for p in sorted(ps, key=lambda p: p.llegada):
        if t < p.llegada:
            segmentos.append((IDLE, t, p.llegada))
            t = p.llegada
        segmentos.append((p.pid, t, t+p.rafaga))
        t += p.rafaga
        p.restante = 0
        p.finalizacion = t
    return _fusionar(segmentos), ps

def _por_clave(procesos, clave, apropiativo):
    #Planificador generico

    #Sirve para SFJ/SRTF (clave = tiempo restante) y prioridades
    #(clave = prioridad).
    #Desempate: menor tiempo de llegada y, si persiste, el orden de ingreso.

    #No apropiativo: el elegido corre hasta terminar.

    # Apropiativo: el elegido corre hasta que termina o hasta la proxima
    # llegada, momento en que se reevalúa quién debe tener la CPU (una
    # reevaluación entre llegadas sería redundante: el proceso en ejecución
    # solo mejora su clave al avanzar).

    ps = [p.copia() for p in procesos]
    t, segmentos = 0, []
    pendientes = len(ps)

    while pendientes:
        listos = [p for p in ps if p.restante > 0 and p.llegada <= t]

        if not listos: # CPU ociosa hasta la siguiente entrada
            proxima = min(p.llegada for p in ps if p.restante > 0)
            segmentos.append((IDLE, t, proxima))
            t = proxima
            continue

        elegido = min(listos, key=lambda p: (clave(p), p.llegada))

        if apropiativo:
            futuras = [p.llegada for p in ps if p.restante > 0 and p.llegada > t]
            limite = min(futuras) if futuras else t + elegido.restante
            duracion = min(elegido.restante, limite - t)
        else:
            duracion = elegido.restante

        segmentos.append((elegido.pid, t, t + duracion))
        t += duracion
        elegido.restante -= duracion
        if elegido.restante == 0:
            elegido.finalizacion = t
            pendientes -= 1

    return _fusionar(segmentos), ps

def sjf(procesos, apropiativo=False):
    # Algoritmo Shortest Job First (no apropiativo) o Shortest Remaining Time First (apropiativo).
    # Se atiende primero al proceso con menor tiempo de ejecución restante.
    return _por_clave(procesos, lambda p: p.restante, apropiativo)

def prioridad(procesos, apropiativo=False):
    # Algoritmo de planificación por prioridad (no apropiativo o apropiativo).
    # Se atiende primero al proceso con mayor prioridad (menor valor numérico).
    return _por_clave(procesos, lambda p: p.prioridad, apropiativo)

def round_robin(procesos, quantum):
    #Round Robin (apropiativo) con quantum ingresado por el usuario.
 
    #Convención de empates: si un proceso llega
    #justo en el instante en que otro agota su quantum, el que llega entra a la
    #cola ANTES que el proceso interrumpido.

    if quantum <= 0:
        raise ValueError("Quantum debe ser mayor a 0")

    ps = [p.copia() for p in procesos]
    por_llegar = deque(sorted(ps, key=lambda p: p.llegada)) #orden estable
    cola = deque()
    t, segmentos, terminados = 0, [], 0

    def admitir(hasta):
        #Admite a la cola todos los procesos que llegan hasta el instante "hasta".
        while por_llegar and por_llegar[0].llegada <= hasta:
            cola.append(por_llegar.popleft())

    while terminados < len(ps):
        admitir(t)

        if not cola:
            proxima = por_llegar[0].llegada
            segmentos.append((IDLE, t, proxima))
            t = proxima
            continue

        p = cola.popleft()
        duracion = min(quantum, p.restante)
        segmentos.append((p.pid, t, t + duracion))
        t += duracion
        p.restante -= duracion

        admitir(t) #los que llegaron durante la ejecucion entran primero
        if p.restante > 0:
            cola.append(p) #vuelve al final de la cola
        else:
            p.finalizacion = t
            terminados += 1

    return _fusionar(segmentos), ps

def ejecutar(nombre, procesos, quantum = None):
    #Ejecuta el algoritmo de planificación indicado por nombre.
    #Si el algoritmo es Round Robin, se requiere un quantum.

    if nombre == "FCFS":
        return fcfs(procesos)
    elif nombre == "SJF":
        return sjf(procesos, apropiativo=False)
    elif nombre == "SRTF":
        return sjf(procesos, apropiativo=True)
    elif nombre == "Round Robin":
        if quantum is None:
            raise ValueError("Se requiere un quantum para Round Robin")
        return round_robin(procesos, quantum)
    elif nombre == "Prioridad (no apropiativo)":
        return prioridad(procesos, apropiativo=False)
    elif nombre == "Prioridad (apropiativo)":
        return prioridad(procesos, apropiativo=True)
    else:
        raise ValueError(f"Algoritmo desconocido: {nombre}")

