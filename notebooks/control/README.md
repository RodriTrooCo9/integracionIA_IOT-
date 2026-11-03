# Rama de control — independiente de visión

Ejecuta `01_identificacion_pid_fopdt.ipynb` de arriba abajo. La preparación inicial
monta el proyecto y luego instala las dependencias de control. No requiere GPU.

Si no existe `data/synthetic/prueba_escalon_fopdt.csv`, se genera un ensayo sintético.
Los resultados de ese ensayo no validan un PID en hardware. Conserva la procedencia
de un CSV experimental antes de aplicar ganancias al equipo.

Las figuras y tablas nuevas se escriben en `runs/control/`. Las salidas antiguas
del cuaderno se conservaron como historial; ejecutar solo las últimas celdas
puede producir NameError. Este cuaderno no es un requisito de los pasos 00–04.
