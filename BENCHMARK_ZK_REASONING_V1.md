🔐 VATA ZK-Reasoning Benchmark v1
(Formal Specification)

You should publish this as a GitHub markdown file:

BENCHMARK_ZK_REASONING_V1.md

Below is the exact content you can commit.

VATA ZK-Reasoning Benchmark v1
Purpose

This benchmark evaluates whether an AI system (or human analyst) can reason mechanistically about a real on-chain zero-knowledge verification event.

It is not a summarization task.
It is not a blockchain explorer lookup task.
It is a reasoning task over cryptographic and EVM execution structure.

Artifact Under Evaluation

Network: Sepolia (chainId 11155111)

Transaction Hash:
0xb29e0784433888b44a8ce874189b5d75636ac3718c7ee90c3ae0c4ab74b1e86f

ProofAnchor Contract:
0xEc848D2D89699e9cD95BFe6d2881E618c9607A61

Verifier Contract:
0x6F3F1453853B067773E64A869f1516e644a66403

Objective

The system must determine:

What type of cryptographic proof was verified.

How the calldata maps to Groth16 proof structure.

Why the EVM returned success (status = 1).

What invariant or statement class the proof enforces.

How the proofId was deterministically constructed.

Why the emitted event constitutes a permanent receipt.

Required Demonstrations

To pass, the system must:

1. ABI-Level Reasoning

Decode the function selector.

Identify the function signature.

Explain parameter encoding:

uint256[2] a

uint256[2][2] b

uint256[2] c

uint256[] input

2. ZK Structural Reasoning

Identify the Groth16 tuple structure.

Explain the role of a, b, c.

Explain why public inputs must match circuit constraints.

3. EVM Execution Reasoning

Explain why require(verifier.verifyProof(...)) would revert on failure.

Explain why status = 1 implies the proof verified.

Explain the difference between staticcall and state-modifying call in this context.

4. Event-Level Reasoning

Identify event signature hash.

Decode indexed topics.

Explain how proofId = keccak256(abi.encode(...)) works.

Explain why this prevents replay ambiguity.

Disallowed Shortcuts

The system fails if it:

Merely describes Groth16 at a high level.

Avoids decoding calldata structure.

Avoids explaining ABI encoding.

Relies solely on blockchain explorer summaries.

Provides speculative statements without structural justification.

Pass Criteria

A response passes if it demonstrates:

Correct structural mapping of calldata to Groth16.

Correct reasoning about EVM execution path.

Correct explanation of deterministic proofId construction.

No internal contradictions.

Scoring

Binary outcome:

PASS — demonstrates mechanistic reasoning.
FAIL — hand-waving, incomplete mapping, or structural errors