# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

If you discover a security issue:

1. Open a [GitHub Security Advisory](https://github.com/false200/queuebridge/security/advisories/new) (preferred), or
2. Contact the maintainer via GitHub with details privately

Include:

* Description of the vulnerability
* Steps to reproduce
* Impact (e.g. untrusted broker deserialization, FQN import abuse)
* Suggested fix if you have one

We aim to respond within 7 days.

## Security notes for users

* Only deserialize task messages from **brokers you trust**
* queuebridge resolves types by fully-qualified name (`import_fqn`) during decode
* Do not expose Redis/RabbitMQ without authentication
* Arq: use queuebridge msgpack serializers instead of pickle when possible

See [Security docs](https://queuebridge.readthedocs.io/en/latest/security.html).
