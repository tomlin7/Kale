# Milestone 17: Universal Serial Bus (USB) Subsystem & UHCI/EHCI Host Controller

## Overview
Implement the Universal Serial Bus (USB) subsystem for Kale OS. This milestone establishes USB standard descriptor serialization and parsing, UHCI (Universal Host Controller Interface) register management, Transfer Descriptors (TDs) and Queue Heads (QHs), USB standard control requests, and Human Interface Device (HID) report parsing for USB keyboards and mice.

## Architecture

```
                       +-----------------------------+
                       |        USB Subsystem        |
                       |    (os/drivers/usb.kl)      |
                       +--------------+--------------+
                                      |
            +-------------------------+-------------------------+
            |                         |                         |
            v                         v                         v
   [Descriptor Engine]        [UHCI Controller]          [HID Class Driver]
   Device / Config / Interface Frame List & TDs          Mouse & Keyboard Reports
   Endpoint Descriptors       SETUP / IN / OUT Tokens    Scancode & Delta Stream
```

## Phases

### Phase 1: USB Standard Descriptors
- **Device Descriptor** (18 bytes):
  - `bLength` (18), `bDescriptorType` (1: Device).
  - `bcdUSB` (e.g. `0x0110` for USB 1.1, `0x0200` for USB 2.0).
  - `bDeviceClass`, `bDeviceSubClass`, `bDeviceProtocol`.
  - `bMaxPacketSize0` (8, 16, 32, or 64).
  - `idVendor`, `idProduct`, `bcdDevice`.
  - `iManufacturer`, `iProduct`, `iSerialNumber`, `bNumConfigurations`.
- **Configuration Descriptor** (9 bytes):
  - `bLength` (9), `bDescriptorType` (2: Configuration), `wTotalLength`.
  - `bNumInterfaces`, `bConfigurationValue`, `bmAttributes`, `bMaxPower`.
- **Interface Descriptor** (9 bytes):
  - `bLength` (9), `bDescriptorType` (4: Interface), `bInterfaceNumber`.
  - `bNumEndpoints`, `bInterfaceClass` (3: HID), `bInterfaceSubClass`, `bInterfaceProtocol` (1: Keyboard, 2: Mouse).
- **Endpoint Descriptor** (7 bytes):
  - `bLength` (7), `bDescriptorType` (5: Endpoint), `bEndpointAddress` (bit 7: 1=IN, 0=OUT).
  - `bmAttributes` (0: Control, 1: Isochronous, 2: Bulk, 3: Interrupt), `wMaxPacketSize`, `bInterval`.

### Phase 2: UHCI Host Controller Register Interface
- Standard I/O registers:
  - `USBCMD` (`0x00`): Run/Stop (bit 0), Host Controller Reset (bit 1), Global Reset (bit 2).
  - `USBSTS` (`0x02`): USB Interrupt (bit 0), Error Interrupt (bit 1), Host Controller Halted (bit 5).
  - `USBINTR` (`0x04`): Interrupt Enable flags.
  - `FRNUM` (`0x06`): Frame Number.
  - `FRBASEADD` (`0x08`): Frame List Base Address (4KB aligned).
  - `SOFMOD` (`0x0C`): Start of Frame Modify.
  - `PORTSC1` (`0x10`) & `PORTSC2` (`0x12`): Port Status and Control (Current Connect Status bit 0, Port Enable bit 2, Line Status bits 3..2: Low-speed vs Full-speed, Port Reset bit 9).

### Phase 3: Transfer Descriptors (TDs) & Control Transfers
- UHCI Transfer Descriptor (32-byte aligned, 16 bytes quad-word):
  - Dword 0: Link Pointer (bit 0: Terminate, bit 1: QH/TD select, bit 2: Depth/Breadth first).
  - Dword 1: Status & Control (Active bit 23, Stalled bit 22, Data Buffer Error bit 21, Babble bit 20, NAK bit 19, CRC/Timeout bit 18, Actual Length bits 10..0).
  - Dword 2: Token (Packet ID PID: `SETUP = 0x2D`, `IN = 0x69`, `OUT = 0xE1`, Device Address bits 14..8, Endpoint bits 18..15, Data Toggle bit 19, Max Length bits 31..21).
  - Dword 3: Buffer Pointer (Physical memory pointer).
- Standard Device Requests:
  - `GET_STATUS (0x00)`
  - `SET_ADDRESS (0x05)`
  - `GET_DESCRIPTOR (0x06)`
  - `SET_CONFIGURATION (0x09)`

### Phase 4: USB HID Report Parser
- HID Mouse Report: Buttons (Left, Right, Middle), Delta X, Delta Y.
- HID Keyboard Report: Modifier keys (Ctrl, Shift, Alt, GUI), 6-key array scancodes.
