## prompts_know_consolidate.py
# import


ENTITY_EXTRACTION_PROMPT = """
Identify the important mathematical entities and concepts represented in
the supplied canonical lecture statements.

The purpose is to create a lecture-level concept / keyword index that can
later be enriched from external sources such as Wikipedia.

Extract only concepts directly supported by the supplied statements.

Useful entity types include:
- concept
- operation
- rule
- method
- quantity
- symbol
- constant
- theorem
- algorithm
- other

Examples of suitable entities include mathematical operations, named
rules, mathematical objects, calculation methods, or explicitly discussed
concepts.

IMPORTANT RULES

1. Do not invent concepts that are absent from the supplied statements.

2. Do not add encyclopedic explanations.

3. canonical_name should be a clean standard name when the supplied
   statements make that name unambiguous.

4. aliases should contain alternative names or clearly recognizable
   variants present in the lecture.

5. Avoid generic discourse words.

6. Every entity must reference the canonical statement IDs that support it.

7. Never invent statement IDs.

8. Do not merge distinct but related concepts.
   For example, "Ausmultiplizieren" and "Distributivgesetz" may be related
   but can remain separate entities.

9. Use the dominant language of the canonical statements for
   canonical_name and aliases.

10. Preserve conventional alternative-language names only as aliases
    when they are actually useful.

Return only entities that would be useful for searching, indexing,
learning, or later enrichment.
"""


SEMANTIC_CONSOLIDATION_PROMPT = """
You consolidate knowledge statements extracted from a lecture transcript.

The input contains statements that have already been extracted from the
transcript. They may contain:

- overlap duplicates
- paraphrases of the same knowledge
- incomplete spoken-language fragments
- transcript noise
- examples
- definitions
- explanations
- rules
- derivation steps

Your task is to create canonical knowledge statements.

IMPORTANT RULES

1. Use ONLY information supported by the supplied statements.

2. Do not add mathematical facts from general knowledge.

3. Merge statements when they communicate the same underlying knowledge.

4. Preserve different pieces of knowledge separately.

5. Preserve examples and derivation steps when they contain useful
   mathematical information.

6. Discard statements only when they are clearly:
   - conversational filler
   - meta-commentary
   - incomplete references such as
     "that is the underlined part"
   - unusable transcript fragments
   - statements without independently useful knowledge

7. Spoken language may be cleaned up grammatically.

8. Obvious transcription/spelling errors may be normalized ONLY when the
   intended term is unambiguous from the supplied statements.

9. Preserve hypothetical reasoning.
   Example:
   If the lecturer assumes "suppose 3/0 = x" for a contradiction,
   do NOT convert this into the factual claim that 3/0 exists.

10. Every canonical statement MUST contain the IDs of all input statements
    that support it.

11. Never invent source_statement_ids.

12. A source statement may support more than one canonical statement when
    it genuinely contains multiple independent pieces of knowledge.

13. Prefer concise, self-contained formulations that are understandable
    without seeing the original transcript.

14. Preserve the semantic category:
    definition, statement, rule, explanation, example, derivation_step.

15. Never repair, simplify, or normalize numerical values when the
    source statements are ambiguous.

16. If a mathematical statement appears internally inconsistent,
    preserve the uncertainty instead of turning it into a clean
    factual statement.

17. Do not infer omitted decimal places, operators, variables,
    brackets, or numerical values from general mathematical knowledge.

18. Never create a canonical statement that describes the input,
    transcript quality, missing information, discarded statements,
    or your own consolidation process.

    Such observations belong only in discarded_statements or
    review metadata.

Return discarded statements separately and explain briefly why they were
discarded.

19. Use the dominant language of the supplied statements for all
    canonical statements, topics, review reasons, and discard reasons.

    Do not switch languages merely because mathematical terminology
    also exists in English.

20. Set needs_review=True whenever relevant mathematical content is
    preserved but cannot be stated reliably because of ambiguity,
    apparent transcription errors, inconsistent numerical values,
    or missing visual information.

    Explain the reason briefly in review_reason.

"""
