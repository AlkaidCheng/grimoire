---
name: cpp-code-review
description: Review and improve C++ code for quality, style, and correctness. Use this skill whenever the user asks to review, refactor, clean up, lint, improve, or critique C++ code. Also trigger when the user shares C++ code and asks to "make it better", "fix this", "check my code", "follow best practices", or mentions clang-format, clang-tidy, modern C++, RAII, smart pointers, const correctness, or code quality. Trigger for any request involving C++ code improvement, even partial — such as "add const", "fix memory management", "modernize this code", or "make this more readable". If the user pastes C++ code without explicit instructions but it clearly needs cleanup, offer to review it using this skill. Also trigger for .cpp, .h, .hpp, .cc, or .cxx files.
---

# C++ Code Review & Improvement

Review and improve C++ code to be clean, correct, well-structured, and production-ready. Every change should have a reason — improve clarity, prevent bugs, enforce safety, or reduce complexity. Never change code just to change it.

Default to modern C++ (C++17 or later) unless the user specifies a standard. Ask about the target standard if the codebase context is ambiguous and the distinction matters for the review.

## Review Checklist

Work through these criteria in order. Each one builds on the previous — formatting and naming first so the code is readable, then types and documentation so intent is clear, then safety, logic, and design.

### 1. Formatting & Style

Use clang-format for automated formatting. Beyond what clang-format handles, enforce these conventions:

- **Includes**: Group into related headers, C system headers, C++ standard library, third-party, and project-local — separated by blank lines, each group sorted alphabetically. Use `#include <header>` for system/library headers and `#include "header.h"` for project headers. Remove unused includes. Prefer forward declarations in headers when the full definition isn't needed.
- **Naming**: `PascalCase` for types (classes, structs, enums, type aliases). `snake_case` for functions, variables, and namespaces. `kPascalCase` or `UPPER_SNAKE_CASE` for constants (pick one and be consistent). `snake_case` for file names. Leading underscore or trailing underscore for private members — trailing is safer since leading underscore + capital letter is reserved.
- **Braces**: Opening brace on the same line as the statement (K&R / "attach" style) for functions, control flow, and classes. Always use braces for single-line `if`/`for`/`while` bodies — the "goto fail" class of bugs is not worth saving one line.
- **Namespaces**: Don't indent namespace bodies. Use `// namespace foo` closing comments for long namespace blocks. Never use `using namespace` in headers. Minimize its use in source files — prefer explicit namespacing or targeted `using` declarations.

### 2. Modern C++ & Type Safety

Write code that leverages the type system to catch bugs at compile time, not runtime.

- **Use `auto` judiciously**: `auto` is great when the type is obvious from context (`auto it = map.find(key)`) or painfully long (`auto result = some_template_function<Args...>()`). Don't use `auto` when it hides the type and the reader needs to know it to understand the code.
- **Prefer `enum class` over plain `enum`**: Scoped enums prevent implicit conversions and name collisions.
- **Use `[[nodiscard]]`**: On functions where ignoring the return value is almost certainly a bug (error codes, newly allocated resources, computation results).
- **Prefer `std::optional`** over sentinel values (`-1`, `nullptr` as "not found"). It makes the "might not have a value" contract explicit.
- **Use `constexpr` and `consteval`**: For values and functions that can be computed at compile time. Prefer `constexpr` over `#define` for constants.
- **`nullptr` over `NULL` or `0`**: Always. `NULL` is a macro and `0` is an integer — both can cause overload resolution surprises.
- **Structured bindings**: Use `auto [key, value] = *it;` for pairs and tuples to improve readability (C++17).
- **`std::string_view`** for read-only string parameters that don't need ownership. Avoids unnecessary copies while staying safe (as long as the view doesn't outlive the source).

**Example — before:**
```cpp
int find_user(vector<pair<int, string>>& users, string name) {
    for (int i = 0; i < users.size(); i++) {
        if (users[i].second == name)
            return users[i].first;
    }
    return -1;
}
```

**Example — after:**
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

Add Doxygen-compatible doc comments to all public functions, classes, and files. Skip documentation for trivially obvious private helpers or simple getters/setters.

**Structure:**
```cpp
/**
 * @brief Calculate weighted summary statistics for a range of values.
 *
 * Computes mean, standard deviation, and median. When weights are
 * provided, the mean and standard deviation are weighted accordingly.
 *
 * @param values  Input values. Must be non-empty.
 * @param weights Weights corresponding to each value. Must be the same
 *                size as @p values when provided. Pass an empty vector
 *                for equal weighting.
 *
 * @return A Metrics struct containing mean, std, and median fields.
 *
 * @throws std::invalid_argument If @p values is empty or sizes mismatch.
 *
 * @note Thread-safe if called with distinct data.
 *
 * @code
 * auto stats = calculate_metrics({1.0, 2.0, 3.0});
 * assert(stats.mean == 2.0);
 * @endcode
 */
Metrics calculate_metrics(
    std::span<const double> values,
    std::span<const double> weights = {});
```

**Rules:**
- `@brief` for the one-line summary. Extended description follows after a blank line.
- Document every parameter with `@param`, every return with `@return`, and every thrown exception with `@throws`.
- Use `@note` for thread-safety guarantees, performance characteristics, or important caveats.
- Use `@code` / `@endcode` for usage examples when the interface isn't self-explanatory.
- For classes, document the class purpose above the class declaration. Document non-obvious member functions individually.
- Header files should have a file-level `@file` / `@brief` comment at the top.

### 4. Variable & Function Naming

Names are the most important documentation. A good name eliminates the need for a comment.

- **Be specific**: `retry_count` not `cnt`, `user_email` not `data`, `max_connections` not `n`. The name should tell you what it holds, not just what type it is.
- **Functions describe actions**: `fetch_user_profile()`, `validate_email()`, `parse_config_file()`. Start with a verb. Getters can omit the verb when it's obvious: `size()`, `empty()`, `name()`.
- **Booleans read as predicates**: `is_valid`, `has_permission`, `should_retry`. For functions returning bool: `is_empty()`, `contains()`, `has_children()`.
- **Avoid generic names**: `data`, `info`, `result`, `tmp`, `val`, `obj` — these almost always have a more descriptive alternative. Exception: very short scopes like a 1-line lambda capture.
- **Match domain language**: If the domain calls it a "ledger", don't call it `record_list`. Use the vocabulary your team or codebase uses.
- **Template parameters**: Single uppercase letters (`T`, `U`) for simple cases. Descriptive names for constrained parameters: `Container`, `Predicate`, `Allocator`.
- **Avoid Hungarian notation**: Don't prefix types onto names (`strName`, `iCount`, `pUser`). The type system already tracks types. Exception: `m_` or trailing `_` for member variables is acceptable and common.

### 5. Code Efficiency

C++ gives you control over performance. Use it thoughtfully — optimize where it matters, not everywhere.

- **Pass by const reference for non-trivial types**: `const std::string&` instead of `std::string` for input parameters. Use `std::string_view` when ownership isn't needed. Pass by value when you're going to move from or copy anyway (sink parameters).
- **Move semantics**: Use `std::move` on values you're done with. Implement move constructors and move assignment for resource-owning types. Return local objects by value — the compiler applies NRVO.
- **Reserve containers**: Call `reserve()` on vectors when you know the final size. Avoids repeated reallocations during `push_back` loops.
- **Prefer algorithms over raw loops**: `std::find_if`, `std::transform`, `std::accumulate`, `std::ranges::` (C++20) express intent more clearly and are often better optimized. Use raw loops when the algorithm version is more complex than the loop.
- **Avoid unnecessary copies**: Watch for accidental copies in range-for loops (`for (auto x : vec)` copies each element — use `const auto&`). Watch for copies from `std::map::operator[]` vs `find()`.
- **Choose the right container**: `std::vector` is the default. `std::unordered_map` / `std::unordered_set` for O(1) lookup. `std::array` for fixed-size. `std::deque` for front-insertion. `std::flat_map` (C++23) or sorted `std::vector` for small ordered maps.
- **Avoid premature optimization**: Don't add complexity for speed improvements you haven't measured. If performance matters, profile first with perf, Valgrind, or a sampling profiler, then optimize the bottleneck.

### 6. Code Readability

Code is read far more often than it is written. Optimize for the reader.

- **Keep functions short**: A function should do one thing. If you need a comment to separate "phases" inside a function, those phases are probably separate functions.
- **Early returns**: Flatten nested conditionals by returning early for edge cases or invalid inputs. Avoid deep nesting — if you're past 3 levels of indentation, refactor.
- **Limit line complexity**: If a single expression requires a comment to explain what it does, break it into named intermediate variables. This is especially important with template-heavy code.
- **Consistent patterns**: Within a module, handle similar operations the same way. Don't error-check with exceptions in one function and return codes in the next for the same kind of operation.
- **Minimize preprocessor use**: Prefer `constexpr`, `consteval`, `if constexpr`, and templates over `#ifdef` chains. Macros are a last resort for things the language can't express (e.g., `__FILE__`, `__LINE__` capture).
- **Keep headers clean**: Minimize what headers expose. Forward declare aggressively. Use the PIMPL idiom for complex classes to reduce compilation dependencies.

### 7. Memory Safety & Resource Management (RAII)

C++ makes memory safety your responsibility. RAII is the primary tool — if you own a resource, tie its lifetime to a scope.

- **Smart pointers over raw pointers**: `std::unique_ptr` for sole ownership (the default), `std::shared_ptr` only when ownership is genuinely shared. Raw pointers are fine for non-owning observation, but never for ownership.
- **`std::make_unique` / `std::make_shared`**: Prefer these over direct `new`. They're exception-safe and more concise.
- **No naked `new`/`delete`**: If you see `new` outside a factory function or custom allocator, it's almost always wrong. If you see `delete` anywhere outside a destructor or custom deleter, it's almost certainly wrong.
- **Rule of Zero/Five**: If your class doesn't manage resources directly, don't declare any special members (destructor, copy/move constructors and assignment) — the compiler-generated defaults are correct. If you manage a resource, implement all five or explicitly `= delete` the ones you don't support.
- **`const` correctness**: Mark everything `const` that doesn't need to mutate — member functions, local variables, parameters, return values from getters. `const` is documentation and a compile-time safety net.
- **Avoid dangling**: Don't return references or pointers to locals. Don't hold iterators across container modifications. Be careful with `std::string_view` and `std::span` — they don't extend the lifetime of the underlying data.
- **Use `std::span`** (C++20) for non-owning array views instead of raw pointer + size pairs.

**Example — before:**
```cpp
class ConnectionPool {
    Connection** connections;
    int size;
public:
    ConnectionPool(int n) {
        size = n;
        connections = new Connection*[n];
        for (int i = 0; i < n; i++)
            connections[i] = new Connection();
    }
    ~ConnectionPool() {
        for (int i = 0; i < size; i++)
            delete connections[i];
        delete[] connections;
    }
};
```

**Example — after:**
```cpp
class ConnectionPool {
public:
    explicit ConnectionPool(std::size_t pool_size)
        : connections_(pool_size)
    {
        for (auto& conn : connections_) {
            conn = std::make_unique<Connection>();
        }
    }

    // Rule of Zero — no destructor, no copy/move declarations needed.
    // std::vector<std::unique_ptr<...>> handles everything.

private:
    std::vector<std::unique_ptr<Connection>> connections_;
};
```

### 8. Error Handling & Edge Cases

Handle what's likely, document what's possible, and don't paper over bugs.

- **Pick an error strategy and be consistent**: Exceptions for truly exceptional failures (I/O errors, resource exhaustion). `std::optional` or `std::expected` (C++23) for operations that can legitimately have no result. Error codes for performance-critical paths or C interop. Don't mix strategies randomly within a module.
- **Validate inputs at boundaries**: Check inputs in public functions — the entry points where bad data arrives. Private helpers can trust their callers.
- **Throw meaningful exceptions**: Derive from `std::runtime_error` or `std::logic_error`. Include context in the message: `throw std::invalid_argument("ConnectionPool: pool_size must be > 0, got " + std::to_string(pool_size));`.
- **Exception safety guarantees**: Aim for the strong guarantee (operation succeeds or has no effect) for public interfaces. Basic guarantee (no leaks, invariants preserved) at minimum. Use the copy-and-swap idiom for strong exception-safe assignment.
- **Consider edge cases but don't over-engineer**: Handle empty containers, null pointers (when your interface accepts them), zero-size inputs, and boundary conditions that are plausible in normal use. Don't add defensive code for scenarios that can't happen given the function's preconditions.
- **`noexcept` when appropriate**: Destructors, move operations, and `swap` should be `noexcept`. Mark functions `noexcept` when you can guarantee they won't throw — it enables compiler optimizations and communicates intent.
- **Fail fast**: If something is wrong, throw or assert immediately. Don't let bad state propagate and manifest as a confusing crash three layers down.

### 9. Comments

Write comments only when the code can't speak for itself. Every comment is a maintenance burden — it can become a lie when the code changes.

- **Explain why, not what**: `// Retry with backoff because the upstream service rate-limits aggressively` is useful. `// Increment counter` is noise.
- **Delete commented-out code**: That's what version control is for.
- **TODOs are acceptable** if they include context: `// TODO(username): Remove after migration to v2 API (tracked in PROJ-1234)`. Orphan TODOs with no owner or ticket are clutter.
- **Header comments**: Use `//` for implementation comments, `/** */` or `///` for Doxygen documentation. Don't mix documentation and implementation comments.
- **Explain template trickery**: Template metaprogramming and SFINAE/concepts constraints are genuinely hard to read. A brief comment explaining what a `requires` clause enforces or why a `static_assert` exists is almost always worth it.
- **Mark intentional fallthrough**: Use `[[fallthrough]]` in switch statements.

### 10. Modularity & Reusability

Structure code so each piece is independently understandable, testable, and compilable.

- **Single Responsibility**: Each function does one thing. Each class represents one concept. Each file covers one cohesive area.
- **Minimize coupling**: Pass dependencies through constructor parameters or function arguments, not through globals or singletons. Use dependency injection for testability.
- **Header/source separation**: Declarations in `.h` / `.hpp`, definitions in `.cpp`. Inline templates and constexpr in headers. Keep headers minimal — include only what is necessary for the declarations.
- **Use namespaces**: Organize code into namespaces that reflect the project structure. Avoid dumping everything into a single namespace or the global namespace.
- **Design stable interfaces**: Prefer narrow interfaces. Use `explicit` on single-argument constructors. Use `[[nodiscard]]` on functions where ignoring the result is a mistake. Consider making classes non-copyable when copying doesn't make semantic sense (`= delete` the copy operations).
- **Templates for compile-time polymorphism**: When the set of types is open-ended, prefer templates over inheritance. Use concepts (C++20) to constrain templates and produce clear error messages.
- **DRY, but not at all costs**: Extract shared logic when the duplication is exact and meaningful. Don't force unrelated code into the same template specialization or base class just because it looks similar — that creates fragile coupling.

### 11. Concurrency Safety

If the code touches threads, verify these. Skip this section for single-threaded code.

- **Protect shared state**: Use `std::mutex` with `std::lock_guard` or `std::scoped_lock`. Prefer `std::scoped_lock` when locking multiple mutexes — it avoids deadlock by locking all at once.
- **Minimize critical sections**: Hold locks for the shortest duration possible. Do allocations, I/O, and computation outside the lock.
- **Prefer higher-level primitives**: `std::async`, `std::jthread` (C++20), `std::atomic` for simple flags. Drop to raw mutexes only when needed.
- **Const means thread-safe**: The standard library assumes `const` member functions are safe to call concurrently. If your `const` function mutates internal state (cached values, lazy init), protect that state with `mutable std::mutex`.
- **Avoid data races**: If two threads can access the same non-atomic variable and at least one writes, that's undefined behavior — no exceptions, no "it works on my machine." Use thread sanitizer (`-fsanitize=thread`) to catch these.

### 12. Security & Defensive Practices

These are easy to miss in review but critical in production.

- **Bounds checking**: Use `.at()` instead of `operator[]` at trust boundaries. Use `std::span` to pass arrays with their sizes. Enable sanitizers (`-fsanitize=address,undefined`) in test builds.
- **Integer safety**: Check for overflow before arithmetic on untrusted integers. Be careful with signed/unsigned comparisons — the compiler warns about these for a reason. Use `<cstdint>` fixed-width types when the size matters.
- **No format string injection**: Never pass user input as the first argument to `printf`-family functions. Use `std::format` (C++20) or `fmt::format` instead.
- **Secrets out of code**: No hardcoded API keys, passwords, or tokens. Use environment variables or configuration files with restricted permissions.
- **Input validation**: Validate all external input — file data, network payloads, command-line arguments. Assume external data is hostile until validated.
- **Compiler warnings as errors**: Build with `-Wall -Wextra -Wpedantic` at minimum. Treat warnings as errors (`-Werror`) in CI. Run clang-tidy with a project-appropriate set of checks.

## How to Deliver the Review

When reviewing code, structure your response as follows:

1. **Start with a brief overall assessment** — one or two sentences on the general quality and the most important issue.
2. **Present the improved code** as a complete, compilable replacement. Don't make the user stitch fragments together. Include the necessary `#include` directives.
3. **Summarize key changes** — group by category (style, safety, logic, structure) and explain the reasoning briefly. Focus on the non-obvious changes. Don't list every renamed variable — the diff speaks for itself.

If the code is mostly fine and only needs minor adjustments, say so. Not every review needs a rewrite. If only specific improvements were requested (e.g., "add const"), focus on those but flag any glaring issues you notice along the way.

When the code is part of a larger codebase, ask about the C++ standard version, compiler, project conventions (naming style, error handling strategy, smart pointer policy), and build system before proposing changes that might conflict.
