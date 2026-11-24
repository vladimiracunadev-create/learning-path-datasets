# Límites y derechos

Léelo antes de entrenar con estos datos o de redistribuirlos.

## Calidad

- **Sin revisión humana profesional.** Los contenidos de `escolar-chile` fueron escritos con asistencia de IA y verificados por lecturas también asistidas según el proyecto de origen; los diccionarios no tuvieron lector independiente. Se marcan con `ia_asistida_sin_revision_humana`. Pueden contener errores, y un modelo entrenado con ellos los aprende como verdad.
- **Verificación parcial.** Solo una fracción pequeña de los ejercicios (`verificable: true`) tiene una respuesta comprobable por cálculo.
- **No es un currículo oficial.** Los datos siguen la estructura de un proyecto abierto, no son material del Ministerio de Educación ni están contrastados con él más allá de lo declarado en el proyecto de origen.
- **La evaluación no es un benchmark certificado.** Es una reserva del ~10 % de las clases. Clases distintas pueden tratar ideas muy parecidas, así que puede haber cercanía de contenido entre `train` y `eval`.
- **Cobertura.** Hoy solo está publicado 1.º básico del pack escolar. No se debe presentar el dataset como representativo de «todo lo que sabe un estudiante».

## Derechos

- **Datos de `escolar-chile`: CC BY-NC-SA 4.0.** Exige atribución, **prohíbe el uso comercial** sin autorización del titular y obliga a compartir igual las adaptaciones. El uso comercial requiere permiso del titular. Si entrenar un modelo con estos datos para un producto comercial cuenta como uso comercial o como adaptación es una cuestión legal que debe evaluar quien entrena; este repositorio no la resuelve.
- **Textos oficiales.** Los objetivos de aprendizaje y otros textos oficiales conservan los derechos de sus titulares y **no se copian**: solo se cita el código del objetivo.
- **Obras de terceros.** No se incluyen. Si un programa nuevo las trae, deben excluirse o declararse con su propia licencia.
- **Licencia de modelos.** Este repositorio no establece qué licencia debe tener un modelo entrenado con los datos; esa decisión y su cumplimiento son de quien entrena.

## Exclusiones deliberadas

- Se excluye «Lengua y Cultura de los Pueblos Originarios Ancestrales»: requiere un educador tradicional y no debe entrenarse sin su participación.
- Los registros de diccionario van solo en `train`.
- El pack incluye la asignatura `ingles-propuesta`: es una **propuesta propia** del programa de origen, no un currículo oficial de inglés para ese nivel.

## Privacidad

No se incluyó información personal a propósito, pero no se ejecutó una auditoría automática de datos personales. Si encuentras algo que lo parezca, repórtalo según [`SECURITY.md`](../SECURITY.md).
