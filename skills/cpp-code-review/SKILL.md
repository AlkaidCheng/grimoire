---
name: cpp-code-review
description: The coding standard for C++ (clang-format style, the naming convention, modern C++ and type safety, RAII and resource management, const-correctness, error handling, threads, floating-point formatting, toolchain minimums, and Python bindings) to follow while writing C++ and to apply when reviewing it. Use when writing, implementing, or refactoring C++, or when asked to review, lint, improve, or critique it ("add const", "fix memory management", "modernize this", "make this more readable"; clang-format, clang-tidy, smart pointers), or for any .cpp/.h/.hpp/.cc/.cxx file or Python extension module (pybind11, nanobind). If C++ is pasted without instructions but clearly needs work, offer a review. For structural design (decomposition, interfaces, coupling) use software-design; for language-agnostic structural or artifact cleanup defer to code-polishing; for Python use python-code-review.
---

# C++ Code Review & Improvement

The coding standard for C++: how it should be written and how it should be reviewed. The language-agnostic conduct is defined in [`../_shared/review-conduct.md`](../_shared/review-conduct.md) and applies here in full: the change ethos (every change needs a reason; never change code just to change it) and the two working modes, **authoring** (apply the standard as you write; the default when implementing or modifying C++) and **reviewing** (audit against it and return an improved version per "How to Deliver the Review").

The standard's aim is code that is easy to maintain: correct today and cheap to read, change, and test tomorrow. Default to modern C++ (C++17 or later) unless the user specifies a standard; ask when the codebase context is ambiguous and the distinction matters.

## Review Checklist

Work through in order: formatting and naming first (readability), then types and documentation (intent), then safety, logic, and design.

### 1. Formatting & Style

Use clang-format with a committed `.clang-format` (a named base style plus the project's column limit), so every editor and CI run formats alike. Beyond what it handles:

- **Includes**: group as related header, C system, C++ standard library, third-party, project-local; blank-line separated, each group sorted alphabetically. `#include <header>` for system/library, `#include "header.h"` for project. Remove unused includes; prefer forward declarations in headers when the full definition isn't needed.
- **Naming convention**: one scheme per codebase. An established scheme wins and new code does not add a second. Without one, follow the standard library and the C++ Core Guidelines (NL.10, underscore style):
  - `PascalCase` for types (classes, structs, enums, type aliases, concepts) and template parameters;
  - `snake_case` for functions, variables, parameters, data members, namespaces, and file names (`order_book.hpp`, `order_book.cpp`);
  - `kPascalCase` for constants and `enum class` enumerators;
  - a trailing underscore on a class's private data members (`size_`), none on a plain struct's public ones; a leading underscore before a capital letter is reserved;
  - `UPPER_SNAKE_CASE` with a project prefix for macros only.

  Other schemes (camelCase functions as in LLVM and Qt, PascalCase functions as in Google's guide) are conventions to follow where a codebase has one, not standards to bring into one.
- **Braces**: opening brace on the same line (K&R / "attach") for functions, control flow, and classes. Always brace single-line `if`/`for`/`while` bodies: the "goto fail" bug class isn't worth one saved line.
- **Namespaces**: don't indent bodies; `// namespace foo` closing comments on long blocks. Never `using namespace` in headers; minimize in source files; prefer explicit namespacing or targeted `using` declarations.

### 2. Modern C++ & Type Safety

Leverage the type system to catch bugs at compile time.

- **`auto` judiciously**: fine when the type is obvious (`auto it = map.find(key)`) or painfully long; not when it hides a type the reader needs.
- **`enum class` over plain `enum`**: prevents implicit conversions and name collisions.
- **`[[nodiscard]]`** where ignoring the return is almost certainly a bug (error codes, newly allocated resources, computation results).
- **`std::optional`** over sentinel values (`-1`, `nullptr` as "not found"): makes the contract explicit. Where a packed array of indices cannot afford an optional per element, the sentinels are named constants declared beside the array they mark (`kNoParent`), never bare `-1` or `-2` at the use sites.
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

The language-agnostic naming doctrine (names as the primary documentation, specific over generic, the representation a value is, verb-led functions, one verb per operation, booleans as predicates, units on quantities, one spelling per idea, domain vocabulary) is in [`../_shared/naming-and-comments.md`](../_shared/naming-and-comments.md). C++ adds:

- **Getters may omit the verb**: `size()`, `empty()`, `name()`.
- **Template parameters**: single uppercase (`T`, `U`) for simple cases; descriptive names for constrained ones (`Container`, `Predicate`, `Allocator`).
- **No Hungarian notation** (`strName`, `iCount`, `pUser`); a member prefix such as `m_` only where the codebase already uses one.
- **No identifier that reads as a language word**: `final`, `override`, `import`, and `module` are ordinary identifiers to the compiler but read as specifiers (`options.final[i]`), so a flag is `is_final`. No name a standard macro owns (`assert`, `errno`).
- **No name shared with a namespace alias in scope**: beside `namespace fs = std::filesystem;` a sampling-rate parameter `fs` compiles, because lookup before `::` ignores variables, but `fs::path` next to `fs * duration` reads as one name. Rename the alias or spell the namespace out.
- **A type is named for what it holds**: a struct of indices into another container, not its elements, says so (`SelectedRows`, not `Order`). The object a function or class is built around never gets a single letter (`table_`, not `t_`); single letters are for loop indices.

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
- **Complexity tripwires**: clang-tidy's `readability-function-cognitive-complexity` and `readability-function-size` flag functions to split; the three measures and their reduction moves are in the shared doctrine.
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
- **One language per directory**: in a project that mixes languages, the C++ sits in its own tree (for a Python package, `cpp/<component>/` beside `src/`), never among the other language's modules, and the build points at it. The core includes no binding header and uses no binding type (`std::int64_t`, not `pybind11::ssize_t`), so it builds and can be tested without the interpreter; the binding is a file of its own (section 15).
- **Enforce interfaces with the type system**: `explicit` on single-argument constructors, `[[nodiscard]]` where ignoring the result is a mistake, `= delete` on copy operations when copying makes no semantic sense.
- **Templates for compile-time polymorphism** when the type set is open-ended; constrain with concepts (C++20) for clear error messages.

### 11. Concurrency Safety

Skip this section for single-threaded code.

- **Protect shared state**: `std::mutex` with `std::lock_guard` or `std::scoped_lock`; prefer `std::scoped_lock` for multiple mutexes; it locks all at once, avoiding deadlock.
- **Minimize critical sections**: allocations, I/O, and computation outside the lock.
- **Higher-level primitives first**: `std::async`, `std::jthread` (C++20), `std::atomic` for simple flags; raw mutexes only when needed.
- **Const means thread-safe**: the standard library assumes `const` member functions are concurrently callable, so protect mutated internals (caches, lazy init) with `mutable std::mutex`.
- **Data races are UB**: two threads, same non-atomic variable, at least one write. No exceptions. Catch with `-fsanitize=thread`.
- **Join every thread on every path**: a `std::thread` still joinable when destroyed calls `std::terminate`, and starting one can throw `std::system_error`. A loop that starts workers therefore joins the ones already running, or does the work on the calling thread, when a later start fails. `std::jthread` (C++20) joins on destruction.
- **No exception leaves a thread's function**: one that does calls `std::terminate`. Catch it in the worker, carry it back as `std::exception_ptr`, and rethrow it on the joining thread.
- **Results independent of the thread count**: give each worker a contiguous share of the input and its own output buffer, combine the buffers in input order, and test that 1 and N threads give identical output.

### 12. Security & Defensive Practices

- **Bounds checking**: `.at()` over `operator[]` at trust boundaries; `std::span` to pass arrays with their sizes; sanitizers (`-fsanitize=address,undefined`) in test builds.
- **Integer safety**: check overflow before arithmetic on untrusted integers; heed signed/unsigned comparison warnings; `<cstdint>` fixed-width types when size matters. Before narrowing a value to the type an external format or API stores it in (a 64-bit id written to a 32-bit field), check it against that type's `std::numeric_limits` and refuse with the value: `static_cast` wraps without a word.
- **No format string injection**: never pass user input as the format argument of `printf`-family functions; use `std::format` (C++20) or `fmt::format`.
- **Secrets out of code**: no hardcoded API keys, passwords, or tokens; use environment variables or restricted-permission config files instead.
- **Validate all external input** (file data, network payloads, command-line arguments) as hostile until validated.
- **Warnings as errors**: `-Wall -Wextra -Wpedantic` minimum, `-Werror` in CI, clang-tidy with a project-appropriate set of checks.

### 13. Floating Point and Number Formatting

- **NaN fails every comparison except `!=`**: `x != 0` counts NaN as nonzero and `a == b` says two NaNs differ. A decision on a floating-point input that can be NaN or infinite tests `std::isfinite` first and handles those values on purpose. `-0.0 == 0.0` holds, though the two print differently.
- **Formatting routines differ on non-finite values**: `std::to_chars` is locale-independent and gives `printf`'s digits for finite numbers, but standard libraries spell NaN and infinity in their own ways (some write a negative NaN as `-nan(ind)`). Output that must match a reference written with `printf` formats non-finite values with the call the reference uses.
- **Test each class of value**: finite of both signs, `+0.0` and `-0.0`, both infinities, NaN of both signs, subnormals, and the type's extremes. When C++ replaces a reference implementation, compare the two on these values: the reference's semantics for them (NaN comparisons, overflow, rounding) are part of the contract the port inherits.

### 14. Toolchain and Platform

- **A library feature has its own minimum toolchain**, apart from the language standard: `-std=c++17` accepts floating-point `std::to_chars`, but only GCC 11's libstdc++, libc++ 14 (on macOS, deployment target 13.3), and MSVC 19.24 provide it. Check each library feature the code uses against cppreference's compiler-support tables, and state the resulting minimum where the build is configured and where users read the install requirements.
- **Set the platform minimum explicitly**: build helpers apply their own default when the environment sets none (pybind11's setup helpers add an old macOS deployment target), and that default can be older than a feature needs.
- **Published binaries carry the minimum in their tags**: from macOS 11 on, a wheel's platform tag keeps only the major version, so a binary that needs 13.3 is tagged 13.0 and installs where it cannot load. Build published wheels for the next major version (14.0).

### 15. Python Bindings

Skip this section for code without a binding. The examples use pybind11; nanobind and the CPython API raise the same points.

- **A thin binding**: it checks what the core trusts (dimensions, lengths, dtypes), converts, calls the core, and converts back; no rule of the domain lives in it.
- **No silent conversion of arrays**: an array argument bound without `.noconvert()` is converted, which copies the whole array when its dtype or layout differs, and with one overload per dtype lets an array of another dtype reach whichever overload accepts it after conversion. Refuse instead, and leave the conversion to the caller, where it is visible.
- **Borrowed memory lives for the call**: a pointer into an argument array is valid until the bound function returns, and the core never keeps one.
- **Release the interpreter lock around the core only**: after every Python object has been read and before any is created (`pybind11::gil_scoped_release` in its own scope).
- **One copy into the result**: a large text or array result is built in place (`PyBytes_FromStringAndSize(nullptr, size)` filled from the core's buffers), not through a `std::string` that the conversion copies again.
- **Python names on the Python side**: bound functions and keyword arguments follow PEP 8 (`snake_case`) whatever the C++ scheme, and a `.pyi` stub beside the module in the package declares them with their dtypes.

## Quick Checklist Before Finishing

The items most easily missed while writing; each points back to its section.

- [ ] Names follow the codebase's scheme, or section 1's default; none reads as a language word or shares a namespace alias; sentinels are named constants (sections 1, 2, 4)
- [ ] Every `if`/`for`/`while` body is braced, and includes are grouped in order (section 1)
- [ ] `[[nodiscard]]` on every function whose result must be used: a success flag, a computed value (section 2)
- [ ] Public declarations documented (section 3)
- [ ] Every narrowing conversion range-checked; NaN and infinity handled on purpose in every floating-point decision (sections 12, 13)
- [ ] Every thread joined on every path; no exception leaves a worker; output identical at 1 and N threads (section 11)
- [ ] Each library feature's minimum toolchain stated in the build and the install requirements (section 14)
- [ ] Built with `-Wall -Wextra -Wpedantic` and no warnings; sanitizers in test builds where the toolchain has them (section 12)
- [ ] For a binding: the core is free of binding types, arrays are never converted silently, the interpreter lock is released around the core only, and the `.pyi` stub matches the bound names (sections 10, 15)

## How to Deliver the Review

Review mode only: the response structure (brief assessment; the improved code as a complete, compilable replacement with its `#include` directives; key changes by category) and the mostly-fine and narrow-request provisions are defined in [`../_shared/review-conduct.md`](../_shared/review-conduct.md). For code in a larger codebase, the specifics to ask about first are the C++ standard version, the compilers and platforms supported, project conventions (naming scheme, error handling strategy, smart pointer policy), and build system.
