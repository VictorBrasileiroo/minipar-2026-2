// minipar_rt — JSON estrito (subconjunto RFC 8259) para as mensagens do protocolo (C-FJ-v1 §2.6).
// Sem biblioteca externa. Rejeita entrada malformada com JsonError; nunca "conserta" dados.
#pragma once

#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <string>
#include <utility>
#include <variant>
#include <vector>

#include "value.hpp"

namespace minipar_rt {

struct JsonError : std::runtime_error {
    using std::runtime_error::runtime_error;
};

class Json {
public:
    enum class Kind { Null, Bool, Int, Float, String, Array, Object };  // mesma ordem do variant
    using Array = std::vector<Json>;
    using Object = std::vector<std::pair<std::string, Json>>;

    Json() = default;
    Json(std::nullptr_t) {}
    Json(bool b) : d_(b) {}
    Json(int v) : d_(static_cast<std::int64_t>(v)) {}
    Json(long v) : d_(static_cast<std::int64_t>(v)) {}
    Json(long long v) : d_(static_cast<std::int64_t>(v)) {}
    Json(unsigned v) : d_(static_cast<std::int64_t>(v)) {}
    Json(double v) : d_(v) {}
    Json(const char* s) : d_(std::string(s)) {}
    Json(std::string s) : d_(std::move(s)) {}
    Json(Array a) : d_(std::move(a)) {}
    Json(Object o) : d_(std::move(o)) {}

    Kind kind() const { return static_cast<Kind>(d_.index()); }
    bool is_object() const { return kind() == Kind::Object; }
    bool is_string() const { return kind() == Kind::String; }
    bool is_int() const { return kind() == Kind::Int; }
    bool is_array() const { return kind() == Kind::Array; }

    const std::string& str() const {
        if (!is_string()) throw JsonError("esperado string");
        return std::get<std::string>(d_);
    }
    std::int64_t integer() const {
        if (!is_int()) throw JsonError("esperado inteiro");
        return std::get<std::int64_t>(d_);
    }
    const Array& array() const {
        if (!is_array()) throw JsonError("esperado array");
        return std::get<Array>(d_);
    }
    const Object& object() const {
        if (!is_object()) throw JsonError("esperado objeto");
        return std::get<Object>(d_);
    }

    const Json* find(const std::string& key) const {
        if (!is_object()) return nullptr;
        for (const auto& kv : std::get<Object>(d_))
            if (kv.first == key) return &kv.second;
        return nullptr;
    }
    const Json& at(const std::string& key) const {
        const Json* j = find(key);
        if (!j) throw JsonError("campo ausente: " + key);
        return *j;
    }

    std::string dump() const {
        std::string out;
        write(out);
        return out;
    }

    static Json parse(const std::string& text) {
        Parser p{text.data(), text.data() + text.size(), 0};
        p.skip_ws();
        Json j = p.value();
        p.skip_ws();
        if (p.cur != p.end) throw JsonError("JSON invalido: conteudo apos o fim");
        return j;
    }

    // Value <-> Json (§2.6: float sempre com ponto/expoente, int sem; NaN/inf proibidos).
    static Json from_value(const Value& v) {
        switch (v.kind()) {
            case Value::Kind::None: return Json();
            case Value::Kind::Bool: return Json(v.as_bool());
            case Value::Kind::Int: return Json(static_cast<long long>(v.as_int()));
            case Value::Kind::Float: {
                double x = v.as_number();
                if (!std::isfinite(x)) throw JsonError("valor nao finito nao pode cruzar a rede");
                return Json(x);
            }
            case Value::Kind::String: return Json(v.as_string());
            case Value::Kind::List: {
                Array a;
                a.reserve(v.as_list().size());
                for (const auto& item : v.as_list()) a.push_back(from_value(item));
                return Json(std::move(a));
            }
        }
        return Json();
    }
    Value to_value() const {
        switch (kind()) {
            case Kind::Null: return Value();
            case Kind::Bool: return Value(std::get<bool>(d_));
            case Kind::Int: return Value(std::get<std::int64_t>(d_));
            case Kind::Float: return Value(std::get<double>(d_));
            case Kind::String: return Value(std::get<std::string>(d_));
            case Kind::Array: {
                Value::List l;
                l.reserve(std::get<Array>(d_).size());
                for (const auto& item : std::get<Array>(d_)) l.push_back(item.to_value());
                return Value(std::move(l));
            }
            case Kind::Object: throw JsonError("objeto JSON nao e um Value");
        }
        return Value();
    }

private:
    static constexpr int kMaxDepth = 64;

    struct Parser {
        const char* cur;
        const char* end;
        int depth;

        [[noreturn]] void fail(const char* what) { throw JsonError(std::string("JSON invalido: ") + what); }
        void skip_ws() {
            while (cur < end && (*cur == ' ' || *cur == '\t' || *cur == '\n' || *cur == '\r')) ++cur;
        }
        bool consume(const char* lit) {
            std::size_t n = std::strlen(lit);
            if (static_cast<std::size_t>(end - cur) >= n && std::memcmp(cur, lit, n) == 0) {
                cur += n;
                return true;
            }
            return false;
        }
        Json value() {
            if (cur >= end) fail("fim inesperado");
            switch (*cur) {
                case '{': return object();
                case '[': return array();
                case '"': return Json(string());
                case 't':
                    if (consume("true")) return Json(true);
                    fail("literal");
                case 'f':
                    if (consume("false")) return Json(false);
                    fail("literal");
                case 'n':
                    if (consume("null")) return Json();
                    fail("literal");
                default: return number();
            }
        }
        Json object() {
            if (++depth > kMaxDepth) fail("profundidade excessiva");
            ++cur;
            Object o;
            skip_ws();
            if (cur < end && *cur == '}') {
                ++cur;
                --depth;
                return Json(std::move(o));
            }
            for (;;) {
                skip_ws();
                if (cur >= end || *cur != '"') fail("chave esperada");
                std::string k = string();
                skip_ws();
                if (cur >= end || *cur != ':') fail("':' esperado");
                ++cur;
                skip_ws();
                for (const auto& kv : o)
                    if (kv.first == k) fail("chave duplicada");
                o.emplace_back(std::move(k), value());
                skip_ws();
                if (cur < end && *cur == ',') {
                    ++cur;
                    continue;
                }
                if (cur < end && *cur == '}') {
                    ++cur;
                    break;
                }
                fail("',' ou '}' esperado");
            }
            --depth;
            return Json(std::move(o));
        }
        Json array() {
            if (++depth > kMaxDepth) fail("profundidade excessiva");
            ++cur;
            Array a;
            skip_ws();
            if (cur < end && *cur == ']') {
                ++cur;
                --depth;
                return Json(std::move(a));
            }
            for (;;) {
                skip_ws();
                a.push_back(value());
                skip_ws();
                if (cur < end && *cur == ',') {
                    ++cur;
                    continue;
                }
                if (cur < end && *cur == ']') {
                    ++cur;
                    break;
                }
                fail("',' ou ']' esperado");
            }
            --depth;
            return Json(std::move(a));
        }
        static void put_utf8(std::string& s, std::uint32_t cp) {
            if (cp < 0x80) {
                s += static_cast<char>(cp);
            } else if (cp < 0x800) {
                s += static_cast<char>(0xC0 | (cp >> 6));
                s += static_cast<char>(0x80 | (cp & 0x3F));
            } else if (cp < 0x10000) {
                s += static_cast<char>(0xE0 | (cp >> 12));
                s += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
                s += static_cast<char>(0x80 | (cp & 0x3F));
            } else {
                s += static_cast<char>(0xF0 | (cp >> 18));
                s += static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
                s += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
                s += static_cast<char>(0x80 | (cp & 0x3F));
            }
        }
        std::uint32_t hex4() {
            if (end - cur < 4) fail("\\u incompleto");
            std::uint32_t v = 0;
            for (int i = 0; i < 4; ++i) {
                char c = *cur++;
                v <<= 4;
                if (c >= '0' && c <= '9') v |= static_cast<std::uint32_t>(c - '0');
                else if (c >= 'a' && c <= 'f') v |= static_cast<std::uint32_t>(c - 'a' + 10);
                else if (c >= 'A' && c <= 'F') v |= static_cast<std::uint32_t>(c - 'A' + 10);
                else fail("\\u invalido");
            }
            return v;
        }
        std::string string() {
            ++cur;  // aspas de abertura
            std::string s;
            for (;;) {
                if (cur >= end) fail("string nao terminada");
                unsigned char c = static_cast<unsigned char>(*cur++);
                if (c == '"') return s;
                if (c < 0x20) fail("caractere de controle em string");
                if (c != '\\') {
                    s += static_cast<char>(c);
                    continue;
                }
                if (cur >= end) fail("escape incompleto");
                char e = *cur++;
                switch (e) {
                    case '"': s += '"'; break;
                    case '\\': s += '\\'; break;
                    case '/': s += '/'; break;
                    case 'b': s += '\b'; break;
                    case 'f': s += '\f'; break;
                    case 'n': s += '\n'; break;
                    case 'r': s += '\r'; break;
                    case 't': s += '\t'; break;
                    case 'u': {
                        std::uint32_t cp = hex4();
                        if (cp >= 0xD800 && cp <= 0xDBFF) {
                            if (!consume("\\u")) fail("surrogate sem par");
                            std::uint32_t lo = hex4();
                            if (lo < 0xDC00 || lo > 0xDFFF) fail("surrogate invalido");
                            cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                        } else if (cp >= 0xDC00 && cp <= 0xDFFF) {
                            fail("surrogate invalido");
                        }
                        put_utf8(s, cp);
                        break;
                    }
                    default: fail("escape desconhecido");
                }
            }
        }
        Json number() {
            const char* start = cur;
            bool is_float = false;
            if (cur < end && *cur == '-') ++cur;
            if (cur >= end) fail("numero");
            if (*cur == '0') {
                ++cur;
            } else if (*cur >= '1' && *cur <= '9') {
                while (cur < end && *cur >= '0' && *cur <= '9') ++cur;
            } else {
                fail("valor inesperado");
            }
            if (cur < end && *cur == '.') {
                is_float = true;
                ++cur;
                if (cur >= end || *cur < '0' || *cur > '9') fail("fracao");
                while (cur < end && *cur >= '0' && *cur <= '9') ++cur;
            }
            if (cur < end && (*cur == 'e' || *cur == 'E')) {
                is_float = true;
                ++cur;
                if (cur < end && (*cur == '+' || *cur == '-')) ++cur;
                if (cur >= end || *cur < '0' || *cur > '9') fail("expoente");
                while (cur < end && *cur >= '0' && *cur <= '9') ++cur;
            }
            std::string txt(start, cur);
            if (!is_float) {
                errno = 0;
                char* e = nullptr;
                long long v = std::strtoll(txt.c_str(), &e, 10);
                if (errno == ERANGE || !e || *e) fail("inteiro fora do intervalo int64");
                return Json(v);
            }
            char* e = nullptr;
            double v = std::strtod(txt.c_str(), &e);
            if (!e || *e || !std::isfinite(v)) fail("real fora do intervalo");
            return Json(v);
        }
    };

    void write(std::string& out) const {
        switch (kind()) {
            case Kind::Null: out += "null"; break;
            case Kind::Bool: out += std::get<bool>(d_) ? "true" : "false"; break;
            case Kind::Int: out += std::to_string(std::get<std::int64_t>(d_)); break;
            case Kind::Float: {
                double x = std::get<double>(d_);
                if (!std::isfinite(x)) throw JsonError("valor nao finito");
                char buf[40];
                std::snprintf(buf, sizeof buf, "%.17g", x);
                out += buf;
                if (!std::strpbrk(buf, ".eE")) out += ".0";  // mantém o tipo float do outro lado
                break;
            }
            case Kind::String: write_string(out, std::get<std::string>(d_)); break;
            case Kind::Array: {
                out += '[';
                bool first = true;
                for (const auto& item : std::get<Array>(d_)) {
                    if (!first) out += ',';
                    first = false;
                    item.write(out);
                }
                out += ']';
                break;
            }
            case Kind::Object: {
                out += '{';
                bool first = true;
                for (const auto& kv : std::get<Object>(d_)) {
                    if (!first) out += ',';
                    first = false;
                    write_string(out, kv.first);
                    out += ':';
                    kv.second.write(out);
                }
                out += '}';
                break;
            }
        }
    }
    static void write_string(std::string& out, const std::string& s) {
        out += '"';
        for (unsigned char c : s) {
            switch (c) {
                case '"': out += "\\\""; break;
                case '\\': out += "\\\\"; break;
                case '\n': out += "\\n"; break;
                case '\r': out += "\\r"; break;
                case '\t': out += "\\t"; break;
                case '\b': out += "\\b"; break;
                case '\f': out += "\\f"; break;
                default:
                    if (c < 0x20) {
                        char buf[8];
                        std::snprintf(buf, sizeof buf, "\\u%04x", c);
                        out += buf;
                    } else {
                        out += static_cast<char>(c);
                    }
            }
        }
        out += '"';
    }

    std::variant<std::monostate, bool, std::int64_t, double, std::string, Array, Object> d_;
};

}  // namespace minipar_rt
