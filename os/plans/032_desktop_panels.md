# Milestone 32: Desktop Panels, Applets & Notification Center

## Overview
Implement the Desktop Panels, System Tray Applets, and Notification Center subsystem for Kale OS. Delivers desktop taskbar navigation, application launcher toggle, system tray clock/status applets, and an interactive desktop notification toast queue with auto-dismiss timers.

## Technical Architecture
1. **Desktop Panel Bar (`DesktopPanel`)**:
   - Anchored to bottom or top of the screen (`x = 0, y, w = screen_w, h = panel_height`).
   - Launcher Button: Hit rect for opening system application menu.
   - Taskbar Item List (`TaskItem[8]`): Tracks open window IDs, titles, and active focus state.
   - System Tray:
     - Real-Time Clock applet: Unpacks hours and minutes into ASCII format (`"HH:MM"`).
     - Network & audio indicators.
2. **Notification Center (`NotificationCenter`)**:
   - Fixed capacity toast queue (`NotificationToast[4]`).
   - Positioning: Automatically stacked in the screen corner with spacing.
   - Auto-dismiss lifecycle:
     - Configurable duration in milliseconds (e.g. 5000 ms).
     - `notification_tick(elapsed_ms)` decrements active timers.
     - Expired toasts are automatically cleared and remaining notifications compacted.
   - Manual dismissal on click or dismiss button.

## Deliverables
- `os/plans/032_desktop_panels.md`: Architecture plan.
- `os/kernel/desktop_panel.kl`: Pure Kale desktop panel bar, clock applet, and notification center engine.
- `tests/test_os_desktop_panel.py`: Test suite validating panel layout, taskbar item tracking, clock formatting, notification queueing, countdown expiration, and manual dismissal.
