PDDL Integration

This document describes the PDDL-FOND integration layer in kplan.

It has two purposes:

    • describe the code that exists today
    • define how this module is expected to evolve

This document is intended to remain aligned with the codebase over time.
Whenever the implementation changes, this document must be updated accordingly.

⸻

1. Scope

The PDDL module is the adapter layer that allows kplan to read external
planning problems written in PDDL-FOND and convert them into internal
structures compatible with the project architecture.

At the current stage, the implemented scope is:

    • parsing PDDL domain files
    • parsing PDDL problem files
    • validating a restricted PDDL subset
    • converting external parser objects into an internal AST
    • testing parser behavior and parser invariants

Not yet implemented:

    • grounding
    • Problem adapter
    • solver execution from PDDL
    • CLI entry point

This distinction is essential.
The current module is a parser layer, not yet a full execution layer.

⸻

2. Why this module exists

The PDDL layer is introduced to make kplan usable on standard planning inputs.

Main goals:

    • load domains and problems from a standard research format
    • prepare the project for external benchmark evaluation
    • keep the core planner independent from file formats and parser libraries
    • preserve the current architecture of kplan

This is part of the long-term goal of evaluating kplan on standard FOND-style
benchmarks and positioning the project for academic publication.  [oai_citation:1‡pddl-integration.md](sediment://file_0000000013b87243b0e63fb8f2b8b5ec)

⸻

3. Architectural position

The PDDL integration lives in:

kplan_io/pddl/

This is intentionally outside:

    • core/
    • algorithms/
    • domains/

The dependency direction is:

PDDL files → kplan_io/pddl → internal AST → future adapter → core interfaces

This preserves the existing kplan structure:

    • core/ defines generic abstractions
    • algorithms/ implements the solver
    • domains/ contains hand-written native domains
    • kplan_io/pddl/ is an external input adapter

The PDDL layer does not modify or replace the native domains.
It is an additional entry path into the system.

⸻

4. Design constraints

The current implementation follows these constraints:

    • no changes to core/
    • no changes to algorithms/
    • no changes to existing domains/
    • no leakage of external parser objects outside parser.py
    • strict validation over permissive interpretation
    • deterministic output for reproducible tests

These constraints are not accidental.
They are part of the design of the module.

⸻

5. External dependency

The current parser backend is the `pddl` PyPI package.

Important architectural rule:

    • all imports from `pddl.*` are confined to kplan_io/pddl/parser.py

No other file in the project is allowed to depend on the external parser.

Why this matters:

    • the rest of the project remains independent from the library
    • the parser backend can be replaced later if necessary
    • external, untyped objects do not pollute the internal model

This boundary is enforced by tests.

⸻

6. Parser boundary invariant

The strongest invariant of the current module is:

    • no object from the external `pddl` package may escape parser.py

The public functions of the parser return only internal AST objects.

This means that downstream code never sees:

    • external parser classes
    • external formula nodes
    • external predicate or term objects

Instead, the parser converts everything into kplan-owned dataclasses.

This invariant is important for:

    • isolation
    • type safety
    • future replaceability of the parser backend
    • testability

⸻

7. Implemented files

At the current stage, the PDDL module consists of:

kplan_io/pddl/errors.py
    Domain-specific exception hierarchy.

kplan_io/pddl/ast.py
    Internal AST used by the rest of the module.

kplan_io/pddl/parser.py
    External parser boundary and conversion logic.

Tests currently live in:

tests/kplan_io/pddl/test_parser.py

The current implementation is therefore centered on parsing and validation.

⸻

8. Internal AST

The parser converts external structures into an internal AST defined in:

kplan_io/pddl/ast.py

Current AST elements include:

Atom
    Predicate name plus ordered arguments.

PDDLState
    Immutable state wrapper over a frozenset of Atom.

LiteralPrecondition
    One atomic literal with an explicit negation flag.

AndPrecondition
    A conjunction of literals.

DeterministicEffect
    Flat add/delete effect:
        • adds
        • dels

OneOfEffect
    Sequence of deterministic branches.

PredicateSchema
    Predicate signature declared in the domain.

ActionSchema
    Parameterized action schema with:
        • name
        • parameters
        • precondition
        • effect

GroundAction
    Present in the AST surface already, but not yet produced by the current implementation.

ParsedDomain
    Internal representation of a parsed domain.

ParsedProblem
    Internal representation of a parsed problem.

⸻

9. Important note about grounding

At the current stage, the parser is symbolic.

This means:

    • problem init atoms are already concrete atoms from the problem file
    • action schemas still contain variables
    • effects in ActionSchema are symbolic, not grounded

So the current module does not yet support direct execution of actions.

Example:

An action schema may still contain:

    holding(?b)

not:

    holding(a)

This is expected at this stage.
Grounding is the next major step.

⸻

10. Current state representation

PDDLState already exists in the code.

Its role today is limited but important:

    • it provides the future state carrier for PDDL-based problems
    • it is immutable and hashable
    • it already matches the requirements of the existing solver architecture

The class currently provides helper methods such as:

    • holds(atom)
    • apply(adds, dels)

These methods are low-level utilities.
They do not yet make the PDDL module executable by themselves.

They become fully meaningful only after grounding and Problem integration.

⸻

11. Preconditions model

The current parser supports only a restricted precondition language.

Supported shape:

    • conjunction of literals
    • positive literals
    • negative literals

Internally, preconditions are normalized to:

AndPrecondition

This means that even a syntactically single literal is wrapped into a
conjunctive structure.

Reason:

    • downstream consumers do not need to handle multiple precondition shapes

This is a deliberate simplification of the internal model.

⸻

12. Effect model

Effects are represented using two layers:

DeterministicEffect
    one flat add/delete effect

OneOfEffect
    a tuple of DeterministicEffect branches

This is the most important normalization rule of the parser.

Even deterministic effects are normalized as:

    OneOfEffect with exactly one branch

This means that all parsed actions share a single effect shape.

That simplifies:

    • future grounding
    • future successor generation
    • future Problem adapter code

⸻

13. Effect normalization rules

The parser currently normalizes effects according to these rules:

    • a deterministic effect becomes OneOfEffect with one branch
    • a top-level oneof becomes multiple branches
    • a top-level conjunction containing oneof distributes the deterministic part into every branch

Example:

(and (not a) (oneof b c))

becomes:

    branch 1
        dels = {a}
        adds = {b}

    branch 2
        dels = {a}
        adds = {c}

Additionally:

    • if normalization would produce a branch that both adds and deletes the same atom,
      the parser raises PddlParseError

This protects the internal model from inconsistent effects.

⸻

14. Supported subset

The parser currently supports a deliberately restricted PDDL fragment.

Supported features:

    • :typing
    • :non-deterministic
    • :negative-preconditions
    • conjunctions of literals
    • oneof in effects
    • delete effects via not(...)

The goal is not broad PDDL coverage.
The goal is a small, explicit, testable subset suitable for the current
kplan integration.

⸻

15. Explicitly rejected features

The parser explicitly rejects unsupported constructs.

This includes at least:

    • or
    • when
    • forall
    • exists
    • equality
    • numeric fluents
    • derived predicates
    • domain constants
    • multiple oneof constructs in a single effect

Also important:

    • using oneof without the required :non-deterministic requirement is rejected

The general rule is:

    • fail loudly
    • do not silently reinterpret unsupported syntax

⸻

16. Error model

The current public error model is:

FileNotFoundError
    Propagated unchanged.

UnsupportedPddlFeatureError
    Raised when the input uses features outside the supported subset
    or violates the accepted requirement/feature contract.

PddlParseError
    Raised when parsing/conversion fails for other reasons.

This keeps the public boundary simple and project-specific.

Also important:

    • external exceptions from the `pddl` package must not leak through the public API

⸻

17. Deterministic output

The external parser may return unordered collections.

The current implementation explicitly normalizes ordering so that parser
output is stable across runs.

This includes sorting of:

    • predicates
    • actions
    • objects

Why this matters:

    • reproducible tests
    • predictable debugging
    • stable textual and structural comparison
    • future benchmark reproducibility

Determinism is part of the module design, not just a testing convenience.

⸻

18. What the current tests actually prove

The current test suite is focused on parser behavior.

It validates:

    • successful parsing of a deterministic toy domain
    • successful parsing of a toy FOND domain
    • normalization of deterministic effects
    • normalization of oneof effects
    • distribution of deterministic literals into oneof branches
    • rejection of unsupported features
    • rejection of branch add/delete conflicts
    • propagation of FileNotFoundError
    • parser-output determinism
    • absence of external parser types in returned objects
    • basic PDDLState helper behavior
    • requirement mismatch handling for oneof without :non-deterministic

What the tests do not yet prove:

    • grounding correctness
    • goal evaluation inside a Problem adapter
    • solver integration from PDDL inputs
    • end-to-end execution of PDDL domains

This distinction should remain explicit.

⸻

19. Relation to current kplan semantics

The parser does not add new planning semantics.

It only creates a representation that is compatible with the current
worst-case interpretation of non-determinism already present in kplan.

At the current architectural level:

    • each oneof branch is intended to become one possible successor
    • no nominal/adverse distinction is encoded in the parser
    • no branch is privileged as “intended”
    • all outcomes remain relevant

This aligns with the current solver model, where non-determinism is handled
as a set of possible successors.

Important clarification:

    • the current solver does not yet consume the PDDL module directly
    • the semantic alignment is architectural, not yet operational

⸻

20. What is not implemented yet

The following pieces do not exist yet in executable form:

    • grounding of ActionSchema into GroundAction
    • typed object substitution
    • precondition instantiation
    • effect instantiation
    • PDDLProblem implementing core.problem.Problem
    • successor generation from grounded actions
    • goal evaluation in solver-facing form
    • command-line execution of PDDL problems

The module must still evolve before PDDL domains can be solved end-to-end.

⸻

21. Evolution path

The intended next stages are:

Stage 1
    Parser and internal AST
    Status: implemented

Stage 2
    Grounding
    Convert ActionSchema into GroundAction by substituting variables with compatible objects.

Stage 3
    Problem adapter
    Implement a PDDL-backed Problem[PDDLState, GroundAction].

Stage 4
    Solver integration
    Run KPlanSolver on grounded PDDL problems.

Stage 5
    CLI and benchmark workflow
    Load domain/problem files and run experiments directly from PDDL inputs.

This sequence reflects the intended implementation order.

⸻

22. Planned grounding model

The grounding phase is planned as:

    • eager
    • deterministic
    • type-aware
    • performed once at initialization

For each ActionSchema:

    1. enumerate object assignments compatible with parameter types
    2. substitute variables with concrete object names
    3. produce GroundAction instances

Expected result:

    symbolic actions → executable actions

Grounding is expected to preserve the normalized internal effect shape:

    GroundAction.effect is still OneOfEffect

This keeps the runtime execution model simple.

⸻

23. Planned Problem adapter

After grounding, the PDDL module is expected to provide an adapter that
implements the existing Problem protocol used by kplan.

Target mapping:

    initial_state()      → PDDLState
    get_actions(state)   → applicable GroundAction set
    get_successors(...)  → successor PDDLState set
    is_goal(state)       → goal satisfaction check

This is the step that will make PDDL operationally compatible with
KPlanSolver.

This adapter does not exist yet.

⸻

24. Planned complexity tradeoff

The planned grounding strategy is eager.

This is expected to increase upfront work, but keep runtime solving simpler.

Tradeoff:

    • simpler runtime behavior
    • deterministic action inventory
    • higher initialization cost
    • possible scalability limits on large object sets

This tradeoff is acceptable for the current research-oriented scope.

If needed in the future, later extensions may explore:

    • lazy grounding
    • symbolic grounding
    • pruning

These are future optimizations, not current behavior.

⸻

25. Maintenance rule for this document

This document must remain synchronized with the code.

When the implementation changes, update:

    • implemented scope
    • AST description
    • supported subset
    • tests section
    • evolution status

The document must always distinguish clearly between:

    • what is implemented now
    • what is planned next
    • what remains only a target

If this distinction is lost, the document becomes misleading.

⸻

26. Summary

The current PDDL module provides:

    • a strict parser boundary
    • an internal AST independent from the external parser library
    • normalized representation of preconditions and effects
    • explicit rejection of unsupported syntax
    • deterministic parser output
    • parser-focused test coverage

It does not yet provide:

    • grounding
    • Problem integration
    • solver execution
    • CLI support

So, at the current stage, the module should be understood as:

    a validated symbolic PDDL front-end for kplan

not yet a complete executable PDDL backend.

⸻