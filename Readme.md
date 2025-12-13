# AutoQAC

**Auto Quick Auto Clean - Batch Plugin Cleaning Tool for Bethesda Games**

Automated batch cleaning of Bethesda game plugins using xEdit's Quick Auto Clean (-QAC) functionality.

## Overview

AutoQAC automates the process of cleaning game plugins (ESP/ESM/ESL files) to remove:
- **ITMs (Identical To Master)**: Records that are identical to the master file
- **UDRs (Undisabled References)**: References that should be disabled but aren't
- **Deleted Navmeshes**: Navigation meshes that can cause crashes

This project provides **two implementations**:

### 1. Python/Qt Implementation (Legacy)

The original implementation using Python 3.12+ with PySide6 (Qt for Python).

- **Location**: Root directory (`AutoQAC_Interface.py`, `AutoQACLib/`)
- **Status**: Stable, feature-complete
- **UI Framework**: PySide6 (Qt 6)
- **Documentation**: See [CLAUDE.md](CLAUDE.md)

**Quick Start**:
```bash
# Install dependencies
uv sync --extra dev

# Run application
uv run python AutoQAC_Interface.py
```

### 2. Rust/Slint Implementation (Modern)

A modern rewrite in Rust with Slint UI framework and Microsoft Fluent Design.

- **Location**: `autoqac-rust/` directory
- **Status**: Feature parity with Qt version (16/20 milestones complete)
- **UI Framework**: Slint 1.13 with Fluent Design
- **Documentation**: See [autoqac-rust/README.md](autoqac-rust/README.md)

**Quick Start**:
```bash
cd autoqac-rust

# Build and run
cargo run --release
```

**Benefits of Rust Implementation**:
- ✅ Type safety (compile-time error checking)
- ✅ Modern async runtime (tokio)
- ✅ Better performance (native code)
- ✅ Fluent Design UI (modern, consistent)
- ✅ Memory safety guarantees
- ✅ Cross-platform support

---

## Is it Safe to Clean Plugins?

**Short answer**: Yes.
**Long answer**: Yeeeeeeeeeeeeeeeee...

### Identical To Master Records (ITMs)

Sometimes, a mod author will open a plugin record simply to investigate a field or property and not change anything. But the Creation Kit will still flag that record as edited, even if it remains identical in every way. These are **Identical To Master Records (ITMs)**.

- They frequently overwrite valid changes made by other mods
- Should be cleaned whenever possible
- Intentional ITMs are extremely rare

### Undisabled References (UDRs)

**Undisabled References (UDRs)** are potentially more harmful. Mod authors will sometimes delete records they no longer wish to use. Depending on what record has been deleted, other mods may try to reference it. When they can't find this record, this can lead to broken quests or game crashes.

- Records need to be restored and properly disabled
- Can cause crashes and broken quests if not cleaned
- AutoQAC automatically handles UDR restoration

### DLC Cleaning

While cleaning official DLC plugins is recommended for **Skyrim**, it is **NOT recommended** for **Fallout 4**. However, AutoQAC will skip official DLC plugins by default for safety.

All other mod plugins, including **Creation Club Content**, can and should be cleaned.

---

## Features

### Core Functionality
- ✅ Batch cleaning of multiple plugins
- ✅ Skip list integration (base game files protected)
- ✅ Auto-detection of game type
- ✅ MO2 (Mod Organizer 2) integration
- ✅ Configurable timeout per plugin
- ✅ Real-time progress tracking
- ✅ Comprehensive logging

### Advanced Features
- ✅ Record-level statistics (UDRs, ITMs, navmeshes, partial forms)
- ✅ Partial Forms experimental support
- ✅ Game detection from xEdit executable or load order
- ✅ Configuration validation with feedback
- ✅ Cancellation support
- ✅ Detailed error reporting

---

## Supported Games

| Game                   | Short Code | xEdit Executables          |
| ---------------------- | ---------- | -------------------------- |
| Fallout 3              | FO3        | FO3Edit.exe, FO3Edit64.exe |
| Fallout New Vegas      | FNV        | FNVEdit.exe, FNVEdit64.exe |
| Fallout 4              | FO4        | FO4Edit.exe, FO4Edit64.exe |
| Skyrim Special Edition | SSE        | SSEEdit.exe, SSEEdit64.exe |
| Fallout 4 VR           | FO4VR      | FO4VREdit.exe              |
| Skyrim VR              | SkyrimVR   | TES5VREdit.exe             |

**Universal xEdit**: Also supports universal xEdit executables (`xEdit.exe`, `xEdit64.exe`) with automatic game detection.

---

## How to Use (Quick Guide)

### Python/Qt Version

1. **Install dependencies**:
   ```bash
   uv sync --extra dev
   ```

2. **Run the application**:
   ```bash
   uv run python AutoQAC_Interface.py
   ```

3. **Configure paths**:
   - Set **Load Order** path (`plugins.txt` or `loadorder.txt`)
   - Set **xEdit** executable path (FO4Edit.exe, SSEEdit.exe, etc.)
   - (Optional) Set **MO2** path for Mod Organizer 2 integration

4. **Start cleaning**:
   - Click **Start Cleaning**
   - Monitor progress
   - Review results when complete

### Rust/Slint Version

1. **Build and run**:
   ```bash
   cd autoqac-rust
   cargo run --release
   ```

2. **Configure and clean**: Same as Python version (modern Fluent UI)

---

## Finding Configuration Files

### Load Order Files

**Vortex**:
- Select **Open** → **Game Application Data Folder** in Vortex
- Files: `plugins.txt` and `loadorder.txt`

**Mod Organizer 2**:
- Navigate to: `MO2/profiles/<profile name>/`
- Files: `plugins.txt` and `loadorder.txt`

### xEdit Executable

Download from Nexus Mods:
- [SSEEdit](https://www.nexusmods.com/skyrimspecialedition/mods/164?tab=files) (Skyrim Special Edition)
- [FO4Edit](https://www.nexusmods.com/fallout4/mods/2737/?tab=files) (Fallout 4)

**Important**: Run xEdit at least once before using AutoQAC to ensure proper configuration.

### Mod Organizer 2 Users

**⚠ IMPORTANT**: Make sure MO2 is **completely closed** before starting cleaning.

Set the **ModOrganizer.exe** path in AutoQAC. Vortex and other mod manager users can leave this blank.

---

## Configuration Files

### Python/Qt Version

Located in `AutoQAC Data/`:
- `AutoQAC Main.yaml`: Game configurations, skip lists
- `AutoQAC Config.yaml`: User settings, paths
- `AutoQAC Ignore.yaml`: Additional ignore list

### Rust/Slint Version

Same structure in `AutoQAC Data/` (shared configuration).

---

## Logging & Journal

Both implementations create log files:

**Python Version**:
- `logs/autoqac_<timestamp>.log`: Application log (rotating)

**Rust Version**:
- `logs/autoqac_<timestamp>.log`: Structured logging with tracing

**Journal** (both):
- Records all cleaned plugins and statistics
- Configurable retention (default: 7 days)

---

## Known Issues

### Critical Constraint

**⚠ AutoQAC SHOULD ONLY CLEAN ONE (1) PLUGIN AT A TIME**

If multiple xEdit windows start opening simultaneously, immediately close AutoQAC and report the issue.

### Timeout Handling

- Default timeout: **5 minutes** (300s) per plugin
- AutoQAC will automatically close xEdit and skip the plugin if timeout is reached
- You can manually close xEdit to skip the wait

### Common Errors

**"Exactly one module must be selected for Quick Clean mode"**:
1. Plugin name is invalid → Press OK, AutoQAC will continue
2. MO2 path not set correctly → Set ModOrganizer.exe path

**"This application failed to start because no Qt Platform..."**:
1. MO2 is already open → Close all MO2 instances
2. MO2 missing files → Reinstall MO2 2.4+ or use portable version

---

## Pro Tip: Virtual Desktops

To avoid xEdit pop-ups interrupting your work:

1. Press **WIN + CTRL + →** to switch to another virtual desktop
2. Run AutoQAC on that desktop
3. Press **WIN + CTRL + ←** to switch back to your main desktop

**Guides**:
- [Windows 11](https://www.howtogeek.com/796349/how-to-use-virtual-desktops-on-windows-11/)
- [Windows 10](https://www.howtogeek.com/197625/how-to-use-virtual-desktops-in-windows-10/)

---

## Documentation

- **Python/Qt Architecture**: See [CLAUDE.md](CLAUDE.md)
- **Rust/Slint Architecture**: See [autoqac-rust/README.md](autoqac-rust/README.md)
- **Development Guide**: See implementation-specific docs

---

## Links

- **Mod Organizer 2**: [GitHub Releases](https://github.com/ModOrganizer2/modorganizer/releases)
- **SSEEdit**: [Nexus Mods](https://www.nexusmods.com/skyrimspecialedition/mods/164?tab=files)
- **FO4Edit**: [Nexus Mods](https://www.nexusmods.com/fallout4/mods/2737/?tab=files)
- **FO4 AutoQAC**: [Nexus Mods](https://www.nexusmods.com/fallout4/mods/69413)
- **SSE AutoQAC**: [Nexus Mods](https://www.nexusmods.com/skyrimspecialedition/mods/86683)

---

## License

GPL-3.0 License - See [LICENSE.md](LICENSE.md) for details.

## Credits

- **Original Author**: Poet (aka GuidanceOfGrace)
- **xEdit Team**: For the powerful xEdit tools
- **Contributors**: See commit history for full list

---

**Choose your implementation**:
- **Stable & Familiar**: Use the Python/Qt version
- **Modern & Fast**: Use the Rust/Slint version

Both implementations are production-ready and feature-complete for core functionality.
