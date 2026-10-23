// minipar_rt — Value: dado copiável que cruza tarefas locais e remotas (C-FJ-v1 §2.4).
// Header-only, C++20, só biblioteca padrão.
#pragma once

#include <concepts>
#include <cstdint>
#include <sstream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <utility>
#include <variant>
#include <vector>

namespace minipar_rt {

class Value {
public:
    enum class Kind { None, Int, Float, Bool, String, List };
    using List = std::vector<Value>;

    Value() = default;
    Value(std::nullptr_t) {}
    template <std::integral T>
        requires(!std::same_as<std::remove_cv_t<T>, bool> && !std::same_as<std::remove_cv_t<T>, char>)
    Value(T v) : data_(static_cast<std::int64_t>(v)) {}
    Value(double v) : data_(v) {}
    Value(float v) : data_(static_cast<double>(v)) {}
    Value(bool v) : data_(v) {}
    Value(const char* v) : data_(std::string(v ? v : "")) {}
    Value(std::string v) : data_(std::move(v)) {}
    Value(List v) : data_(std::move(v)) {}

    Kind kind() const { return static_cast<Kind>(data_.index()); }
    bool is_none() const { return kind() == Kind::None; }
    bool is_int() const { return kind() == Kind::Int; }
    bool is_float() const { return kind() == Kind::Float; }
    bool is_number() const { return is_int() || is_float(); }
    bool is_bool() const { return kind() == Kind::Bool; }
    bool is_string() const { return kind() == Kind::String; }
    bool is_list() const { return kind() == Kind::List; }

    std::int64_t as_int() const {
        if (is_int()) return std::get<std::int64_t>(data_);
        if (is_float()) return static_cast<std::int64_t>(std::get<double>(data_));
        throw_kind("int");
    }
    double as_number() const {
        if (is_float()) return std::get<double>(data_);
        if (is_int()) return static_cast<double>(std::get<std::int64_t>(data_));
        throw_kind("number");
    }
    bool as_bool() const {
        if (is_bool()) return std::get<bool>(data_);
        throw_kind("bool");
    }
    const std::string& as_string() const {
        if (is_string()) return std::get<std::string>(data_);
        throw_kind("string");
    }
    const List& as_list() const {
        if (is_list()) return std::get<List>(data_);
        throw_kind("list");
    }
    List& as_list() {
        if (is_list()) return std::get<List>(data_);
        throw_kind("list");
    }

    static const char* kind_name(Kind k) {
        switch (k) {
            case Kind::None: return "none";
            case Kind::Int: return "int";
            case Kind::Float: return "float";
            case Kind::Bool: return "bool";
            case Kind::String: return "string";
            case Kind::List: return "list";
        }
        return "?";
    }

    friend bool operator==(const Value& a, const Value& b) { return a.data_ == b.data_; }

    // Representação legível (igual à impressão de listas do MiniPar: [1, 2, 3]).
    std::string to_display() const {
        std::ostringstream os;
        write_display(os);
        return os.str();
    }

private:
    [[noreturn]] void throw_kind(const char* wanted) const {
        throw std::invalid_argument(std::string("minipar_rt::Value: esperado ") + wanted + ", recebido " +
                                    kind_name(kind()));
    }

    void write_display(std::ostringstream& os) const {
        switch (kind()) {
            case Kind::None: os << "none"; break;
            case Kind::Int: os << std::get<std::int64_t>(data_); break;
            case Kind::Float: os << std::get<double>(data_); break;
            case Kind::Bool: os << (std::get<bool>(data_) ? "true" : "false"); break;
            case Kind::String: os << std::get<std::string>(data_); break;
            case Kind::List: {
                os << '[';
                const auto& l = std::get<List>(data_);
                for (std::size_t i = 0; i < l.size(); ++i) {
                    if (i) os << ", ";
                    l[i].write_display(os);
                }
                os << ']';
                break;
            }
        }
    }

    std::variant<std::monostate, std::int64_t, double, bool, std::string, List> data_;
};

using TaskArgs = std::vector<Value>;

// ---- to_value: tipos C++ -> Value -------------------------------------------------------------

inline Value to_value(const Value& v) { return v; }
inline Value to_value(Value&& v) { return std::move(v); }
inline Value to_value(const char* v) { return Value(v); }
inline Value to_value(const std::string& v) { return Value(v); }
inline Value to_value(bool v) { return Value(v); }
inline Value to_value(double v) { return Value(v); }
inline Value to_value(float v) { return Value(v); }
template <std::integral T>
    requires(!std::same_as<std::remove_cv_t<T>, bool>)
Value to_value(T v) { return Value(static_cast<std::int64_t>(v)); }
template <typename T>
Value to_value(const std::vector<T>& v) {
    Value::List out;
    out.reserve(v.size());
    for (const auto& item : v) out.push_back(to_value(item));
    return Value(std::move(out));
}

// ---- value_cast: Value -> tipos C++ ----------------------------------------------------------

template <typename T>
struct ValueCast;

template <typename T>
T value_cast(const Value& v) { return ValueCast<std::remove_cvref_t<T>>::from(v); }

template <>
struct ValueCast<Value> {
    static Value from(const Value& v) { return v; }
};
template <>
struct ValueCast<bool> {
    static bool from(const Value& v) { return v.as_bool(); }
};
template <>
struct ValueCast<double> {
    static double from(const Value& v) { return v.as_number(); }
};
template <>
struct ValueCast<float> {
    static float from(const Value& v) { return static_cast<float>(v.as_number()); }
};
template <>
struct ValueCast<std::string> {
    static std::string from(const Value& v) { return v.as_string(); }
};
template <std::integral T>
    requires(!std::same_as<T, bool>)
struct ValueCast<T> {
    static T from(const Value& v) { return static_cast<T>(v.as_int()); }
};
template <typename T>
struct ValueCast<std::vector<T>> {
    static std::vector<T> from(const Value& v) {
        std::vector<T> out;
        out.reserve(v.as_list().size());
        for (const auto& item : v.as_list()) out.push_back(value_cast<T>(item));
        return out;
    }
};

}  // namespace minipar_rt
