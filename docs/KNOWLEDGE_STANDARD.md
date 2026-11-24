# Estándar de conocimiento puro

Un dataset de **conocimiento puro** contiene afirmaciones verdaderas, atómicas y rastreables sobre un dominio, no instrucciones ni conversaciones. Sirve para ajustar modelos, para recuperar contenido (RAG) y para evaluar si un modelo sabe algo. Este estándar lo usan las [skills y los agentes](SKILLS_AND_AGENTS.md) de este repositorio y es **independiente del dominio**: vale igual para matemática escolar que para ciberseguridad o finanzas.

## Los siete principios

1. **Atómico.** Un registro, una idea. Si una afirmación se puede dividir en dos que se verifiquen por separado, se divide.
2. **Autocontenido.** Se entiende sin ver el registro de al lado: no usa «lo anterior», «el ejemplo de arriba» ni pronombres sin referente.
3. **Fundamentado.** Cada afirmación se apoya en un pasaje de la fuente, que se cita en `razon` (o en `extra.soporte`). Si la fuente no lo dice, no se escribe.
4. **Verificable por separado.** Quien verifica no es quien extrajo. Lo calculable se calcula; lo demás se contrasta con la fuente.
5. **Con vigencia.** Lo que cambia con el tiempo (cifras, versiones, normas) declara su fecha de corte en `extra.vigencia`. Lo atemporal lo dice.
6. **Neutral y sin ruido.** Sin opinión, sin publicidad, sin referencias al formato original (números de página, «ver figura»), sin datos personales.
7. **Honesto sobre su origen.** `revision` dice la verdad: mientras no haya revisión humana, el valor es `ia_asistida_sin_revision_humana`.

## Tipos de conocimiento

| Tipo | Qué es | `entrada` | `salida` |
|---|---|---|---|
| `definicion` | qué significa un término | el término | definición autocontenida |
| `hecho` | una afirmación sobre el mundo | pregunta o sujeto | la afirmación, en una oración |
| `relacion` | cómo se conectan dos conceptos | los dos conceptos | la relación (causa, parte de, tipo de, requiere…) |
| `procedimiento` | cómo se hace algo | el objetivo | pasos en orden |
| `concepcion_erronea` | una idea equivocada frecuente | la idea equivocada | la corrección; el porqué en `razon` |
| `concepto` | una sección entera de explicación | recorrido de encabezados | el texto (cuando no se puede atomizar) |

`extra` admite `sujeto`, `predicado`, `objeto`, `vigencia`, `confianza` (`alta`/`media`/`baja`) y `soporte` (cita breve de la fuente).

## Ejemplo

```json
{"tipo": "hecho", "entrada": "¿Qué identifica una dirección IP?",
 "salida": "Una dirección IP identifica a un equipo dentro de una red para que los paquetes lleguen a su destino.",
 "razon": "Fuente: «Una dirección IP identifica a un equipo dentro de una red…» (redes.md, ## Direcciones IP).",
 "extra": {"sujeto": "dirección IP", "predicado": "identifica", "objeto": "equipo en una red", "confianza": "alta"}}
```

## Lo que no es conocimiento puro

Respuestas de chat, opiniones, texto promocional, ejercicios sin respuesta verificada, citas largas copiadas de terceros, afirmaciones que dependen de una fecha sin declararla.

## Calidad mínima para publicar

- 100 % de los registros con fuente (repo, commit, ruta) y licencia.
- Un verificador independiente revisó cada registro o una muestra declarada; el informe se conserva.
- Sin duplicados exactos y con la cercanía entre `train` y `eval` medida o declarada.
- Derechos y datos personales revisados.
