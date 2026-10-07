#Cálculo de métricas de rendimiento, común a todos los algoritmos.
    #Tiempo de retorno (Turnaround) = Finalización - Llegada
    #Tiempo de espera  (Waiting)    = Retorno - Duración

def _formula_promedio(valores):
    # Devuelve el promedio con el desarrollo de la formula
    promedio = sum(valores) / len(valores)
    suma = " + ".join(str(v) for v in valores)
    return promedio, f"({suma}) / {len(valores)} = {promedio:.2f}"

def calcular(procesos):
    #Calcula las métricas de una lista de procesos ya simulados.
 
    #Devuelve un diccionario con:
        #filas: una por proceso, con valores y fórmulas desarrolladas.
        #prom_espera / prom_retorno: promedios globales (float).
        #f_prom_espera / f_prom_retorno: texto con el cálculo del promedio.
        #utilizacion: % de tiempo que la CPU estuvo ocupada.

    filas = []
    for p in procesos:
        retorno = p.finalizacion - p.llegada
        espera = retorno - p.rafaga
        filas.append({
            "pid": p.pid,
            "llegada": p.llegada,
            "rafaga": p.rafaga,
            "fin": p.finalizacion,
            "retorno": retorno,
            "espera": espera,
            "f_retorno": f"{p.finalizacion} - {p.llegada} = {retorno}",
            "f_espera": f"{retorno} - {p.rafaga} = {espera}"
        })

        prom_espera, f_espera = _formula_promedio([f["espera"] for f in filas])
        prom_retorno, f_retorno = _formula_promedio([f["retorno"] for f in filas])

        tiempo_total = max(p.finalizacion for p in procesos)
        utilizacion = 100 * sum(p.rafaga for p in procesos) / tiempo_total

        return {
            "filas": filas,
            "prom_espera": prom_espera,
            "f_prom_espera": f_espera,
            "prom_retorno": prom_retorno,
            "f_prom_retorno": f_retorno,
            "utilizacion": utilizacion
        }