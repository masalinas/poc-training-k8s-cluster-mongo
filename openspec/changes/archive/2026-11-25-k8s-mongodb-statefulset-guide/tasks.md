# Tasks

## 1. Storage & Security Manifests

- [x] 1.1 Crear el manifiesto de almacenamiento dinámico `manifests/00-local-path-storage.yaml` (Rancher local-path-provisioner) y verificar sintaxis con `kubectl apply --dry-run=client`
- [x] 1.2 Generar el Secret `manifests/01-mongo-secret.yaml` con credenciales administrativas y clave de autenticación interna de clúster (`keyFile`) de 756 bytes codificada en base64
- [x] 1.3 Crear el ConfigMap `manifests/02-mongo-configmap.yaml` con la configuración declarativa `mongod.conf` (WiredTiger, replicación `rs0`, seguridad activa y límite de caché de memoria)

## 2. Network & StatefulSet Manifests

- [x] 2.1 Crear el manifiesto del Headless Service `manifests/03-mongo-service.yaml` (`clusterIP: None`, puerto 27017, selector `app: mongodb`) y verificar sintaxis YAML
- [x] 2.2 Crear el manifiesto del StatefulSet `manifests/04-mongo-statefulset.yaml` con 3 réplicas de `mongo:7.0`, `volumeClaimTemplates` de 1Gi (`local-path`), probes de salud y un `initContainer` que copie y asigne permisos estrictos (`chmod 400`, `chown 999:999`) al `keyFile` en un volumen `emptyDir`

## 3. Comprehensive Technical Guide (Markdown)

- [x] 3.1 Redactar los Capítulos 1 a 3 de `docs/k8s-mongodb-statefulset.md`: Fundamentos de estado (StatefulSet vs Deployment), diagramas de topología en ASCII, preparación de StorageClass y gestión de credenciales/keyFile
- [x] 3.2 Redactar los Capítulos 4 a 6 de `docs/k8s-mongodb-statefulset.md`: Capa de red Headless y DNS, despliegue del StatefulSet con initContainer, proceso interactivo guiado de `rs.initiate()` con `mongosh` y comprobación de replicación Oplog
- [x] 3.3 Redactar los Capítulos 7 a 9 de `docs/k8s-mongodb-statefulset.md`: Laboratorio de Caos (elección automática ante caída de pod-0, pérdida de quórum con auto-degradación, y desincronización de escalado de réplicas en K8s puro), matriz comparativa de Operadores (MongoDB Community Operator y Percona PSMDB) y guía de resolución de problemas

## 4. PDF Compilation Pipeline & Deliverables

- [x] 4.1 Implementar el script `scripts/generate_html_pdf.py` para construir la maquetación HTML editorial en `docs/k8s-mongodb-statefulset.html` con tipografías Inter/JetBrains Mono, reglas `@page` A4 y resaltado de bloques técnicos
- [x] 4.2 Compilar el entregable `k8s-mongodb-statefulset.pdf` ejecutando `python3 scripts/generate_html_pdf.py` con Google Chrome o Chromium headless e inyección de marcadores jerárquicos vía `pypdf`, verificando tamaño y consistencia
