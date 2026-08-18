---
name: cpp-code-review
description: The coding standard for C++ (clang-format style, modern C++ and type safety, RAII and resource management, const-correctness, naming, and error handling) to follow while writing C++ and to apply when reviewing it. Use when writing, implementing, or refactoring C++, or when asked to review, lint, improve, or critique it ("add const", "fix memory management", "modernize this", "make this more readable"; clang-format, clang-tidy, smart pointers), or for any .cpp/.h/.hpp/.cc/.cxx file. If C++ is pasted without instructions but clearly needs work, offer a review. For structural design (decomposition, interfaces, coupling) use software-design; for language-agnostic structural or artifact cleanup defer to code-polishing; for Python use python-code-review.
---

# C++ Code Review & Improvement

The coding standard for C++: how it should be written and how it should be reviewed. The language-agnostic conduct is defined in [`../_shared/review-conduct.md`](../_shared/review-conduct.md) and applies here in full: the change ethos (every change needs a reason; never change code just to change it) and the two working modes, **authoring** (apply the standard as you write; the default when implementing or modifying C++) and **reviewing** (audit against it and return an improved version per "How to Deliver the Review").

Default to modern C++ (C++17 or later) unless the user specifies a standard; ask when the codebase context is ambiguous and the distinction matters.

## Review Checklist

Work through in order: formatting and naming first (readability), then types and documentation (intent), then safety, logic, and design.

### 1. Formatting & Style

Use clang-format. Beyond what it handles:

- **Includes**: group as related header, C system, C++ standard library, third-party, project-local; blank-line separated, each group sorted alphabetically. `#include <header>` for system/library, `#include "header.h"` for project. Remove unused includes; prefer forward declarations in headers when the full definition isn't needed.
- **Naming**: `PascalCase` for types (classes, structs, enums, type aliases); `snake_case` for functions, variables, namespaces, and file names; `kPascalCase` or `UPPER_SNAKE_CASE` for constants (pick one, be consistent). Private members: leading or trailing underscore; trailing is safer (leading underscore + capital letter is reserved).
- **Braces**: opening brace on the same line (K&R / "attach") for functions, control flow, and classes. Always brace single-line `if`/`for`/`while` bodies: the "goto fail" bug class isn't worth one saved line.
- **Namespaces**: don't indent bodies; `// namespace foo` closing comments on long blocks. Never `using namespace` in headers; minimize in source files; prefer explicit namespacing or targeted `using` declarations.

### 2. Modern C++ & Type Safety

Leverage the type system to catch bugs at compile time.

- **`auto` judiciously**: fine when the type is obvious (`auto it = map.find(key)`) or painfully long; not when it hides a type the reader needs.
- **`enum class` over plain `enum`**: prevents implicit conversions and name collisions.
- **`[[nodiscard]]`** where ignoring the return is almost certainly a bug (error codes, newly allocated resources, computation results).
- **`std::optional`** over sentinel values (`-1`, `nullptr` as "not found"): makes the contract explicit.
- **`constexpr`/`consteval`** for compile-time values and functions; `constexpr` over `#define` for constants.
- **`nullptr`** over `NULL` or `0`, always: macro/integer overload-resolution surprises.
- **Structured bindings** (C++17): `auto [key, value] = *it;` for pairs and tuples.
- **`std::string_view`** for read-only string parameters that don't need ownership (safe as long as the view doesn't outlive the source).

**Before:**
```cpp
int find_user(vector<pair<int, string>>& users, string name) {
    for (int i = 0; i < users.size(); i++)
        if (users[i].second == name) return users[i].first;
    return -1;
}
```

**After:**
```cpp
[[nodiscard]] std::optional<int> find_user_id(
    const std::vector<std::pair<int, std::string>>& users,
    std::string_view name)
{
    for (const auto& [id, user_name] : users) {
        if (user_name == name) {
            return id;
        }
    }
    return std::nullopt;
}
```

### 3. Documentation (Doxygen Style)

Doc-comment all public functions, classes, and files; skip trivially obvious private helpers and simple getters/setters.

```cpp
/**
 * @brief Calculate weighted summary statistics for a range of values.
 *
 * Extended description after a blank line.
 *
 * @param values  Input values. Must be non-empty.
 * @param weights Same size as @p values when provided; empty for equal weighting.
 * @return A Metrics struct containing mean, std, and median fields.
 * @throws std::invalid_argument If @p values is empty or sizes mismatch.
 * @note Thread-safe if called with distinct data.
 * @code
 * auto stats = calculate_metrics({1.0, 2.0, 3.0});
 * @endcode
 */
Metrics calculate_metrics(std::span<const double> values,
                          std::span<const double> weights = {});
```

- `@brief` one-line summary; extended description after a blank line.
- Every parameter gets `@param`, every return `@return`, every thrown exception `@throws`.
- `@note` for thread-safety, performance characteristics, or caveats; `@code`/`@endcode` for examples when the interface isn't self-explanatory.
- Classes: document purpose above the declaration; non-obvious member functions individually.
- Headers: file-level `@file`/`@brief` comment at the top.

### 4. Variable & Function Naming

The language-agnostic naming doctrine (names as the primary documentation, specific over generic, verb-led functions, booleans as predicates, domain vocabulary) is in [`../_shared/naming-and-comments.md`](../_shared/naming-and-comments.md). C++ adds:

- **Getters may omit the verb**: `size()`, `empty()`, `name()`.
- **Template parameters**: single uppercase (`T`, `U`) for simple cases; descriptive names for constrained ones (`Container`, `Predicate`, `Allocator`).
- **No Hungarian notation** (`strName`, `iCount`, `pUser`); `m_` or trailing `_` for members is acceptable.

### 5. Code Efficiency

Optimize where it matters, not everywhere.

- **Const reference for non-trivial input parameters** (`const std::string&`); `std::string_view` when ownership isn't needed; by value for sink parameters you'll move or copy anyway.
- **Move semantics**: `std::move` values you're done with; implement move constructor/assignment for resource-owning types; return locals by value (NRVO).
- **`reserve()`** vectors when the final size is known: avoids reallocations in `push_back` loops.
- **Algorithms over raw loops**: `std::find_if`, `std::transform`, `std::accumulate`, `std::ranges::` (C++20), unless the algorithm version is more complex than the loop.
- **Avoid accidental copies**: `for (auto x : vec)` copies each element, so use `const auto&`; watch `std::map::operator[]` vs `find()`.
- **Right container**: `std::vector` default; `std::unordered_map`/`std::unordered_set` for O(1) lookup; `std::array` for fixed-size; `std::deque` for front-insertion; `std::flat_map` (C++23) or sorted `std::vector` for small ordered maps.
- **No premature optimization**: profile first (perf, Valgrind, a sampling profiler), then optimize the bottleneck.

### 6. Code Readability

The shared clarity doctrine (short single-purpose functions, early returns, complex expressions broken into named intermediates) is in [`../_shared/naming-and-comments.md`](../_shared/naming-and-comments.md); named intermediates pay off most in template-heavy code. C++ adds:

- **Consistent patterns** within a module: don't mix exceptions and return codes for the same kind of operation.
- **Minimize preprocessor**: `constexpr`/`consteval`/`if constexpr`/templates over `#ifdef` chains; macros only for what the language can't express (`__FILE__`, `__LINE__`).
- **Clean headers**: minimize exposure, forward declare aggressively, PIMPL for complex classes to reduce compilation dependencies.

### 7. Memory Safety & Resource Management (RAII)

RAII is the primary tool: tie every owned resource's lifetime to a scope.

- **Smart pointers for ownership**: `std::unique_ptr` as the default, `std::shared_ptr` only for genuinely shared ownership; raw pointers only for non-owning observation.
- **`std::make_unique`/`std::make_shared`** over direct `new`: exception-safe and concise.
- **No naked `new`/`delete`**: `new` outside a factory function or custom allocator is almost always wrong; `delete` outside a destructor or custom deleter is almost certainly wrong.
- **Rule of Zero/Five**: with no direct resource management, declare no special members (compiler defaults are correct); when managing a resource, implement all five or explicitly `= delete` the unsupported ones.
- **`const` correctness**: member functions, locals, parameters, getter returns; it is documentation plus a compile-time safety net.
- **Avoid dangling**: no references/pointers to locals; no iterators held across container modifications; `std::string_view`/`std::span` don't extend the underlying data's lifetime.
- **`std::span`** (C++20) for non-owning array views instead of raw pointer + size.

```cpp
// Before: Connection** + manual new[]/new per slot and a hand-written
// destructor doing delete/delete[]. After:
class ConnectionPool {
public:
    explicit ConnectionPool(std::size_t pool_size)
        : connections_(pool_size)
    {
        for (auto& conn : connections_) {
            conn = std::make_unique<Connection>();
        }
    }
    // Rule of Zero: vector<unique_ptr> handles destruction, copy, move.
private:
    std::vector<std::unique_ptr<Connection>> connections_;
};
```

### 8. Error Handling & Edge Cases

- **One consistent strategy per module**: exceptions for truly exceptional failures (I/O errors, resource exhaustion); `std::optional`/`std::expected` (C++23) for operations that can legitimately have no result; error codes for performance-critical paths or C interop.
- **Validate at boundaries**: public entry points check inputs; private helpers trust their callers.
- **Meaningful exceptions**: derive from `std::runtime_error`/`std::logic_error`; include context: `throw std::invalid_argument("ConnectionPool: pool_size must be > 0, got " + std::to_string(pool_size));`
- **Exception safety**: strong guarantee (succeed or no effect) for public interfaces; basic guarantee (no leaks, invariants preserved) at minimum; copy-and-swap for strong exception-safe assignment.
- **Plausible edge cases only**: empty containers, null pointers (when the interface accepts them), zero-size inputs, boundary conditions; no defensive code for states the preconditions exclude.
- **`noexcept`**: destructors, move operations, and `swap` must be; mark others when you can guarantee no throw; it enables optimizations and communicates intent.
- **Fail fast**: throw or assert immediately; don't let bad state propagate into a confusing crash three layers down.

### 9. Comments

The shared comments doctrine (comment only what the code cannot say; *why* not *what*; delete commented-out code; TODOs with owner and ticket) is in [`../_shared/naming-and-comments.md`](../_shared/naming-and-comments.md). C++ adds:

- **`//` for implementation comments, `/** */` or `///` for Doxygen**: don't mix.
- **Explain template trickery**: what a `requires` clause enforces or why a `static_assert` exists is almost always worth a line.
- **`[[fallthrough]]`** for intentional switch fallthrough.

### 10. Modularity & Reusability

Structural design is owned by the `software-design` skill; apply it for Single Responsibility, minimizing coupling, narrow and stable interfaces, and DRY (the same *fact* in two places, not lookalikes). The C++-specific mechanics:

- **Header/source separation**: declarations in `.h`/`.hpp`, definitions in `.cpp`; inline templates and constexpr in headers; headers include only what their declarations need.
- **Namespaces reflect project structure**; don't dump everything into one namespace or the global one.
- **Enforce interfaces with the type system**: `explicit` on single-argument constructors, `[[nodiscard]]` where ignoring the result is a mistake, `= delete` on copy operations when copying makes no semantic sense.
- **Templates for compile-time polymorphism** when the type set is open-ended; constrain with concepts (C++20) for clear error messages.

### 11. Concurrency Safety

Skip this section for single-threaded code.

- **Protect shared state**: `std::mutex` with `std::lock_guard` or `std::scoped_lock`; prefer `std::scoped_lock` for multiple mutexes; it locks all at once, avoiding deadlock.
- **Minimize critical sections**: allocations, I/O, and computation outside the lock.
- **Higher-level primitives first**: `std::async`, `std::jthread` (C++20), `std::atomic` for simple flags; raw mutexes only when needed.
- **Const means thread-safe**: the standard library assumes `const` member functions are concurrently callable, so protect mutated internals (caches, lazy init) with `mutable std::mutex`.
- **Data races are UB**: two threads, same non-atomic variable, at least one write. No exceptions. Catch with `-fsanitize=thread`.

### 12. Security & Defensive Practices

- **Bounds checking**: `.at()` over `operator[]` at trust boundaries; `std::span` to pass arrays with their sizes; sanitizers (`-fsanitize=address,undefined`) in test builds.
- **Integer safety**: check overflow before arithmetic on untrusted integers; heed signed/unsigned comparison warnings; `<cstdint>` fixed-width types when size matters.
- **No format string injection**: never pass user input as the format argument of `printf`-family functions; use `std::format` (C++20) or `fmt::format`.
- **Secrets out of code**: no hardcoded API keys, passwords, or tokens; use environment variables or restricted-permission config files instead.
- **Validate all external input** (file data, network payloads, command-line arguments) as hostile until validated.
- **Warnings as errors**: `-Wall -Wextra -Wpedantic` minimum, `-Werror` in CI, clang-tidy with a project-appropriate set of checks.

## How to Deliver the Review

Review mode only: the response structure (brief assessment; the improved code as a complete, compilable replacement with its `#include` directives; key changes by category) and the mostly-fine and narrow-request provisions are defined in [`../_shared/review-conduct.md`](../_shared/review-conduct.md). For code in a larger codebase, the specifics to ask about first are the C++ standard version, compiler, project conventions (naming style, error handling strategy, smart pointer policy), and build system.
