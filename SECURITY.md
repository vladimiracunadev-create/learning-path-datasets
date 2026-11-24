# Política de seguridad

Reporta de forma privada en **Security → Report a vulnerability** de GitHub. No publiques secretos, datos personales ni documentos confidenciales en un issue. Incluye la ruta afectada, el impacto observado y una forma segura de reproducirlo.

## Alcance

Este repositorio es una herramienta local de preparación de datos: no presta un servicio ni procesa datos de usuarios. Los riesgos principales son:

- la incorporación accidental de secretos, datos personales o material sin licencia dentro de un dataset;
- datos adulterados: cada dataset trae SHA-256 en su manifiesto y `lpdatasets validate` los comprueba, pero esto no sustituye una firma ni una revisión de procedencia;
- dependencias con vulnerabilidades conocidas (se auditan con `pip-audit` y se actualizan con Dependabot);
- confiar en que un dato publicado es correcto: ningún registro tiene revisión humana profesional.

Si encuentras contenido que parezca información personal o que vulnere derechos de autor, repórtalo por el mismo canal para retirarlo.
