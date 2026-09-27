# pNote Skill - Setup & Usage Guide

## Quick Start with uv
...

### PrivateBin Server Fallback

pNote supports robust PrivateBin paste creation by automatically trying up to 3 random fallback servers if the first fails (unless you specify --server directly).

- The fallback server list is configured in `servers.yaml` in the pNote directory:

```yaml
servers:
  - https://privatebin.net/
  - https://paste.debian.net/
  - https://bin.nixnet.services/
...
```

- The list is shuffled randomly for each attempt, up to 3 servers will be tried for each paste.
- To use a specific server, use `--server <URL>`.
- On total failure, the result shows the error received from each attempted server.

To customize the fallback:
- Edit `servers.yaml` to add/remove/replace endpoints as needed.

### Installation
...
(unchanged)

