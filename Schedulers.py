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

