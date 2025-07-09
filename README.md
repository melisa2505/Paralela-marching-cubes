# Paralela-Marching-Cubes

Este proyecto implementa el algoritmo de Marching Cubes en C++ con paralelismo usando OpenMP. Permite extraer superficies implícitas desde funciones 3D, generando mallas triangulares exportadas en formato `.obj`.

El algoritmo se acelera mediante el uso de tareas recursivas (`#pragma omp task`) y puede ejecutarse eficientemente en múltiples núcleos.

## Requisitos

- Compilador compatible con C++11 o superior (ej. `g++`)
- OpenMP habilitado
- make (opcional)
    
## Compilación y ejecución

Desde terminal:

```bash
g++ -std=c++11 -fopenmp marching_cubes_paralelo.cpp -o marching
./marching
```
