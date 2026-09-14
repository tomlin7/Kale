# apps/lsp Architecture Plan

## 1. Overview
The intelligence engine for Kale tooling, implementing Microsoft's Language Server Protocol.

## 2. Modules
- `rpc.kl`: JSON-RPC 2.0 framing and message dispatch over stdio.
- `document.kl`: Synchronized document store tracking open buffer piece tables.
- `analysis.kl`: Incremental symbol analysis, scope lookup, and type inference.
- `main.kl`: Server startup, handshake, and request routing.
