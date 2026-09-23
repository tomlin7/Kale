# Milestone 33: Virtual Desktop Workspace Manager & Multi-Monitor Viewport

## Overview
Implement virtual desktop workspaces (Workspaces 1–4) and multi-monitor viewport management in pure Kale for the composited window system.

## Key Capabilities
1. **Virtual Workspaces**:
   - 4 independent virtual workspaces (`WORKSPACE_1` through `WORKSPACE_4`).
   - Window-to-workspace assignment (`workspace_assign_window`).
   - Active workspace switching (`workspace_set_active`).
   - Sticky / pinned windows across all workspaces (`WINDOW_FLAG_STICKY` / `0x0008`).
2. **Multi-Monitor Viewport Management**:
   - Primary display (`1024x768`) and secondary auxiliary display (`800x600`).
   - Monitor bounds clamping and window migration across displays (`workspace_move_to_monitor`).
   - Per-monitor clipping and composite bounds.
3. **Workspace Carousel & Pager Integration**:
   - Workspace thumbnail metadata for panel pagers.
   - Window visibility query based on active workspace (`workspace_is_window_visible`).
   - Workspace cycle shortcuts (Next / Previous workspace with wrap-around).
