// Mini framework de testes do runtime (sem dependências externas).
#pragma once

#include <chrono>
#include <cstdio>
#include <exception>
#include <functional>
#include <string>
#include <vector>

namespace rt_test {

struct Case {
    const char* name;
    std::function<void()> fn;
};

inline std::vector<Case>& cases() {
    static std::vector<Case> c;
    return c;
}

struct Failure {
    std::string msg;
};

struct Register {
    Register(const char* name, std::function<void()> fn) { cases().push_back({name, std::move(fn)}); }
};

inline long long now_ms() {
    using namespace std::chrono;
    return duration_cast<milliseconds>(steady_clock::now().time_since_epoch()).count();
}

// Executa todos os casos (ou só os cujo nome contém filtro). Retorna 0 se todos passaram.
inline int run_all(int argc, char** argv) {
    std::string filter = argc > 1 ? argv[1] : "";
    int failed = 0, run = 0;
    for (auto& c : cases()) {
        if (!filter.empty() && std::string(c.name).find(filter) == std::string::npos) continue;
        ++run;
        long long t0 = now_ms();
        try {
            c.fn();
            std::printf("[PASS] %s (%lld ms)\n", c.name, now_ms() - t0);
        } catch (const Failure& f) {
            ++failed;
            std::printf("[FAIL] %s: %s\n", c.name, f.msg.c_str());
        } catch (const std::exception& ex) {
            ++failed;
            std::printf("[FAIL] %s: excecao %s\n", c.name, ex.what());
        }
        std::fflush(stdout);
    }
    std::printf("== %d casos, %d falhas\n", run, failed);
    return failed == 0 && run > 0 ? 0 : 1;
}

}  // namespace rt_test

#define RT_CONCAT2(a, b) a##b
#define RT_CONCAT(a, b) RT_CONCAT2(a, b)
#define TEST_CASE(name)                                                      \
    static void RT_CONCAT(test_fn_, __LINE__)();                             \
    static rt_test::Register RT_CONCAT(test_reg_, __LINE__)(name, RT_CONCAT(test_fn_, __LINE__)); \
    static void RT_CONCAT(test_fn_, __LINE__)()

#define CHECK(cond)                                                                                 \
    do {                                                                                            \
        if (!(cond))                                                                                \
            throw rt_test::Failure{std::string(__FILE__) + ":" + std::to_string(__LINE__) + ": " + #cond}; \
    } while (0)

#define CHECK_MSG(cond, msg)                                                                         \
    do {                                                                                             \
        if (!(cond))                                                                                 \
            throw rt_test::Failure{std::string(__FILE__) + ":" + std::to_string(__LINE__) + ": " + #cond + \
                                   " — " + (msg)};                                                   \
    } while (0)
