# Perfil de repositorio · Trayectoria Escolar Chile

Lo que hay que saber para no romper [chilean-school-learning-path](https://github.com/vladimiracunadev-create/chilean-school-learning-path). Es un ejemplo de perfil: para otro repositorio se escribe uno propio en la fase 0. Compruébalo contra el repositorio, que puede haber cambiado desde el 2026-11-26.

## Fuente y salidas

- El contenido del estudiante se escribe en `scripts/student_content_*.py`. `curriculum/`, `site/`, `output/pdf/` y los índices son **generados**: no se editan.
- Cada clase es una llamada `register(OA, número, …)` con `materials`, `use`, `prior`, `explain` (párrafos), `vocab`, `worked`, `mistakes`, `tiers` (`recovery`, `understand`, `apply`, `reason`, `challenge`), `context`, `selfcheck`, `open_task`, `reinforce` y `extend`.
- Hay funciones que **componen texto**: `ex(pregunta, respuesta, razón, calc)`; `arith(…)` calcula la respuesta y escribe «Cálculo: …» con signos como «×»; y ayudantes como `fill`, `cmp_ex`, `task`, `dots` o `frame`.
- `balance_options` **reordena alternativas A/B/C** al cargar: revisa el texto cargado, no el literal.
- Hay textos compartidos en constantes y definiciones repetidas entre clases: cambia solo la de la clase afectada.

## Cómo leer una clase

Carga el registro (`student_lessons.load_all()` y `REGISTRY`) o lee la ficha generada en `curriculum/<nivel>/<asignatura>/`.

## Validación y qué no ve

`student_lessons.problems` exige mínimos (12 ejercicios cerrados, 5 niveles, 2 ejemplos, 3 de autoevaluación, explicación de 90 palabras), razones de al menos 3 palabras, que `calc` concuerde con la respuesta y que no haya enunciados repetidos en la clase. **No comprueba que la respuesta conteste la pregunta, que sea de ese nivel ni que sea la única válida.**

## Regeneración, en orden

1. `scripts/validate_student_lessons.py --write`
2. `scripts/generate_development_plan.py`, `generate_school_program.py`, `generate_competency_portal.py`, `export_pdfs.py`
3. Validadores (`validate_*.py`, `audit_content.py`, `audit_alignment.py`, `generate_competency_portal.py --check`), pruebas `unittest`, `compileall` y `mojibake_probe.py`
4. Segunda generación: fuera de los PDF, no debe cambiar nada.

Usa el entorno del proyecto con sus versiones fijadas. La vuelta completa tarda unos 35 minutos; no toques el repositorio mientras corre.

## Reglas editoriales

- Primera entrada fechada de `CHANGELOG.md` para todo cambio visible; el generador la publica.
- «Revisada» exige evidencia humana (`docs/REVISION_HUMANA.md`). Una lectura de IA no cambia el estado editorial.
- Se conservan identificadores; se distingue texto oficial de elaboración propia; contenido bajo CC BY-NC-SA 4.0.
- Una prueba rechaza la expresión «prompt maestro» en superficies pedagógicas públicas: estas instrucciones viven en `.claude/`.
- La firma DCO (`Signed-off-by`) es de quien contribuye: no se agrega en su nombre.

## Quién consume este contenido

[learning-path-datasets](https://github.com/vladimiracunadev-create/learning-path-datasets) exporta 1.º básico desde un commit fijo. Tras corregir, hay que reexportar allí; las etiquetas aprobadas de las clases cambiadas caducan.
