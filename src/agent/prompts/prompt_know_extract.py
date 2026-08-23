## prompt_know_extract.py
# import 
from src.model_knowledge.data_knowledge import (
                                            KnowledgeSemanticType, 
                                            MathExpressionType   
                                            )

def build_knowledge_extraction_prompt() -> str:
    return f"""
## Goal

Analyze the target transcript chunk and extract all distinct, relevant,
and reliable knowledge from it.

The target_chunk is the only source from which knowledge may be extracted.
previous_context and next_context are provided only to help interpret the
target chunk.

The summary must not contain factual or mathematical knowledge that is
missing from the structured extraction.

Use the language of target_chunk for extracted knowledge.

## 1. Evidence and context rules

Extract a knowledge item only if it is supported by evidence in target_chunk.

Knowledge from previous_context or next_context MUST NOT be extracted unless
the same knowledge is independently supported by target_chunk.

Surrounding context may only be used to:
- resolve references,
- clarify terminology,
- resolve ambiguities in wording,
- identify what an explicitly mentioned term or reference refers to.

Surrounding context MUST NOT be used to complete a claim that is only
partially stated in target_chunk.

A knowledge item is supported by target_chunk only if the complete substantive
claim can be derived from target_chunk without adding information that appears
only in previous_context or next_context.

Before extracting each knowledge item, verify that supporting evidence exists
within target_chunk.


## 2. Knowledge classification

Classify each extracted knowledge item using the following semantic categories:

{KnowledgeSemanticType.prompt_description()}

Prefer the most specific applicable category.


## 3. Mathematical expressions

Classify extracted mathematical expressions using the following categories:

{MathExpressionType.prompt_description()}

Only extract a mathematical expression when it can be reconstructed reliably
from target_chunk alone.

Never repair, complete, or infer missing mathematical expressions unless all
required information is explicitly and unambiguously supported by target_chunk.

Do not replace an incomplete or informal statement with a more formal
mathematical fact from your own knowledge.

External mathematical knowledge may be used only to interpret terminology.
It must never be used to add, strengthen, generalize, correct, or complete
a claim from target_chunk.

Do NOT invent:
- vector or matrix components,
- operators,
- variables,
- indices,
- signs,
- constants,
- equation terms.

If a mathematical expression is incomplete or ambiguous enough to require
visual context, do not extract the incomplete expression as a MathExpression. 
Set needs_visual_context=True instead.

Only include MathExpression objects whose complete mathematical content can
be reconstructed reliably from target_chunk.

## 4. Visual-context assessment

Set needs_visual_context=True whenever relevant information contained in the
original lecture is likely missing or ambiguous in the transcript and could
potentially be recovered reliably from the video.

This includes, but is not limited to:
- incomplete or ambiguous mathematical notation,
- vectors, matrices, equations, or diagrams whose components are unclear,
- calculations whose operands or layout cannot be reconstructed reliably,
- visual or deictic references such as "this", "here", "there", "the upper
  one", "the middle one", or "delete this" when their referent cannot be
  determined from target_chunk.

This applies even if the remaining conceptual knowledge can be extracted
reliably from text alone.

needs_visual_context=True does NOT mean that the entire chunk is unreliable.
Continue extracting every conceptual statement that is independently and
completely supported by target_chunk.

When uncertain whether mathematical information can be reconstructed reliably
from the transcript alone, prefer needs_visual_context=True.


## 5. Handling incomplete mathematical information

If a mathematical expression is incomplete or ambiguous:
- do NOT reconstruct or complete the expression,
- set needs_visual_context=True,
- extract conceptual knowledge that is independently supported by target_chunk,
  if possible.

Do not discard reliable conceptual knowledge merely because an associated
mathematical expression requires visual context.


## 6. Final verification

Before returning the result, verify that:
- every extracted knowledge item is independently supported by target_chunk,
- no claim has been completed using information available only in surrounding
  context,
- surrounding context has not introduced additional knowledge,
- external mathematical knowledge has not added, corrected, generalized, or
  strengthened any claim,
- mathematical expressions contain no inferred or invented components,
- needs_visual_context=True whenever relevant information could not be
  reconstructed reliably from the transcript alone,
- every relevant factual or mathematical claim appearing in the summary is
  represented in the structured extraction.
""".strip()

    
# Analyze the target transcript chunk. Previous_context and next_context 
# are provided only to interpret the target chunk. Knowledge from 
# previous_context or next_context MUST NOT be included in the extraction 
# unless the same knowledge is explicitly supported by the target chunk itself.

# Surrounding context may only be used to resolve references, ambiguities, 
# terminology, or incomplete wording in the target chunk. 

# Before extracting each knowledge item, verify that evidence for the item 
# exists within the target chunk.

# Classify each extracted knowledge item using the following definitions:
# {KnowledgeSemanticType.prompt_description()}

# Prefer the most specific applicable category.

# Set needs_visual_context=True when the transcript refers to visual
# information required to reconstruct the knowledge reliably, including:

# - incomplete or ambiguous mathematical notation,
# - vectors, matrices, equations, or diagrams whose components are unclear,
# - deictic references such as "this", "here", "there", "the upper one",
#   "the middle one", "delete this", etc. when their referent is visual,
# - calculations whose operands or layout cannot be reconstructed reliably.

# When uncertain whether a mathematical expression can be reconstructed
# from transcript alone, prefer needs_visual_context=True.

# Never repair, complete, or infer missing mathematical expressions
# unless they can be reconstructed unambiguously from the target chunk.

# Do not invent missing vector components, operators, variables,
# indices, signs, or equation terms.

# If a mathematical expression is incomplete or ambiguous:
# - do not reconstruct it as a formula,
# - set needs_visual_context=True,
# - describe the recoverable conceptual knowledge separately if possible.


    # f"""
    # Knowledge from previous_context or next_context MUST NOT be included
    # in the extraction unless the same knowledge is explicitly supported
    # by the target chunk itself.

    # Surrounding context may only be used to resolve references,
    # ambiguities, terminology, or incomplete wording in the target chunk.

    # Before extracting each knowledge item, verify that evidence for the
    # item exists within the target chunk.
    ###############################
    # Analyze the target transcript chunk and extract
    # only knowledge supported by the target chunk.

    # Previous and next context are provided only for interpretation.
    # Do not extract claims supported solely by surrounding context.

    # Mark knowledge as requiring visual context when mathematical
    # notation, formulas, diagrams, vectors, or other information
    # cannot be reconstructed reliably from the transcript alone.
    # """

# previous_context and next_context are provided only to interpret
# the target chunk.

# Extract knowledge only if it is supported by the target chunk.
# Do not extract knowledge solely from previous_context or next_context.

