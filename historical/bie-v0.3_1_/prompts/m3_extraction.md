# M3 extraction contract

Input: a batch of M2 document blocks.

Output: atomic information units and explicit typed relations. Every unit must preserve
source block ids. Do not infer unsupported facts. Split multi-claim paragraphs. Use the
question taxonomy to identify which questions the unit answers. Use `unknown` when a
classification cannot be supported.

The extraction stage is not lesson planning and not summarization. It is evidence-preserving
semantic decomposition.
