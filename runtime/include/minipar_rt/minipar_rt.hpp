// minipar_rt — runtime de Fork/Join do MiniPar 2026.2 (Eixo C). Contrato: docs/02_CONTRATOS_TECNICOS.md §2 (C-FJ-v1).
// Header-only. Compilar com: -std=c++20 -pthread -I <repo>/runtime/include  (+ -lws2_32 no Windows)
#pragma once

#include "value.hpp"
#include "core.hpp"
#include "json.hpp"
#include "net.hpp"
#include "remote.hpp"
#include "api.hpp"
#include "worker.hpp"
