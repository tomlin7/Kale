import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSUSBSubsystem(unittest.TestCase):
    def run_kale_jit(self, code: str):
        st = SourceText(code)
        diag = DiagnosticBag()
        loader = ModuleLoader([os.path.abspath(".")], diag)
        parser = Parser(st, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parser errors: {[d.message for d in diag]}")

        binder = Binder(diag, module_loader=loader)
        bound = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Binder errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        llvm_mod = emitter.emit_module(bound)
        jit = LLVMJIT()
        return jit.run_ir(str(llvm_mod))

    def test_usb_device_descriptor_parsing(self):
        code = """
        import "os/drivers/usb.kl" as usb;

        uint8[18] raw;
        raw[0] = 18 as uint8;  // bLength
        raw[1] = 1 as uint8;   // bDescriptorType (Device)
        raw[2] = 0x10 as uint8; // bcdUSB 1.10 (low)
        raw[3] = 0x01 as uint8; // bcdUSB (high)
        raw[4] = 0 as uint8;   // bDeviceClass
        raw[5] = 0 as uint8;   // bDeviceSubClass
        raw[6] = 0 as uint8;   // bDeviceProtocol
        raw[7] = 64 as uint8;  // bMaxPacketSize0
        raw[8] = 0x34 as uint8; // idVendor (low)
        raw[9] = 0x12 as uint8; // idVendor (high: 0x1234)
        raw[10] = 0x78 as uint8; // idProduct (low)
        raw[11] = 0x56 as uint8; // idProduct (high: 0x5678)
        raw[12] = 0x01 as uint8; // bcdDevice (low)
        raw[13] = 0x00 as uint8; // bcdDevice (high)
        raw[14] = 1 as uint8;   // iManufacturer
        raw[15] = 2 as uint8;   // iProduct
        raw[16] = 0 as uint8;   // iSerialNumber
        raw[17] = 1 as uint8;   // bNumConfigurations

        usb.USBDeviceDescriptor desc;
        bool ok = usb.usb_parse_device_descriptor(&desc, &raw[0]);

        if (!ok || !desc.is_valid) return 1;
        if (desc.bLength != (18 as uint8) || desc.bDescriptorType != (1 as uint8)) return 2;
        if (desc.bcdUSB != (0x0110 as uint16)) return 3;
        if (desc.bMaxPacketSize0 != (64 as uint8)) return 4;
        if (desc.idVendor != (0x1234 as uint16) || desc.idProduct != (0x5678 as uint16)) return 5;
        if (desc.bNumConfigurations != (1 as uint8)) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_usb_config_and_interface_descriptors(self):
        code = """
        import "os/drivers/usb.kl" as usb;

        // Config Descriptor: 9 bytes, total length 34 bytes, 1 interface
        uint8[9] c_raw;
        c_raw[0] = 9 as uint8;
        c_raw[1] = 2 as uint8; // Config
        c_raw[2] = 34 as uint8; // wTotalLength low
        c_raw[3] = 0 as uint8;  // wTotalLength high
        c_raw[4] = 1 as uint8;  // bNumInterfaces
        c_raw[5] = 1 as uint8;  // bConfigurationValue
        c_raw[6] = 0 as uint8;  // iConfiguration
        c_raw[7] = 0xA0 as uint8; // bmAttributes (Bus powered, Remote wakeup)
        c_raw[8] = 50 as uint8; // bMaxPower (100 mA)

        usb.USBConfigDescriptor c_desc;
        bool ok = usb.usb_parse_config_descriptor(&c_desc, &c_raw[0]);
        if (!ok || !c_desc.is_valid || c_desc.wTotalLength != (34 as uint16)) {
            return 1;
        }

        // Interface Descriptor: 9 bytes, HID class (3), Mouse (protocol 2)
        uint8[9] if_raw;
        if_raw[0] = 9 as uint8;
        if_raw[1] = 4 as uint8; // Interface
        if_raw[2] = 0 as uint8; // bInterfaceNumber
        if_raw[3] = 0 as uint8; // bAlternateSetting
        if_raw[4] = 1 as uint8; // bNumEndpoints
        if_raw[5] = 3 as uint8; // bInterfaceClass (HID)
        if_raw[6] = 1 as uint8; // bInterfaceSubClass (Boot)
        if_raw[7] = 2 as uint8; // bInterfaceProtocol (Mouse)
        if_raw[8] = 0 as uint8; // iInterface

        usb.USBInterfaceDescriptor if_desc;
        ok = usb.usb_parse_interface_descriptor(&if_desc, &if_raw[0]);
        if (!ok || !if_desc.is_valid) return 2;
        if (if_desc.bInterfaceClass != (3 as uint8) || if_desc.bInterfaceProtocol != (2 as uint8)) {
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_uhci_td_token_generation(self):
        code = """
        import "os/drivers/usb.kl" as usb;

        // Token: PID=SETUP (0x2D), DevAddr=5, Endpoint=0, DataToggle=false, MaxLen=8
        // Bits 7..0: 0x2D
        // Bits 14..8: 5 << 8 = 0x0500
        // Bits 18..15: 0
        // Bit 19: 0
        // Bits 31..21: (8 - 1) = 7 -> 7 << 21 = 0x00E00000
        // Expected: 0x00E00000 | 0x0500 | 0x2D = 0x00E0052D
        uint32 token = usb.usb_make_td_token(usb.USB_PID_SETUP, 5 as uint8, 0 as uint8, false, 8 as uint16);
        if (token != (0x00E0052D as uint32)) {
            return 1;
        }

        // Test with DataToggle = true and MaxLen = 64 (64 - 1 = 63 = 0x3F)
        // 0x3F << 21 = 0x07E00000 | (1 << 19: 0x00080000) = 0x07E80000
        uint32 token2 = usb.usb_make_td_token(usb.USB_PID_IN, 2 as uint8, 1 as uint8, true, 64 as uint16);
        if ((token2 & (1 << 19)) == (0 as uint32)) {
            return 2; // Data toggle bit missing
        }
        if ((token2 & (0xFF as uint32)) != (usb.USB_PID_IN as uint32)) {
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_usb_hid_mouse_report_decoding(self):
        code = """
        import "os/drivers/usb.kl" as usb;

        // Mouse packet 1: Left button down (0x01), dx = +15, dy = -5 (256 - 5 = 251)
        uint8[3] pkt1;
        pkt1[0] = 0x01 as uint8;
        pkt1[1] = 15 as uint8;
        pkt1[2] = 251 as uint8;

        usb.HIDMouseReport r1;
        bool ok = usb.usb_hid_parse_mouse_report(&r1, &pkt1[0], 3);
        if (!ok || !r1.left_btn || r1.right_btn || r1.middle_btn) return 1;
        if (r1.delta_x != 15 || r1.delta_y != -5) return 2;

        // Mouse packet 2: Right button down (0x02), dx = -20 (236), dy = +30 (30)
        uint8[3] pkt2;
        pkt2[0] = 0x02 as uint8;
        pkt2[1] = 236 as uint8;
        pkt2[2] = 30 as uint8;

        usb.HIDMouseReport r2;
        ok = usb.usb_hid_parse_mouse_report(&r2, &pkt2[0], 3);
        if (!ok || r2.left_btn || !r2.right_btn) return 3;
        if (r2.delta_x != -20 || r2.delta_y != 30) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_usb_hid_keyboard_report_decoding(self):
        code = """
        import "os/drivers/usb.kl" as usb;

        // Keyboard packet: Left Shift (0x02), keycode 'a' (0x04)
        uint8[8] k_pkt;
        k_pkt[0] = 0x02 as uint8; // Left Shift
        k_pkt[1] = 0x00 as uint8; // Reserved
        k_pkt[2] = 0x04 as uint8; // Key 1: 'a'
        k_pkt[3] = 0x05 as uint8; // Key 2: 'b'
        k_pkt[4] = 0x00 as uint8;
        k_pkt[5] = 0x00 as uint8;
        k_pkt[6] = 0x00 as uint8;
        k_pkt[7] = 0x00 as uint8;

        usb.HIDKeyboardReport k_rep;
        bool ok = usb.usb_hid_parse_keyboard_report(&k_rep, &k_pkt[0], 8);
        if (!ok || k_rep.modifiers != (0x02 as uint8)) return 1;
        if (k_rep.keycodes[0] != (0x04 as uint8) || k_rep.keycodes[1] != (0x05 as uint8)) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
