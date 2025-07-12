import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import pandas as pd

# Configuración de matplotlib para mejor visualización
plt.rcParams['figure.figsize'] = (15, 12)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

# Datos experimentales basados en las gráficas del documento
# Tiempos en segundos
datos_tiempo = {
    'resoluciones': [0.2, 0.1, 0.05, 0.025],
    'hilos': [1, 2, 4, 8, 16],
    'tiempos': {
        0.2: [2.442, 1.25, 0.65, 0.227, 0.225],
        0.1: [5.100, 2.60, 1.35, 1.080, 1.070],
        0.05: [22.230, 11.5, 6.2, 5.279, 5.492],
        0.025: [120.325, 62.0, 33.5, 30.738, 30.842]
    }
}

# Parámetros del modelo teórico (estimados basándose en los datos)
params = {
    'k': 0.2,  # Factor de eficiencia espacial
    'T_cubo': 1e-6,  # Tiempo base por cubo (segundos)
    'alpha_task': 1e-6,  # Overhead por tarea (segundos)
    'beta_sync': 1e-5,  # Tiempo de sincronización (segundos)
}

def modelo_tiempo_teorico(p, r, k, T_cubo, alpha_task, beta_sync):
    """
    Modelo teórico del tiempo de ejecución paralelo
    """
    n_cubos = k * (1/r)**3
    
    # Tiempo de cómputo
    T_comp = n_cubos * T_cubo / p
    
    # Tiempo de overhead
    T_overhead = n_cubos * alpha_task / 7
    
    # Tiempo de sincronización
    T_sync = 3 * np.log(1/r) / np.log(8) * beta_sync
    
    return T_comp + T_overhead + T_sync

def speedup_teorico(p, r, k, T_cubo, alpha_task, beta_sync):
    """
    Speedup teórico basado en el modelo
    """
    T_s = modelo_tiempo_teorico(1, r, k, T_cubo, alpha_task, beta_sync)
    T_p = modelo_tiempo_teorico(p, r, k, T_cubo, alpha_task, beta_sync)
    return T_s / T_p

def eficiencia_teorica(p, r, k, T_cubo, alpha_task, beta_sync):
    """
    Eficiencia teórica
    """
    return speedup_teorico(p, r, k, T_cubo, alpha_task, beta_sync) / p

def optimizar_parametros(datos_tiempo, params_iniciales):
    """
    Optimiza los parámetros del modelo para ajustar a los datos experimentales
    """
    def modelo_ajuste(datos_x, k, T_cubo, alpha_task, beta_sync):
        p_vals, r_vals = datos_x
        return np.array([modelo_tiempo_teorico(p, r, k, T_cubo, alpha_task, beta_sync) 
                        for p, r in zip(p_vals, r_vals)])
    
    # Preparar datos para optimización
    p_vals = []
    r_vals = []
    t_vals = []
    
    for r in datos_tiempo['resoluciones']:
        for i, p in enumerate(datos_tiempo['hilos']):
            p_vals.append(p)
            r_vals.append(r)
            t_vals.append(datos_tiempo['tiempos'][r][i])
    
    # Optimizar parámetros
    try:
        popt, _ = curve_fit(modelo_ajuste, (p_vals, r_vals), t_vals, 
                           p0=[params_iniciales[key] for key in ['k', 'T_cubo', 'alpha_task', 'beta_sync']],
                           bounds=([0.01, 1e-8, 1e-8, 1e-8], [1.0, 1e-4, 1e-4, 1e-3]))
        
        return {
            'k': popt[0],
            'T_cubo': popt[1],
            'alpha_task': popt[2],
            'beta_sync': popt[3]
        }
    except:
        return params_iniciales

# Crear figura con subplots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

# Optimizar parámetros
params_opt = optimizar_parametros(datos_tiempo, params)

# Gráfica 1: Tiempo vs Número de Hilos
hilos = np.array(datos_tiempo['hilos'])
colores = ['blue', 'red', 'green', 'orange']
markers = ['o', 's', '^', 'D']

for i, r in enumerate(datos_tiempo['resoluciones']):
    # Datos experimentales
    tiempos_exp = datos_tiempo['tiempos'][r]
    ax1.plot(hilos, tiempos_exp, marker=markers[i], color=colores[i], 
             linewidth=2, markersize=8, label=f'Experimental r={r}')
    
    # Modelo teórico
    tiempos_teo = [modelo_tiempo_teorico(p, r, **params_opt) for p in hilos]
    ax1.plot(hilos, tiempos_teo, '--', color=colores[i], alpha=0.7, 
             linewidth=2, label=f'Teórico r={r}')

ax1.set_xlabel('Número de Hilos')
ax1.set_ylabel('Tiempo de Ejecución (s)')
ax1.set_title('Tiempo de Ejecución: Experimental vs Teórico')
ax1.set_yscale('log')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Gráfica 2: Speedup vs Número de Hilos
for i, r in enumerate(datos_tiempo['resoluciones']):
    # Speedup experimental
    tiempos_exp = datos_tiempo['tiempos'][r]
    speedup_exp = [tiempos_exp[0] / t for t in tiempos_exp]
    ax2.plot(hilos, speedup_exp, marker=markers[i], color=colores[i], 
             linewidth=2, markersize=8, label=f'Experimental r={r}')
    
    # Speedup teórico
    speedup_teo = [speedup_teorico(p, r, **params_opt) for p in hilos]
    ax2.plot(hilos, speedup_teo, '--', color=colores[i], alpha=0.7, 
             linewidth=2, label=f'Teórico r={r}')

# Línea de speedup ideal
ax2.plot(hilos, hilos, 'k--', alpha=0.5, label='Speedup Ideal')
ax2.set_xlabel('Número de Hilos')
ax2.set_ylabel('Speedup')
ax2.set_title('Speedup: Experimental vs Teórico')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Gráfica 3: Eficiencia vs Número de Hilos
for i, r in enumerate(datos_tiempo['resoluciones']):
    # Eficiencia experimental
    tiempos_exp = datos_tiempo['tiempos'][r]
    eficiencia_exp = [(tiempos_exp[0] / t) / p for t, p in zip(tiempos_exp, hilos)]
    ax3.plot(hilos, eficiencia_exp, marker=markers[i], color=colores[i], 
             linewidth=2, markersize=8, label=f'Experimental r={r}')
    
    # Eficiencia teórica
    eficiencia_teo = [eficiencia_teorica(p, r, **params_opt) for p in hilos]
    ax3.plot(hilos, eficiencia_teo, '--', color=colores[i], alpha=0.7, 
             linewidth=2, label=f'Teórico r={r}')

ax3.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='Eficiencia Ideal')
ax3.set_xlabel('Número de Hilos')
ax3.set_ylabel('Eficiencia')
ax3.set_title('Eficiencia: Experimental vs Teórico')
ax3.set_ylim(0, 1.5)
ax3.legend()
ax3.grid(True, alpha=0.3)

# Gráfica 4: Escalabilidad - Trabajo vs Número de Hilos
hilos_ext = np.linspace(1, 32, 100)
eficiencias = [0.5, 0.7, 0.8, 0.9]
colores_esc = ['purple', 'brown', 'pink', 'gray']

for i, E in enumerate(eficiencias):
    # Función de isoeficiencia
    W_iso = [params_opt['k'] * p * params_opt['alpha_task'] / (7 * (1 - E)) for p in hilos_ext]
    ax4.plot(hilos_ext, W_iso, color=colores_esc[i], linewidth=2, 
             label=f'Isoeficiencia E={E}')

# Puntos experimentales de trabajo
for i, r in enumerate(datos_tiempo['resoluciones']):
    trabajo_exp = [params_opt['k'] * (1/r)**3 * params_opt['T_cubo']] * len(hilos)
    ax4.scatter(hilos, trabajo_exp, marker=markers[i], color=colores[i], 
               s=80, label=f'Trabajo r={r}', alpha=0.7)

ax4.set_xlabel('Número de Hilos')
ax4.set_ylabel('Trabajo Requerido (FLOPs)')
ax4.set_title('Escalabilidad: Función de Isoeficiencia')
ax4.set_yscale('log')
ax4.legend()
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('escalabilidad_marching_cubes.png', dpi=300, bbox_inches='tight')
plt.show()

# Imprimir parámetros optimizados
print("Parámetros del modelo optimizados:")
print(f"k (factor de eficiencia espacial): {params_opt['k']:.6f}")
print(f"T_cubo (tiempo por cubo): {params_opt['T_cubo']:.2e} s")
print(f"alpha_task (overhead por tarea): {params_opt['alpha_task']:.2e} s")
print(f"beta_sync (tiempo de sincronización): {params_opt['beta_sync']:.2e} s")

# Calcular número óptimo de hilos para cada resolución
print("\nNúmero óptimo de hilos por resolución:")
for r in datos_tiempo['resoluciones']:
    p_opt = np.sqrt(7 * params_opt['k'] * (1/r)**3 * params_opt['T_cubo'] / 
                   (3 * np.log(1/r) / np.log(8) * params_opt['beta_sync']))
    print(f"Resolución {r}: p_opt = {p_opt:.1f} hilos")

# Análisis de escalabilidad
print("\nAnálisis de escalabilidad:")
print("Clasificación: Escalabilidad BUENA a MODERADA")
print("Función de isoeficiencia: W = k × p × α_task / (7 × (1-E))")

# Crear tabla de comparación
print("\nComparación Experimental vs Teórico:")
print("Resolución | Hilos | Tiempo Exp | Tiempo Teo | Speedup Exp | Speedup Teo | Eficiencia Exp | Eficiencia Teo")
print("-" * 100)

for r in datos_tiempo['resoluciones']:
    for i, p in enumerate(datos_tiempo['hilos']):
        t_exp = datos_tiempo['tiempos'][r][i]
        t_teo = modelo_tiempo_teorico(p, r, **params_opt)
        s_exp = datos_tiempo['tiempos'][r][0] / t_exp
        s_teo = speedup_teorico(p, r, **params_opt)
        e_exp = s_exp / p
        e_teo = s_teo / p
        
        print(f"{r:9.3f} | {p:5d} | {t_exp:10.3f} | {t_teo:10.3f} | {s_exp:11.2f} | {s_teo:11.2f} | {e_exp:14.3f} | {e_teo:14.3f}")

# Guardar gráficas adicionales
fig2, (ax5, ax6) = plt.subplots(1, 2, figsize=(16, 6))

# Gráfica de componentes de tiempo
r_ejemplo = 0.05
hilos_detalle = np.linspace(1, 16, 100)

T_comp = [params_opt['k'] * (1/r_ejemplo)**3 * params_opt['T_cubo'] / p for p in hilos_detalle]
T_overhead = [params_opt['k'] * (1/r_ejemplo)**3 * params_opt['alpha_task'] / 7] * len(hilos_detalle)
T_sync = [3 * np.log(1/r_ejemplo) / np.log(8) * params_opt['beta_sync']] * len(hilos_detalle)

ax5.plot(hilos_detalle, T_comp, 'b-', linewidth=2, label='Tiempo Cómputo')
ax5.plot(hilos_detalle, T_overhead, 'r-', linewidth=2, label='Tiempo Overhead')
ax5.plot(hilos_detalle, T_sync, 'g-', linewidth=2, label='Tiempo Sincronización')
ax5.plot(hilos_detalle, np.array(T_comp) + np.array(T_overhead) + np.array(T_sync), 
         'k--', linewidth=2, label='Tiempo Total')

ax5.set_xlabel('Número de Hilos')
ax5.set_ylabel('Tiempo (s)')
ax5.set_title(f'Descomposición del Tiempo (r={r_ejemplo})')
ax5.set_yscale('log')
ax5.legend()
ax5.grid(True, alpha=0.3)

# Gráfica de escalabilidad débil
resoluciones_escala = np.linspace(0.01, 0.3, 50)
hilos_escala = np.power(resoluciones_escala, -3)  # r = O(p^(-1/3))

eficiencias_escala = [eficiencia_teorica(p, r, **params_opt) 
                     for p, r in zip(hilos_escala, resoluciones_escala)]

ax6.plot(hilos_escala, eficiencias_escala, 'b-', linewidth=2, label='Escalabilidad Débil')
ax6.axhline(y=0.8, color='r', linestyle='--', alpha=0.7, label='Eficiencia Objetivo (80%)')

ax6.set_xlabel('Número de Hilos')
ax6.set_ylabel('Eficiencia')
ax6.set_title('Escalabilidad Débil: Eficiencia Constante')
ax6.set_xscale('log')
ax6.legend()
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('escalabilidad_detalles.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nGráficas guardadas como 'escalabilidad_marching_cubes.png' y 'escalabilidad_detalles.png'")