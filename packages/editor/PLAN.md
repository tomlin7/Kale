# Legacy Editor Core (`packages/editor`) Maintenance Plan

## 1. Overview
The `packages/editor/` package contains the prototype GDI-based text editor components (`editor.kl`, `syntax.kl`, `theme.kl`).

---

## 2. Deprecation & Migration Strategy
1. **Status**: ⚠️ Maintenance / Deprecated in favor of `apps/editor`.
2. **Role**: Serves as a reference implementation for lexical tokenization (`LineHighlighter`) and color theming (`Theme`).
3. **Migration**:
   - The tokenizer algorithms and color definitions will be ported directly to `libs/render` and `apps/editor`.
   - Once `apps/editor` v2 (GPU-rendered) is validated, `packages/editor` will be safely archived.
