# Ablation Prompts

消融实验 B (prototype) 和 C (structure) 使用与 baseline 相同的 prompt。

这是因为消融实验的目的是测试**检索方式**的差异，而不是 prompt 的差异：
- **Ablation B (prototype)**: 只使用原型向量检索，不使用结构化推理
- **Ablation C (structure)**: 使用结构化检索，但不使用推理增强

如果未来需要为消融实验定制 prompt，可以在此目录下创建对应子文件夹。
