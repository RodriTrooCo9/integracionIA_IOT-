#ifndef CONTROL_SAFETY_H
#define CONTROL_SAFETY_H
#include <math.h>

inline bool lectura_aire_valida(float temperature, float humidity) {
    return isfinite(temperature) && isfinite(humidity) && temperature >= -20.0f &&
           temperature <= 60.0f && humidity >= 0.0f && humidity <= 100.0f;
}
inline bool setpoints_validos(float temperature, float humidity) {
    return isfinite(temperature) && isfinite(humidity) && temperature >= 5.0f &&
           temperature <= 35.0f && humidity >= 30.0f && humidity <= 95.0f;
}
inline bool ganancias_validas(float p, float i, float d) {
    return isfinite(p) && isfinite(i) && isfinite(d) && p >= 0 && p <= 100 &&
           i >= 0 && i <= 10 && d >= 0 && d <= 1000;
}
inline bool control_habilitado(bool auto_mode, bool sensor_ok, unsigned long age_ms) {
    return auto_mode && sensor_ok && age_ms <= 2000;
}
#endif
