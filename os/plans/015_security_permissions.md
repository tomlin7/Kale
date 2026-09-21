# Milestone 15: Security, User Accounts & POSIX Permissions

## Overview
Implement the security, user authentication, and access control subsystem for Kale OS. This milestone introduces process credentials (`uid`, `gid`, `euid`, `egid`), standard Unix-style file permission mode bits (`rwxrwxrwx`, `suid`, `sgid`), access control verification for VFS filesystem nodes, and Linux-style capability flags (`CAP_SYS_ADMIN`, `CAP_NET_RAW`, `CAP_KILL`, `CAP_SETUID`).

## Architecture

```
                       +-----------------------------+
                       |      Security Manager       |
                       |   (os/kernel/security.kl)   |
                       +--------------+--------------+
                                      |
            +-------------------------+-------------------------+
            |                         |                         |
            v                         v                         v
   [Process Credentials]     [POSIX Access Checks]     [Kernel Capabilities]
    UID / GID / EUID / EGID   Owner / Group / Other     CAP_SYS_ADMIN / KILL
    Root UID 0 Superuser      rwx bitmask matching      DAC Override / Raw Net
```

## Phases

### Phase 1: User & Group Credentials
- `Credentials`:
  - `uid`: Real User ID.
  - `gid`: Real Group ID.
  - `euid`: Effective User ID (determines access permissions).
  - `egid`: Effective Group ID.
  - `suid`: Saved User ID (for privilege dropping and restoration).
  - `sgid`: Saved Group ID.
- Standard User IDs:
  - `UID_ROOT = 0` (Superuser).
  - `UID_DAEMON = 1` (System service daemon).
  - `UID_DEFAULT_USER = 1000` (First standard interactive user).

### Phase 2: POSIX File Mode Bits
- Standard permission masks:
  - User: `S_IRUSR (0400)`, `S_IWUSR (0200)`, `S_IXUSR (0100)`.
  - Group: `S_IRGRP (0040)`, `S_IWGRP (0020)`, `S_IXGRP (0010)`.
  - Other: `S_IROTH (0004)`, `S_IWOTH (0002)`, `S_IXOTH (0001)`.
  - Special: `S_ISUID (04000)`, `S_ISGID (02000)`.
- Access request flags:
  - `ACCESS_R_OK = 4` (Read).
  - `ACCESS_W_OK = 2` (Write).
  - `ACCESS_X_OK = 1` (Execute).

### Phase 3: Access Control Verification
- `security_check_access(creds, node_uid, node_gid, node_mode, request_flags)`:
  - **Superuser (Root)**:
    - If `creds->euid == 0`: Always grant read and write. For execute (`X_OK`), grant if ANY execute bit (`0111`) is set on the node.
  - **Owner**:
    - If `creds->euid == node_uid`: Shift user permission bits right by 6, check if requested bits match.
  - **Group**:
    - If `creds->egid == node_gid`: Shift group permission bits right by 3, check if requested bits match.
  - **Other**:
    - Check lowest 3 bits against requested bits.

### Phase 4: Kernel Capabilities
- Fine-grained permission model:
  - `CAP_CHOWN (1 << 0)`: Change arbitrary file ownership.
  - `CAP_DAC_OVERRIDE (1 << 1)`: Bypass file read, write, and execute permission checks.
  - `CAP_KILL (1 << 2)`: Send signals to arbitrary processes.
  - `CAP_SETUID (1 << 3)`: Arbitrary manipulation of process UIDs.
  - `CAP_NET_RAW (1 << 4)`: Open raw network sockets.
  - `CAP_SYS_ADMIN (1 << 5)`: Mount/unmount filesystems, configure hardware devices.
