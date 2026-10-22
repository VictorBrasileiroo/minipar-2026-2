// RUN-02 — testes de unidade do codec JSON e dos frames (sem processos externos).
#include <chrono>
#include <limits>
#include <string>
#include <thread>

#include "minipar_rt/minipar_rt.hpp"
#include "test_util.hpp"

using namespace minipar_rt;

namespace {

bool rejects(const std::string& text) {
    try {
        (void)Json::parse(text);
    } catch (const JsonError&) {
        return true;
    }
    return false;
}

// Par de sockets conectados pelo loopback (listener efêmero em 127.0.0.1:0).
struct Pair {
    net::Socket a, b;
};
Pair make_pair_sockets() {
    std::string err;
    net::Socket l = net::listen_tcp("127.0.0.1", 0, err);
    if (!l.valid()) throw rt_test::Failure{"listen: " + err};
    std::uint16_t port = net::local_port(l.get());
    Pair p;
    std::thread t([&] {
        std::string peer;
        p.b = net::accept_tcp(l.get(), peer);
    });
    p.a = net::connect_tcp("127.0.0.1", port, 2000, err);
    t.join();
    if (!p.a.valid() || !p.b.valid()) throw rt_test::Failure{"connect: " + err};
    return p;
}

}  // namespace

TEST_CASE("JSON: ida e volta de Value preserva tipos") {
    Value v(Value::List{Value(), Value(true), Value(-42), Value(2.0), Value(0.1), Value("a\"b\\c\n\t\x01 ç"),
                        Value(Value::List{Value(1), Value(Value::List{})})});
    std::string txt = Json::from_value(v).dump();
    Value back = Json::parse(txt).to_value();
    CHECK_MSG(back == v, txt);
    CHECK(Json::from_value(Value(2.0)).dump() == "2.0");  // float continua float
    CHECK(Json::from_value(Value(2)).dump() == "2");
    CHECK(Json::parse("1e3").to_value().is_float());
    CHECK(Json::parse("-0").to_value().is_int());
}

TEST_CASE("JSON: escapes \\u e pares surrogate viram UTF-8") {
    CHECK(Json::parse("\"\\u00e7\"").str() == "\xC3\xA7");
    CHECK(Json::parse("\"\\ud83d\\ude00\"").str() == "\xF0\x9F\x98\x80");
    CHECK(rejects("\"\\ud83d\""));
    CHECK(rejects("\"\\ude00\""));
}

TEST_CASE("JSON: entradas malformadas sao rejeitadas") {
    for (const char* bad : {"", " ", "{", "[1,]", "{\"a\":1,}", "01", "1.", ".5", "+1", "NaN", "Infinity", "tru",
                            "\"abc", "\"a\x01\"", "{\"a\":1,\"a\":2}", "[1] x", "{a:1}", "'a'", "\"\\x\"",
                            "99999999999999999999", "1e999"}) {
        CHECK_MSG(rejects(bad), std::string("aceitou: ") + bad);
    }
    std::string deep(65, '[');
    deep += std::string(65, ']');
    CHECK(rejects(deep));
    std::string ok(64, '[');
    ok += std::string(64, ']');
    CHECK(!rejects(ok));
}

TEST_CASE("JSON: valor nao finito nao cruza a rede") {
    for (double x : {std::numeric_limits<double>::infinity(), std::numeric_limits<double>::quiet_NaN()}) {
        bool threw = false;
        try {
            (void)Json::from_value(Value(x));
        } catch (const JsonError&) {
            threw = true;
        }
        CHECK(threw);
    }
}

TEST_CASE("frame: ida e volta, inclusive maior que 1 MiB") {
    Pair p = make_pair_sockets();
    std::string big(3 * 1024 * 1024 + 7, 'x');
    big[0] = '{';
    std::thread w([&] {
        net::write_frame(p.a.get(), "a");
        net::write_frame(p.a.get(), big);
    });
    std::string got, err;
    CHECK(net::read_frame(p.b.get(), got, err) == net::FrameStatus::Ok && got == "a");
    CHECK(net::read_frame(p.b.get(), got, err) == net::FrameStatus::Ok && got == big);
    w.join();
}

TEST_CASE("frame: recebido byte a byte (fragmentacao)") {
    Pair p = make_pair_sockets();
    std::string payload = "{\"type\":\"TESTE\",\"x\":[1,2,3]}";
    std::string wire = {char(0), char(0), char(0), char(payload.size())};
    wire += payload;
    std::thread w([&] {
        for (char c : wire) {
            net::send_all(p.a.get(), &c, 1);
            std::this_thread::sleep_for(std::chrono::milliseconds(2));
        }
    });
    std::string got, err;
    CHECK(net::read_frame(p.b.get(), got, err) == net::FrameStatus::Ok);
    CHECK(got == payload);
    w.join();
}

TEST_CASE("frame: tamanho 0 e acima de 8 MiB sao invalidos; fim no meio e Closed") {
    {
        Pair p = make_pair_sockets();
        const char zero[4] = {0, 0, 0, 0};
        net::send_all(p.a.get(), zero, 4);
        std::string got, err;
        CHECK(net::read_frame(p.b.get(), got, err) == net::FrameStatus::Invalid);
    }
    {
        Pair p = make_pair_sockets();
        const unsigned char huge[4] = {0x00, 0x80, 0x00, 0x01};  // 8 MiB + 1
        net::send_all(p.a.get(), reinterpret_cast<const char*>(huge), 4);
        std::string got, err;
        CHECK(net::read_frame(p.b.get(), got, err) == net::FrameStatus::Invalid);
    }
    {
        Pair p = make_pair_sockets();
        const char partial[6] = {0, 0, 0, 10, 'a', 'b'};
        net::send_all(p.a.get(), partial, 6);
        p.a.close();
        std::string got, err;
        CHECK(net::read_frame(p.b.get(), got, err) == net::FrameStatus::Closed);
    }
    CHECK(!net::write_frame(net::kInvalidSocket, ""));  // payload vazio não é enviado
}

int main(int argc, char** argv) { return rt_test::run_all(argc, argv); }
