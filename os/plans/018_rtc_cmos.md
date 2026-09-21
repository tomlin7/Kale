# Milestone 18: Real-Time Clock (RTC) & CMOS Subsystem

## Overview
Implement the Real-Time Clock (RTC) and CMOS subsystem for Kale OS. This milestone establishes hardware access to the Motorola MC146818 RTC controller via ports `0x70` and `0x71`, implements non-maskable interrupt (NMI) preservation, decodes Binary-Coded Decimal (BCD) values into binary date/time components, handles 24-hour vs 12-hour AM/PM formats, computes Unix epoch timestamps, and configures periodic interrupts for high-precision timekeeping.

## Architecture

```
                       +-----------------------------+
                       |        RTC Subsystem        |
                       |    (os/drivers/rtc.kl)      |
                       +--------------+--------------+
                                      |
            +-------------------------+-------------------------+
            |                         |                         |
            v                         v                         v
    [CMOS Register I/O]      [BCD/Time Converter]       [Unix Epoch Engine]
     Ports 0x70 / 0x71        Seconds, Minutes, Hours    Days from 1970
     NMI Disable Bit          Day, Month, Year, Century  POSIX Timestamp (sec)
```

## Phases

### Phase 1: CMOS Register Addressing & Status Registers
- Port `0x70`: CMOS Index Register (write register offset 0..127, bit 7 controls NMI disable).
- Port `0x71`: CMOS Data Register (read/write data byte).
- Register map:
  - `0x00`: Seconds (0..59)
  - `0x02`: Minutes (0..59)
  - `0x04`: Hours (0..23 in 24h mode, or 1..12 with bit 7 = PM in 12h mode)
  - `0x06`: Day of Week (1..7)
  - `0x07`: Day of Month (1..31)
  - `0x08`: Month (1..12)
  - `0x09`: Year (0..99)
  - `0x32`: Century (e.g. 20 for 2026)
  - `0x0A`: Status Register A (bit 7: Update In Progress UIP, bits 3..0: Rate selection)
  - `0x0B`: Status Register B (bit 2: BCD vs Binary mode, bit 1: 24h vs 12h mode, bit 6: Periodic Interrupt Enable PIE)

### Phase 2: BCD to Binary Conversion & Time Normalization
- Check bit 7 of Status Register A (UIP): wait until clear to avoid reading partial updates.
- Check bit 2 of Status Register B:
  - If bit 2 is `0`: values are stored in BCD format (`binary = (bcd & 0x0F) + ((bcd / 16) * 10)`).
  - If bit 2 is `1`: values are already in standard binary format.
- Check bit 1 of Status Register B (24-hour mode):
  - If 12-hour mode and bit 7 is set: add 12 to hours (PM conversion).
- Full Year calculation: `year = (century * 100) + year_offset`.

### Phase 3: Unix Epoch Timestamp Calculation
- Number of days from January 1, 1970 to given date.
- Leap year calculation: year is leap year if `(year % 4 == 0 && (year % 100 != 0 || year % 400 == 0))`.
- Sum seconds: `epoch_seconds = (days_since_1970 * 86400) + (hours * 3600) + (minutes * 60) + seconds`.

### Phase 4: Periodic Interrupt Rate Configuration
- Set lower 4 bits of Status Register A:
  - Rate `3`: 8192 Hz
  - Rate `6`: 1024 Hz (standard kernel tick)
  - Rate `10`: 64 Hz
  - Rate `15`: 2 Hz
