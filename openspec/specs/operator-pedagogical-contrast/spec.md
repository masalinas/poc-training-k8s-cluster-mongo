# operator-pedagogical-contrast Specification

## Purpose
Define los escenarios prácticos de inyección de fallos, pérdida de quórum y desincronización de escalado, contrastando el comportamiento de Kubernetes puro frente a la automatización de Operadores.

## Requirements

### Requirement: Validación de Elección Automática de Primario ante Fallo de Pod
El sistema DEBE (MUST) demostrar que la caída repentina del Pod `mongodb-0` desencadena una elección interna exitosa donde los nodos supervivientes eligen un nuevo `PRIMARY` gracias a la mayoría de votos (2 de 3).

#### Scenario: Elección transparente de nuevo líder
- **WHEN** se elimina forzosamente el Pod `mongodb-0` mediante `kubectl delete pod mongodb-0 --now`
- **THEN** los Pods `mongodb-1` y `mongodb-2` completan una elección de consenso promoviendo uno de ellos a `PRIMARY` en menos de 5 segundos.

### Requirement: Demostración de Pérdida de Quórum y Bloqueo de Escrituras
El sistema DEBE (MUST) demostrar que la caída simultánea de dos nodos provoca la pérdida de quórum en el nodo restante (`1/3` de votos), obligándolo a auto-degradarse a `SECONDARY` y rechazando escrituras.

#### Scenario: Degradación automática por falta de mayoría
- **WHEN** los Pods `mongodb-1` y `mongodb-2` están inaccesibles o detenidos
- **THEN** el nodo `mongodb-0` pierde la condición de `PRIMARY`, pasa a `SECONDARY` y rechaza operaciones de escritura con error de desconexión o primario no disponible.

### Requirement: Demostración del Desfase de Escalado entre Kubernetes y el Replica Set
El sistema DEBE (MUST) evidenciar que el escalado horizontal de réplicas en el StatefulSet no modifica la configuración interna `rs.conf()` del motor MongoDB, dejando los nuevos Pods en aislamiento funcional.

#### Scenario: Ignorancia del Replica Set ante escalado de Pods
- **WHEN** un administrador ejecuta `kubectl scale statefulset mongodb --replicas=5`
- **THEN** Kubernetes crea los Pods `mongodb-3` y `mongodb-4`, pero la salida de `rs.status()` confirma que el clúster sigue compuesto únicamente por los 3 miembros iniciales.

### Requirement: Evaluación Comparativa de Capacidades de Operadores de Producción
El sistema DEBE (MUST) proporcionar una matriz técnica estructurada que justifique el uso de Operadores en producción (MongoDB Community Operator y Percona PSMDB) frente al despliegue manual.

#### Scenario: Contraste de funciones operativas críticas
- **WHEN** se evalúan requerimientos de reconfiguración dinámica de miembros, backups consistentes del Oplog y rotación de certificados TLS
- **THEN** la guía detalla cómo los controladores de Operadores automatizan la reconciliación del Replica Set sin intervención manual ni riesgo de corrupción.
