#Pruebas de los algoritmos contra ejemplos clásicos (Silberschatz) resueltos a mano.
 
import Metrics
import Schedulers as s
from Models import Proceso
 
 
def lista(*datos):
    return [Proceso(*d) for d in datos]
 
 
def promedios(procesos):
    m = Metrics.calcular(procesos)
    return m["prom_espera"], m["prom_retorno"]
 
 
# Ejemplo: P1(0,8) P2(1,4) P3(2,9) P4(3,5)
EJ = lista(("P1", 0, 8), ("P2", 1, 4), ("P3", 2, 9), ("P4", 3, 5))
 
 
def test_fcfs():
    segs, res = s.fcfs(EJ)
    assert segs == [("P1", 0, 8), ("P2", 8, 12), ("P3", 12, 21), ("P4", 21, 26)]
    assert promedios(res)[0] == 8.75          # esperas 0, 7, 10, 18
 
 
def test_sjf_no_apropiativo():
    segs, res = s.sjf(EJ, apropiativo=False)
    assert segs == [("P1", 0, 8), ("P2", 8, 12), ("P4", 12, 17), ("P3", 17, 26)]
    assert promedios(res)[0] == 7.75          # esperas 0, 7, 15, 9
 
 
def test_srtf():
    segs, res = s.sjf(EJ, apropiativo=True)
    assert segs == [("P1", 0, 1), ("P2", 1, 5), ("P4", 5, 10),
                    ("P1", 10, 17), ("P3", 17, 26)]
    assert promedios(res)[0] == 6.5           # esperas 9, 0, 15, 2
 
 
def test_round_robin():
    ej = lista(("P1", 0, 24), ("P2", 0, 3), ("P3", 0, 3))
    segs, res = s.round_robin(ej, 4)
    assert segs == [("P1", 0, 4), ("P2", 4, 7), ("P3", 7, 10), ("P1", 10, 30)]
    assert abs(promedios(res)[0] - 17 / 3) < 1e-9
 
 
def test_round_robin_empate_llegada_y_fin_de_quantum():
    # P2 llega en t=2, justo cuando P1 agota su quantum: P2 entra primero.
    ej = lista(("P1", 0, 4), ("P2", 2, 2))
    segs, _ = s.round_robin(ej, 2)
    assert segs == [("P1", 0, 2), ("P2", 2, 4), ("P1", 4, 6)]
 
 
def test_cpu_ociosa():
    ej = lista(("P1", 2, 3), ("P2", 10, 2))
    for nombre in ("FCFS", "SJF (no apropiativo)", "SRTF (SJF apropiativo)"):
        segs, _ = s.ejecutar(nombre, ej)
        assert segs == [("IDLE", 0, 2), ("P1", 2, 5), ("IDLE", 5, 10), ("P2", 10, 12)]
    segs, _ = s.round_robin(ej, 2)
    assert segs[0] == ("IDLE", 0, 2) and ("IDLE", 5, 10) in segs
 
 
def test_desempate_sjf():
    # Misma ráfaga: gana el que llegó antes.
    ej = lista(("A", 0, 5), ("B", 1, 3), ("C", 2, 3))
    segs, _ = s.sjf(ej, apropiativo=False)
    assert [x[0] for x in segs] == ["A", "B", "C"]
 
 
def test_prioridad():
    ej = lista(("P1", 0, 5, 3), ("P2", 1, 2, 1), ("P3", 2, 1, 2))
    segs, _ = s.prioridad(ej, apropiativo=False)
    assert [x[0] for x in segs] == ["P1", "P2", "P3"]
    segs, _ = s.prioridad(ej, apropiativo=True)
    assert segs == [("P1", 0, 1), ("P2", 1, 3), ("P3", 3, 4), ("P1", 4, 8)]
 
 
def test_lista_original_no_se_modifica():
    s.round_robin(EJ, 3)
    assert all(p.restante == p.rafaga and p.finalizacion == 0 for p in EJ)
 
 
def test_metricas():
    _, res = s.fcfs(EJ)
    m = Metrics.calcular(res)
    p2 = m["filas"][1]
    assert p2["f_retorno"] == "12 - 1 = 11" and p2["f_espera"] == "11 - 4 = 7"
 
 
if __name__ == "__main__":
    pruebas = [f for n, f in sorted(globals().items()) if n.startswith("test_")]
    for prueba in pruebas:
        prueba()
        print("OK ", prueba.__name__)
    print(f"\n{len(pruebas)} pruebas pasaron.")