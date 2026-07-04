# networking/

Traffic routing between K8s and serverless backends.

## haproxy/

HAProxy is the traffic router that distributes requests between the K8s cluster and Knative serverless based on configurable weights. The routing daemon (`apps/routing/`) dynamically adjusts these weights based on SLO violations and GRU predictions.

Files:
- `haproxy.cfg` — Default HAProxy config (80/20 K8s/Knative split)
- `haproxy-knative.cfg` — Knative-optimized config
- `haproxy-coldstart.cfg` — Cold-start variant
- `docker-compose.yml` — Local docker-compose for HAProxy
- `docker-compose-knative.yml` — With Knative gateway

**Why not a "load balancer" or "proxy" name?** The domain is traffic routing, not just load balancing. HAProxy is the specific tool, but the domain concept is "how traffic flows between backends."

## Related packages

- `apps/routing/routing/algorithm/weight_adjuster.py` — Runtime weight adjustment via HAProxy admin socket
- `infra/networking/haproxy/client.py` — Programmatic access to HAProxy stats and socket
