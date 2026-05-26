<!-- SPECKIT START -->
Current Spec Kit feature: `specs/001-skills-agent-mvp`.
For technologies, project structure, shell commands, and implementation context,
read `specs/001-skills-agent-mvp/plan.md` first.
<!-- SPECKIT END -->

## Spec Kit 与 Superpowers 协作规范

本项目同时使用 Spec Kit 和 Superpowers，但两者职责必须清晰分离：

1. Spec Kit 只负责项目规范文档的生成、落盘和维护。
   - 后续所有开发都必须以 Spec Kit 生成和维护的规范文档为准。
   - Spec Kit 的职责范围限于规范文档，例如 `spec.md`、`plan.md`、`tasks.md` 以及相关规范材料。
   - 最终正式规范文档只能由 Spec Kit 创建和维护。

2. Superpowers 负责除规范文档维护之外的其他协作和工程任务。
   - 包括需求探索、头脑风暴、调研、设计讨论、实现规划、开发执行、调试、验证和代码评审等。
   - 不应让 Superpowers 取代 Spec Kit 成为正式规范文档的来源。

3. 在使用 `speckit-specify` 之前，必须先使用 Superpowers 的 `brainstorming` 流程进行头脑风暴。
   - 头脑风暴结果应先落盘为 Markdown 文档，作为后续 `speckit-specify` 生成 `spec.md` 的参考输入。
   - 该头脑风暴文档只是参考材料，不是最终规范。
   - `spec.md` 以及后续正式规范文档仍必须由 Spec Kit 生成和维护。
