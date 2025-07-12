#!/bin/bash

# Script de benchmark para análisis de complejidad Marching Cubes
# Análisis de matriz cúbica con múltiples resoluciones y threads

echo "========================================="
echo "ANÁLISIS DE COMPLEJIDAD MARCHING CUBES"
echo "Matriz Cúbica: Threads vs Resolución"
echo "========================================="
echo ""

# Configuración
EXECUTABLE="./paralelo"
OUTPUT_FILE="matrix_analysis.csv"
LOG_FILE="matrix_analysis.log"
REPETITIONS=3

# Lista de resoluciones (equivalentes a diferentes tamaños de grilla)
# Rango: -3 a 3 (6 unidades por eje)
declare -a RESOLUTIONS=(
    "0.0125"
)

# Lista de threads a probar
declare -a THREAD_COUNTS=(1 2 4 8 16)

# Verificar ejecutable
if [ ! -f "$EXECUTABLE" ]; then
    echo "Error: No se encontró el ejecutable $EXECUTABLE"
    echo "Compila primero: g++ -O3 -fopenmp marching_cubes_paralelo.cpp -o paralelo"
    exit 1
fi

# Crear archivo de resultados con estructura de matriz cúbica
echo "Creando archivo de resultados: $OUTPUT_FILE"
echo "Threads,Resolution,Grid_Size,Repetition,Time_seconds,Speedup_vs_1thread,Efficiency,Speedup_vs_sequential" > "$OUTPUT_FILE"

echo "Iniciando análisis de matriz cúbica: $(date)" > "$LOG_FILE"
echo "Configuración:" >> "$LOG_FILE"
echo "  Resoluciones: ${RESOLUTIONS[*]}" >> "$LOG_FILE"
echo "  Threads: ${THREAD_COUNTS[*]}" >> "$LOG_FILE"
echo "  Repeticiones: $REPETITIONS" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Función para calcular tamaño de grilla aproximado
calculate_grid_size() {
    local resolution=$1
    local range=6  # de -3 a 3
    awk "BEGIN {printf \"%.0f\", $range / $resolution}"
}

# Array para almacenar tiempos de referencia (1 thread) para cada resolución
declare -A reference_times

echo "========================================="
echo "FASE 1: OBTENIENDO TIEMPOS DE REFERENCIA"
echo "========================================="

# Obtener tiempo de referencia (1 thread) para cada resolución
for resolution in "${RESOLUTIONS[@]}"; do
    grid_size=$(calculate_grid_size $resolution)
    echo ""
    echo "Resolución: $resolution (≈${grid_size}³ celdas)"
    echo "Midiendo tiempo de referencia con 1 thread..."
    
    total_time=0
    valid_runs=0
    
    for rep in $(seq 1 $REPETITIONS); do
        echo "  Repetición $rep/$REPETITIONS..."
        
        start_ns=$(date +%s.%N)
        timeout 3600 $EXECUTABLE 1 $resolution > /dev/null 2>&1
        exit_code=$?
        end_ns=$(date +%s.%N)
        
        if [ $exit_code -eq 124 ]; then
            echo "    TIMEOUT (>5 min) - Resolución demasiado fina"
            break
        elif [ $exit_code -ne 0 ]; then
            echo "    Error en ejecución"
            continue
        fi
        
        execution_time=$(awk "BEGIN {printf \"%.3f\", $end_ns - $start_ns}")
        echo "    Tiempo: ${execution_time}s"
        
        total_time=$(awk "BEGIN {print $total_time + $execution_time}")
        valid_runs=$((valid_runs + 1))
        
        # Guardar en CSV
        echo "1,$resolution,$grid_size,$rep,$execution_time,1.000,1.000,1.000" >> "$OUTPUT_FILE"
    done
    
    if [ $valid_runs -gt 0 ]; then
        avg_time=$(awk "BEGIN {printf \"%.3f\", $total_time / $valid_runs}")
        reference_times[$resolution]=$avg_time
        echo "  Tiempo promedio: ${avg_time}s"
        echo "Referencia [$resolution]: ${avg_time}s" >> "$LOG_FILE"
    else
        echo "  ¡Error! No se pudieron obtener tiempos válidos"
        echo "Saltando resolución $resolution" >> "$LOG_FILE"
        unset RESOLUTIONS[$(echo ${RESOLUTIONS[@]/$resolution} | cut -d/ -f1 | wc -w)]
    fi
done

echo ""
echo "========================================="
echo "FASE 2: ANÁLISIS COMPLETO DE MATRIZ"
echo "========================================="

# Análisis principal: matriz threads x resoluciones
for resolution in "${RESOLUTIONS[@]}"; do
    if [ -z "${reference_times[$resolution]}" ]; then
        continue  # Saltar resoluciones que fallaron
    fi
    
    grid_size=$(calculate_grid_size $resolution)
    ref_time=${reference_times[$resolution]}
    
    echo ""
    echo "Analizando resolución: $resolution (≈${grid_size}³ celdas)"
    echo "Tiempo de referencia: ${ref_time}s"
    echo "----------------------------------------"
    
    for threads in "${THREAD_COUNTS[@]}"; do
        if [ $threads -eq 1 ]; then
            continue  # Ya tenemos los datos de 1 thread
        fi
        
        echo "  Probando $threads threads..."
        
        total_time=0
        valid_runs=0
        
        for rep in $(seq 1 $REPETITIONS); do
            echo "    Repetición $rep/$REPETITIONS..."
            
            start_ns=$(date +%s.%N)
            timeout 3600 $EXECUTABLE $threads $resolution > /dev/null 2>&1
            exit_code=$?
            end_ns=$(date +%s.%N)
            
            if [ $exit_code -eq 124 ]; then
                echo "      TIMEOUT"
                echo "$threads,$resolution,$grid_size,$rep,TIMEOUT,0.000,0.000,0.000" >> "$OUTPUT_FILE"
                continue
            elif [ $exit_code -ne 0 ]; then
                echo "      ERROR"
                continue
            fi
            
            execution_time=$(awk "BEGIN {printf \"%.3f\", $end_ns - $start_ns}")
            
            # Calcular métricas
            speedup_vs_1thread=$(awk "BEGIN {printf \"%.3f\", $ref_time / $execution_time}")
            efficiency=$(awk "BEGIN {printf \"%.3f\", $speedup_vs_1thread / $threads}")
            
            # Speedup vs secuencial (asumiendo que 1 thread es secuencial)
            speedup_vs_seq=$speedup_vs_1thread
            
            echo "      Tiempo: ${execution_time}s (Speedup: ${speedup_vs_1thread}, Eff: ${efficiency})"
            
            # Guardar en CSV
            echo "$threads,$resolution,$grid_size,$rep,$execution_time,$speedup_vs_1thread,$efficiency,$speedup_vs_seq" >> "$OUTPUT_FILE"
            
            total_time=$(awk "BEGIN {print $total_time + $execution_time}")
            valid_runs=$((valid_runs + 1))
        done
        
        if [ $valid_runs -gt 0 ]; then
            avg_time=$(awk "BEGIN {printf \"%.3f\", $total_time / $valid_runs}")
            avg_speedup=$(awk "BEGIN {printf \"%.3f\", $ref_time / $avg_time}")
            avg_efficiency=$(awk "BEGIN {printf \"%.3f\", $avg_speedup / $threads}")
            echo "    Promedio: ${avg_time}s (Speedup: ${avg_speedup}, Eficiencia: ${avg_efficiency})"
        fi
    done
done

echo ""
echo "========================================="
echo "ANÁLISIS COMPLETADO"
echo "========================================="
echo ""
echo "Resultados guardados en:"
echo "  - Datos CSV: $OUTPUT_FILE"
echo "  - Log detallado: $LOG_FILE"
echo ""

# Generar resumen de la matriz
echo "RESUMEN DE MATRIZ CÚBICA:"
echo "=========================="
echo ""

# Encabezado
printf "%-12s" "Resolución"
for threads in "${THREAD_COUNTS[@]}"; do
    printf " | %-8s" "${threads}T"
done
printf " | %-10s\n" "Grid Size"

# Línea separadora
printf "%-12s" "------------"
for threads in "${THREAD_COUNTS[@]}"; do
    printf " | %-8s" "--------"
done
printf " | %-10s\n" "----------"

# Datos de la matriz
for resolution in "${RESOLUTIONS[@]}"; do
    if [ -z "${reference_times[$resolution]}" ]; then
        continue
    fi
    
    grid_size=$(calculate_grid_size $resolution)
    printf "%-12s" "$resolution"
    
    for threads in "${THREAD_COUNTS[@]}"; do
        # Extraer tiempo promedio para esta configuración
        avg_time=$(grep "^$threads,$resolution," "$OUTPUT_FILE" | grep -v "TIMEOUT" | \
                   awk -F',' '{sum+=$5; count++} END {if(count>0) printf "%.3f", sum/count; else printf "FAIL"}')
        
        if [ "$avg_time" = "FAIL" ] || [ -z "$avg_time" ]; then
            printf " | %-8s" "FAIL"
        else
            printf " | %-8s" "${avg_time}s"
        fi
    done
    printf " | %-10s\n" "${grid_size}³"
done

echo ""
echo "Para análisis en Python:"
echo "import pandas as pd"
echo "df = pd.read_csv('$OUTPUT_FILE')"
echo "print(df.pivot_table(values='Time_seconds', index='Resolution', columns='Threads', aggfunc='mean'))"
echo ""
echo "¡Análisis completo!"

# Información adicional sobre complejidad teórica
echo "" >> "$LOG_FILE"
echo "ANÁLISIS DE COMPLEJIDAD TEÓRICA:" >> "$LOG_FILE"
echo "Complejidad esperada: O(n³) donde n = 1/resolución" >> "$LOG_FILE"
echo "Speedup ideal: S(p) = p (lineal con número de threads)" >> "$LOG_FILE"
echo "Eficiencia ideal: E(p) = S(p)/p = 1" >> "$LOG_FILE"