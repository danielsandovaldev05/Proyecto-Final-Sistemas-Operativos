#Modelo de datos del simulador: El PCB simplificado

from dataclasses import dataclass, field

@dataclass
class Proceso:
    #Represena un proceso que compite por la CPU.

    #Atributos de entrada (los ingresa el usuario):
    pid: str #Identificador del proceso
    llegada: int #Tiempo de llegada a la cola de listos
    rafaga: int #Tiempo de CPU requerido (duración) debe ser > 0
    prioridad: int = 0 #Prioridad del proceso, a menor número, mayor prioridad
    restante: int = field(init = False) #tiempo de CPU que aún le falta
    finalizacion: int = field(init = False, default = 0) #Tiempo en que el proceso termina de ejecutarse

    def __post_init__(self):
        #Inicializa el tiempo restante al valor de la ráfaga
        self.restante = self.rafaga

    def copia(self) -> "Proceso":
        #Devuelve una copia del proceso, útil para simular sin alterar los datos originales.

        #Cada algoritmo trabaja sobre su propia copia, así la misma lista de 
        #procesos puede ser usada para simular distintos algoritmos sin que se alteren los datos originales.
        return Proceso(self.pid, self.llegada, self.rafaga, self.prioridad)