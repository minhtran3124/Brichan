# Orchard coordinator pack

Orchard is a small coordinator that delegates work to worker sessions. This
pack holds its policy, routing configuration, helper scripts, and task memory.

- [Operating rules](policy/operating.md)
- [Worker rules](policy/workers.md)
- [Model catalog](policy/catalog.md)
- [Review rules](policy/review.md)
- [Task register](memory/tasks.md)
- [Escalation guide](policy/escalation.md)

Routing lives only in `config/routing.json`. Policy files describe rules; they
never restate which route uses which model.
