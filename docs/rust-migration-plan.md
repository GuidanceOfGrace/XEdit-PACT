# AutoQAC Python-to-Rust Migration Plan

## Executive Summary

This plan outlines the conversion of AutoQAC from Python 3.12+ with PySide6 to Rust with Slint GUI framework. The migration preserves all functionality while leveraging Rust's safety guarantees, performance benefits, and modern async ecosystem. The UI will follow Microsoft's Fluent Design System for a modern, Windows-native look and feel.

## 1. Architecture Mapping: PySide6 → Rust/Slint

### 1.1 Core Component Mapping

| Python Component | Rust Equivalent | Key Changes |
|-----------------|-----------------|-------------|
| **StateManager** (QObject + QReadWriteLock) | `Arc<RwLock<AppState>>` + channels | Replace Qt signals with `tokio::sync` channels or Slint callbacks |
| **AppState** (dataclass) | Rust struct with derive macros | Use `#[derive(Clone, Debug)]` + builder pattern |
| **ConfigManager** (ruamel.yaml) | `rust-yaml2` + `config` crate | Structured config with `serde` derive |
| **CleaningService** (pure logic) | Pure Rust module | Direct translation, already Qt-free |
| **CleaningWorker** (QThread) | `tokio::task` or `std::thread` | Async tasks with structured concurrency |
| **GuiController** | Slint component + async runtime bridge | Mediator pattern with callback-based communication |
| **MainWindow** (PySide6 + MixIns) | Slint UI markup + Rust logic modules | Composition via Slint components + Rust traits; **Fluent Design** |
| **Qt Signals/Slots** | Channels or Slint callbacks | `tokio::sync::mpsc`, `flume`, or Slint property bindings |
| **N/A** | `EventLoopBridge` | **New:** Abstraction for tokio/Slint event loop coordination |

### 1.2 Threading Model Evolution

**Current (Python/Qt):**
```
QThread workers → QMutex/QReadWriteLock → Qt signals → GUI updates
```

**Target (Rust):**
```
tokio::spawn tasks → Arc<RwLock<T>> → channels → EventLoopBridge → Slint UI updates
                                                         ↓
                                              Slint callbacks → tokio tasks
```

**Key Decision Point:** Async vs threaded model
- **Recommended:** Hybrid approach with explicit event loop bridge
  - GUI event loop: Slint's native loop (single-threaded)
  - I/O operations: `tokio` async runtime (multi-threaded)
  - CPU-bound work: `tokio::task::spawn_blocking` or `rayon`
  - **Bridge:** `EventLoopBridge` coordinates between tokio and Slint

## 2. Technology Stack

### 2.1 Core Dependencies (Cargo.toml)

```toml
[dependencies]
# GUI Framework
slint = "1.9"

# Async Runtime (for subprocess management)
tokio = { version = "1.41", features = ["full"] }

# Configuration
serde = { version = "1.0", features = ["derive"] }
serde-saphyr = "0.0.2"  # Modern maintained YAML library (faster, safe)
config = "0.14"     # Structured configuration management

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }
tracing-appender = "0.2"  # For rotating file logs

# Error Handling
anyhow = "1.0"  # Application errors
thiserror = "2.0"  # Library errors

# Path handling
camino = "1.1"  # UTF-8 paths (Windows-safe)

# Subprocess management
tokio-process = "0.2"  # Part of tokio

# Collections
indexmap = "2.0"  # Preserve insertion order for configs

[dev-dependencies]
# Testing
tokio-test = "0.4"
tempfile = "3.14"
proptest = "1.0"  # Property-based testing
criterion = "0.5"  # Benchmarking
mockall = "0.13"  # Mocking

[build-dependencies]
slint-build = "1.9"
```

### 2.2 Justification for Key Choices

**Slint over other Rust GUI frameworks:**
- Native performance, small binary size
- Declarative UI markup (similar to QML/XAML)
- Good Windows support
- Active development and documentation
- Built-in property binding system
- Flexible styling system for implementing Fluent Design

**Fluent Design System:**
- Modern, native Windows appearance
- Familiar to Windows users (used in Windows 11, Office, etc.)
- Acrylic materials, depth, motion, and light effects
- Consistent with Microsoft's design language
- Professional appearance for tool targeting Windows games

**Tokio over async-std:**
- More mature ecosystem
- Better Windows support
- Tokio Console for debugging
- Industry standard for Rust async

**Tracing over log:**
- Structured logging
- Better async support
- Built-in spans for operation tracking
- JSON output for log parsing

**serde-saphyr over serde-yaml:**
- Actively maintained (serde-yaml is abandonware as of 2024)
- Faster than other YAML libraries
- Modern safe implementation (no unsafe-libyaml dependency)
- Better error messages and security

## 3. Phased Migration Strategy

### Phase 1: Foundation (Weeks 1-2) ✅ COMPLETED

**Goal:** Establish project structure and core data types

**Tasks:**
1. Create new Rust project structure
   ```
   autoqac-rust/
   ├── Cargo.toml
   ├── build.rs              # Slint build integration
   ├── src/
   │   ├── main.rs
   │   ├── lib.rs
   │   ├── models/           # Data structures
   │   │   ├── mod.rs
   │   │   ├── app_state.rs  # AppState struct
   │   │   └── config.rs     # Configuration structures
   │   ├── services/         # Business logic
   │   │   ├── mod.rs
   │   │   └── cleaning.rs   # CleaningService translation
   │   ├── state/            # State management
   │   │   ├── mod.rs
   │   │   └── manager.rs    # StateManager with Arc<RwLock>
   │   ├── config/           # Configuration management
   │   │   └── mod.rs
   │   └── ui/               # GUI logic
   │       ├── mod.rs
   │       └── bridge.rs     # EventLoopBridge abstraction
   ├── ui/                   # Slint UI files
   │   ├── main.slint
   │   ├── fluent/           # Fluent Design components
   │   │   ├── styles.slint  # Fluent color palette and styles
   │   │   ├── button.slint  # Fluent-style button
   │   │   ├── card.slint    # Fluent card component
   │   │   └── input.slint   # Fluent text input
   │   ├── components/
   │   └── dialogs/
   └── tests/
       ├── integration/
       └── unit/
   ```

2. Define core types (AppState, CleanResult, etc.)
   ```rust
   #[derive(Clone, Debug)]
   pub struct AppState {
       // Configuration
       pub load_order_path: Option<PathBuf>,
       pub mo2_exe_path: Option<PathBuf>,
       pub xedit_exe_path: Option<PathBuf>,

       // Runtime state
       pub is_cleaning: bool,
       pub current_plugin: Option<String>,

       // Progress
       pub progress: usize,
       pub total_plugins: usize,

       // Results
       pub cleaned_plugins: HashSet<String>,
       pub failed_plugins: HashSet<String>,

       // Settings
       pub cleaning_timeout: Duration,
       pub max_concurrent_subprocesses: usize,
   }
   ```

3. Set up configuration system with `serde-saphyr`
   ```rust
   use serde::{Deserialize, Serialize};
   use serde_saphyr as yaml;

   #[derive(Deserialize, Serialize)]
   struct MainConfig {
       #[serde(rename = "AutoQAC_Data")]
       autoqac_data: AutoQACData,
   }

   #[derive(Deserialize, Serialize)]
   struct AutoQACData {
       #[serde(rename = "Skip_Lists")]
       skip_lists: HashMap<String, Vec<String>>,

       #[serde(rename = "XEdit_Lists")]
       xedit_lists: HashMap<String, Vec<String>>,
   }

   // Loading YAML config
   fn load_config(path: &Path) -> Result<MainConfig, yaml::Error> {
       let file = std::fs::File::open(path)?;
       let config = yaml::from_reader(file)?;
       Ok(config)
   }

   // Writing YAML config
   fn save_config(path: &Path, config: &MainConfig) -> Result<(), yaml::Error> {
       let file = std::fs::File::create(path)?;
       yaml::to_writer(file, config)?;
       Ok(())
   }
   ```

4. Implement logging with `tracing`
   ```rust
   use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
   use tracing_appender::rolling;

   fn setup_logging() -> anyhow::Result<()> {
       let file_appender = rolling::daily("logs", "autoqac.log");
       let (non_blocking, _guard) = tracing_appender::non_blocking(file_appender);

       tracing_subscriber::registry()
           .with(tracing_subscriber::EnvFilter::new("info"))
           .with(tracing_subscriber::fmt::layer()
               .with_writer(non_blocking)
               .with_ansi(false))
           .init();

       Ok(())
   }
   ```

**Deliverable:** Compiling Rust project with core types and config loading

### Phase 2: Business Logic (Weeks 3-4) ✅ COMPLETED

**Goal:** Port CleaningService and subprocess handling

**Tasks:**
1. Translate CleaningService methods
   - `clean_plugin()` → async function
   - Command building logic
   - Skip list validation

2. Implement subprocess execution with real-time output
   ```rust
   use tokio::process::Command;
   use tokio::io::{AsyncBufReadExt, BufReader};

   async fn execute_cleaning_command(
       command: &str,
       plugin_name: &str,
       timeout: Duration,
       output_callback: impl Fn(String),
   ) -> Result<CleanResult, CleaningError> {
       let mut child = Command::new("cmd")
           .args(["/C", command])
           .stdout(Stdio::piped())
           .stderr(Stdio::piped())
           .spawn()?;

       let stdout = child.stdout.take().unwrap();
       let mut reader = BufReader::new(stdout).lines();

       while let Some(line) = reader.next_line().await? {
           output_callback(line);
       }

       let status = tokio::time::timeout(timeout, child.wait()).await??;
       // Process result...
   }
   ```

3. Implement output parsing (ITM/UDR detection)
   ```rust
   use regex::Regex;

   #[derive(Default)]
   struct CleaningStats {
       undeleted: usize,
       removed: usize,
       skipped: usize,
       partial_forms: usize,
   }

   fn parse_cleaning_output(line: &str, stats: &mut CleaningStats) {
       // Regex patterns matching Python version
   }
   ```

4. Create comprehensive error types
   ```rust
   #[derive(thiserror::Error, Debug)]
   pub enum CleaningError {
       #[error("Plugin {0} not found")]
       PluginNotFound(String),

       #[error("xEdit executable not configured")]
       XEditNotConfigured,

       #[error("Timeout after {0:?}")]
       Timeout(Duration),

       #[error("Subprocess error: {0}")]
       SubprocessError(#[from] std::io::Error),
   }
   ```

**Deliverable:** Working CleaningService with unit tests

### Phase 3: State Management (Weeks 5-6) ✅ COMPLETED

**Goal:** Implement thread-safe state with reactive updates

**Tasks:**
1. Create StateManager with Arc + RwLock
   ```rust
   pub struct StateManager {
       state: Arc<RwLock<AppState>>,
       // Channels for notifying GUI of changes
       state_tx: broadcast::Sender<StateChange>,
   }

   #[derive(Clone, Debug)]
   pub enum StateChange {
       ConfigurationChanged { is_fully_configured: bool },
       ProgressUpdated { current: usize, total: usize },
       CleaningStarted,
       CleaningFinished,
       PluginProcessed { plugin: String, status: String, message: String },
   }

   impl StateManager {
       pub fn new() -> Self {
           let (state_tx, _) = broadcast::channel(100);
           Self {
               state: Arc::new(RwLock::new(AppState::default())),
               state_tx,
           }
       }

       pub fn update(&self, updates: impl FnOnce(&mut AppState)) -> Vec<StateChange> {
           let mut state = self.state.write().unwrap();
           let old_state = state.clone();

           updates(&mut state);

           // Detect changes and emit events
           let changes = self.detect_changes(&old_state, &state);
           for change in &changes {
               let _ = self.state_tx.send(change.clone());
           }

           changes
       }

       pub fn subscribe(&self) -> broadcast::Receiver<StateChange> {
           self.state_tx.subscribe()
       }
   }
   ```

2. Implement state update batching
3. Add validation logic (is_fully_configured, etc.)
4. Create thread-safe result tracking

**Deliverable:** StateManager with event emission and tests

### Phase 4: Slint GUI with Fluent Design & Event Loop Bridge (Weeks 7-10) ✅ COMPLETED

**Goal:** Create modern Fluent Design UI with Slint and establish event loop coordination

**Tasks:**

1. **Create EventLoopBridge abstraction** (Critical for tokio/Slint coexistence)
   ```rust
   // src/ui/bridge.rs
   use slint::{ComponentHandle, Weak};
   use tokio::sync::mpsc;
   use std::future::Future;

   /// Coordinates between tokio async runtime and Slint event loop
   pub struct EventLoopBridge<T: ComponentHandle> {
       ui_weak: Weak<T>,
       tokio_handle: tokio::runtime::Handle,
       // Channel for sending UI update requests from tokio tasks
       ui_update_tx: mpsc::UnboundedSender<Box<dyn FnOnce(&T) + Send>>,
   }

   impl<T: ComponentHandle> EventLoopBridge<T> {
       pub fn new(ui: &T, tokio_handle: tokio::runtime::Handle) -> Self {
           let ui_weak = ui.as_weak();
           let (ui_update_tx, mut ui_update_rx) = mpsc::unbounded_channel();

           // Spawn a task to handle UI updates from the Slint event loop
           let ui_weak_clone = ui_weak.clone();
           std::thread::spawn(move || {
               while let Some(update_fn) = ui_update_rx.blocking_recv() {
                   if let Some(ui) = ui_weak_clone.upgrade() {
                       // Use invoke_from_event_loop to safely update UI from another thread
                       ui.invoke_from_event_loop(move || {
                           update_fn(&ui);
                       }).ok();
                   } else {
                       // UI has been dropped, stop the update handler
                       break;
                   }
               }
           });

           Self {
               ui_weak,
               tokio_handle,
               ui_update_tx,
           }
       }

       /// Schedule a UI update from any thread (typically from tokio tasks)
       /// This safely marshals the update to the Slint event loop
       pub fn update_ui<F>(&self, update: F)
       where
           F: FnOnce(&T) + Send + 'static,
       {
           let _ = self.ui_update_tx.send(Box::new(update));
       }

       /// Spawn an async task on the tokio runtime from a Slint callback
       /// This allows Slint UI callbacks to trigger async operations
       pub fn spawn_async<F, Fut>(&self, future_factory: F)
       where
           F: FnOnce() -> Fut + Send + 'static,
           Fut: Future<Output = ()> + Send + 'static,
       {
           self.tokio_handle.spawn(async move {
               future_factory().await;
           });
       }

       /// Clone the bridge for use in multiple callbacks
       pub fn clone_handle(&self) -> EventLoopBridgeHandle<T> {
           EventLoopBridgeHandle {
               ui_weak: self.ui_weak.clone(),
               tokio_handle: self.tokio_handle.clone(),
               ui_update_tx: self.ui_update_tx.clone(),
           }
       }
   }

   /// Lightweight handle that can be cloned and passed to callbacks
   #[derive(Clone)]
   pub struct EventLoopBridgeHandle<T: ComponentHandle> {
       ui_weak: Weak<T>,
       tokio_handle: tokio::runtime::Handle,
       ui_update_tx: mpsc::UnboundedSender<Box<dyn FnOnce(&T) + Send>>,
   }

   impl<T: ComponentHandle> EventLoopBridgeHandle<T> {
       pub fn update_ui<F>(&self, update: F)
       where
           F: FnOnce(&T) + Send + 'static,
       {
           let _ = self.ui_update_tx.send(Box::new(update));
       }

       pub fn spawn_async<F, Fut>(&self, future_factory: F)
       where
           F: FnOnce() -> Fut + Send + 'static,
           Fut: Future<Output = ()> + Send + 'static,
       {
           self.tokio_handle.spawn(async move {
               future_factory().await;
           });
       }
   }
   ```

2. **Define Fluent Design System in Slint**
   ```slint
   // ui/fluent/styles.slint
   // Microsoft Fluent Design System color palette and constants

   export global FluentPalette {
       // Dark theme colors (default)
       in-out property <color> background: #202020;
       in-out property <color> surface: #2B2B2B;
       in-out property <color> surface-secondary: #323232;
       in-out property <color> card-background: #2B2B2B;
       in-out property <color> card-stroke: #3F3F3F;

       // Accent colors
       in-out property <color> accent: #60CDFF;  // Fluent blue for dark theme
       in-out property <color> accent-hover: #3AA0F3;
       in-out property <color> accent-pressed: #1A86D9;
       in-out property <color> accent-disabled: #3F3F3F;

       // Text colors
       in-out property <color> text-primary: #FFFFFF;
       in-out property <color> text-secondary: #CCCCCC;
       in-out property <color> text-tertiary: #999999;
       in-out property <color> text-on-accent: #000000;
       in-out property <color> text-disabled: #6D6D6D;

       // Semantic colors
       in-out property <color> success: #6CCB5F;
       in-out property <color> warning: #FCE100;
       in-out property <color> error: #FF99A4;

       // Effects
       in-out property <length> corner-radius: 4px;
       in-out property <length> card-corner-radius: 8px;
       in-out property <length> elevation-shadow: 4px;
   }

   // Fluent animation timings
   export global FluentAnimation {
       in-out property <duration> fast: 150ms;
       in-out property <duration> normal: 250ms;
       in-out property <duration> slow: 400ms;
   }
   ```

   ```slint
   // ui/fluent/button.slint
   import { FluentPalette, FluentAnimation } from "styles.slint";

   export component FluentButton inherits Rectangle {
       in property <string> text;
       in property <bool> primary: false;
       in property <bool> enabled: true;

       callback clicked();

       // Button styling
       background: touch-area.has-hover ?
           (primary ? FluentPalette.accent-hover : FluentPalette.surface-secondary) :
           (primary ? FluentPalette.accent : FluentPalette.surface);

       border-radius: FluentPalette.corner-radius;
       border-width: primary ? 0px : 1px;
       border-color: FluentPalette.card-stroke;

       min-width: 120px;
       min-height: 32px;

       // Hover and press animations
       animate background { duration: FluentAnimation.fast; }

       // Shadow effect for depth (lighter for dark theme)
       drop-shadow-blur: touch-area.has-hover ? 8px : 4px;
       drop-shadow-color: #00000040;
       drop-shadow-offset-y: 2px;

       animate drop-shadow-blur { duration: FluentAnimation.fast; }

       touch-area := TouchArea {
           enabled: root.enabled;
           clicked => { root.clicked(); }
       }

       HorizontalLayout {
           padding: 8px 16px;
           alignment: center;

           Text {
               text: root.text;
               color: primary ? FluentPalette.text-on-accent : FluentPalette.text-primary;
               font-size: 14px;
               font-weight: 600;
           }
       }
   }
   ```

   ```slint
   // ui/fluent/card.slint
   import { FluentPalette } from "styles.slint";

   export component FluentCard inherits Rectangle {
       in property <string> title;

       background: FluentPalette.card-background;
       border-radius: FluentPalette.card-corner-radius;
       border-width: 1px;
       border-color: FluentPalette.card-stroke;

       // Acrylic-like effect with subtle shadow (lighter for dark theme)
       drop-shadow-blur: FluentPalette.elevation-shadow;
       drop-shadow-color: #00000030;
       drop-shadow-offset-y: 2px;

       VerticalLayout {
           padding: 16px;
           spacing: 12px;

           if title != "": Text {
               text: title;
               font-size: 16px;
               font-weight: 600;
               color: FluentPalette.text-primary;
           }

           @children
       }
   }
   ```

   ```slint
   // ui/fluent/input.slint
   import { FluentPalette, FluentAnimation } from "styles.slint";

   export component FluentLineEdit inherits Rectangle {
       in-out property <string> text;
       in property <string> placeholder;
       in property <bool> enabled: true;

       background: FluentPalette.surface;
       border-radius: FluentPalette.corner-radius;
       border-width: input-focused ? 2px : 1px;
       border-color: input-focused ? FluentPalette.accent : FluentPalette.card-stroke;

       min-height: 32px;

       animate border-color, border-width { duration: FluentAnimation.fast; }

       property <bool> input-focused: input.has-focus;

       HorizontalLayout {
           padding: 6px 12px;

           input := TextInput {
               text <=> root.text;
               enabled: root.enabled;
               color: FluentPalette.text-primary;
               font-size: 14px;
               vertical-alignment: center;

               // Placeholder text
               Text {
                   text: root.placeholder;
                   color: FluentPalette.text-tertiary;
                   visible: input.text == "";
               }
           }
       }
   }
   ```

3. **Design main window with Fluent Design**
   ```slint
   // ui/main.slint
   import { FluentPalette } from "fluent/styles.slint";
   import { FluentButton } from "fluent/button.slint";
   import { FluentCard } from "fluent/card.slint";
   import { FluentLineEdit } from "fluent/input.slint";
   import { ProgressIndicator, ListView } from "std-widgets.slint";

   export component MainWindow inherits Window {
       title: "AutoQAC - Automatic Quick Auto Clean";
       background: FluentPalette.background;
       preferred-width: 900px;
       preferred-height: 700px;

       // Properties bound to Rust state
       in-out property <string> load-order-path;
       in-out property <string> xedit-exe-path;
       in-out property <string> mo2-exe-path;
       in-out property <bool> is-cleaning;
       in-out property <int> progress-current;
       in-out property <int> progress-total;
       in-out property <bool> mo2-mode;
       in-out property <bool> partial-forms-enabled;

       // Callbacks to Rust
       callback start-cleaning();
       callback stop-cleaning();
       callback browse-load-order();
       callback browse-xedit();
       callback browse-mo2();

       VerticalLayout {
           padding: 24px;
           spacing: 16px;

           // Header
           Text {
               text: "AutoQAC";
               font-size: 28px;
               font-weight: 700;
               color: FluentPalette.text-primary;
           }

           Text {
               text: "Automatic Quick Auto Clean for Bethesda Game Plugins";
               font-size: 14px;
               color: FluentPalette.text-secondary;
           }

           // Configuration Card
           FluentCard {
               title: "Configuration";

               VerticalLayout {
                   spacing: 12px;

                   // Load Order Path
                   HorizontalLayout {
                       spacing: 8px;

                       Text {
                           text: "Load Order:";
                           vertical-alignment: center;
                           min-width: 120px;
                           color: FluentPalette.text-primary;
                       }

                       FluentLineEdit {
                           text <=> load-order-path;
                           placeholder: "Path to plugins.txt";
                           horizontal-stretch: 1;
                       }

                       FluentButton {
                           text: "Browse";
                           clicked => { browse-load-order(); }
                       }
                   }

                   // xEdit Path
                   HorizontalLayout {
                       spacing: 8px;

                       Text {
                           text: "xEdit:";
                           vertical-alignment: center;
                           min-width: 120px;
                           color: FluentPalette.text-primary;
                       }

                       FluentLineEdit {
                           text <=> xedit-exe-path;
                           placeholder: "Path to SSEEdit.exe / FO4Edit.exe";
                           horizontal-stretch: 1;
                       }

                       FluentButton {
                           text: "Browse";
                           clicked => { browse-xedit(); }
                       }
                   }

                   // MO2 Path (conditional)
                   if mo2-mode: HorizontalLayout {
                       spacing: 8px;

                       Text {
                           text: "Mod Organizer 2:";
                           vertical-alignment: center;
                           min-width: 120px;
                           color: FluentPalette.text-primary;
                       }

                       FluentLineEdit {
                           text <=> mo2-exe-path;
                           placeholder: "Path to ModOrganizer.exe";
                           horizontal-stretch: 1;
                       }

                       FluentButton {
                           text: "Browse";
                           clicked => { browse-mo2(); }
                       }
                   }
               }
           }

           // Options Card
           FluentCard {
               title: "Options";

               HorizontalLayout {
                   spacing: 24px;

                   // Checkboxes styled with Fluent
                   Rectangle {
                       // MO2 Mode checkbox
                   }

                   Rectangle {
                       // Partial Forms checkbox
                   }
               }
           }

           // Progress Card (shown when cleaning)
           if is-cleaning: FluentCard {
               title: "Cleaning Progress";

               VerticalLayout {
                   spacing: 12px;

                   HorizontalLayout {
                       Text {
                           text: "Progress: " + progress-current + " / " + progress-total;
                           color: FluentPalette.text-primary;
                       }
                   }

                   ProgressIndicator {
                       progress: progress-total > 0 ? progress-current / progress-total : 0;

                       // Custom Fluent-styled progress bar
                       height: 4px;
                   }
               }
           }

           // Control Buttons
           HorizontalLayout {
               spacing: 12px;
               alignment: end;

               FluentButton {
                   text: "Stop";
                   enabled: is-cleaning;
                   clicked => { stop-cleaning(); }
               }

               FluentButton {
                   text: is-cleaning ? "Cleaning..." : "Start Cleaning";
                   primary: true;
                   enabled: !is-cleaning && load-order-path != "" && xedit-exe-path != "";
                   clicked => {
                       if (!is-cleaning) {
                           start-cleaning();
                       }
                   }
               }
           }
       }
   }
   ```

4. **Bridge Slint properties to Rust state using EventLoopBridge**
   ```rust
   slint::include_modules!();

   pub struct GuiController {
       ui: MainWindow,
       bridge: EventLoopBridge<MainWindow>,
       state_manager: Arc<StateManager>,
   }

   impl GuiController {
       pub fn new(
           state_manager: Arc<StateManager>,
           tokio_handle: tokio::runtime::Handle,
       ) -> Self {
           let ui = MainWindow::new().unwrap();
           let bridge = EventLoopBridge::new(&ui, tokio_handle);

           // Set up Slint → tokio callbacks
           {
               let state = state_manager.clone();
               let bridge_handle = bridge.clone_handle();

               ui.on_start_cleaning(move || {
                   let state = state.clone();
                   let bridge = bridge_handle.clone();

                   // Spawn async cleaning task on tokio runtime
                   bridge.spawn_async(move || async move {
                       // Start cleaning...
                       state.update(|s| s.is_cleaning = true);

                       // Update UI when done
                       bridge.update_ui(|ui| {
                           ui.set_is_cleaning(false);
                       });
                   });
               });
           }

           // Subscribe to state changes and update UI via bridge
           {
               let bridge_handle = bridge.clone_handle();
               let mut rx = state_manager.subscribe();

               std::thread::spawn(move || {
                   while let Ok(change) = rx.blocking_recv() {
                       match change {
                           StateChange::ProgressUpdated { current, total } => {
                               bridge_handle.update_ui(move |ui| {
                                   ui.set_progress_current(current as i32);
                                   ui.set_progress_total(total as i32);
                               });
                           }
                           StateChange::CleaningStarted => {
                               bridge_handle.update_ui(|ui| {
                                   ui.set_is_cleaning(true);
                               });
                           }
                           StateChange::CleaningFinished => {
                               bridge_handle.update_ui(|ui| {
                                   ui.set_is_cleaning(false);
                               });
                           }
                           // Handle other changes...
                           _ => {}
                       }
                   }
               });
           }

           Self { ui, bridge, state_manager }
       }

       pub fn run(self) -> Result<(), slint::PlatformError> {
           self.ui.run()
       }
   }
   ```

5. **Test EventLoopBridge with mock operations**
   ```rust
   #[cfg(test)]
   mod tests {
       use super::*;

       #[test]
       fn test_bridge_update_ui() {
           let rt = tokio::runtime::Runtime::new().unwrap();
           let ui = MainWindow::new().unwrap();
           let bridge = EventLoopBridge::new(&ui, rt.handle().clone());

           // Test that UI updates are properly marshaled
           bridge.update_ui(|ui| {
               ui.set_progress_current(50);
           });

           // Verify update was applied
           std::thread::sleep(Duration::from_millis(100));
           assert_eq!(ui.get_progress_current(), 50);
       }

       #[tokio::test]
       async fn test_bridge_spawn_async() {
           let ui = MainWindow::new().unwrap();
           let bridge = EventLoopBridge::new(&ui, tokio::runtime::Handle::current());

           let (tx, rx) = tokio::sync::oneshot::channel();

           bridge.spawn_async(move || async move {
               tx.send(42).unwrap();
           });

           let result = rx.await.unwrap();
           assert_eq!(result, 42);
       }

       #[test]
       fn test_fluent_theme_colors() {
           // Test that Fluent color palette is correctly applied
           let ui = MainWindow::new().unwrap();
           // Validate Fluent Design colors are accessible
       }
   }
   ```

6. **Implement Fluent-styled dialogs** (progress, warnings, confirmations)
   ```slint
   // ui/fluent/dialog.slint
   import { FluentPalette } from "styles.slint";
   import { FluentButton } from "button.slint";
   import { FluentCard } from "card.slint";

   export component FluentDialog inherits Dialog {
       in property <string> dialog-title;
       in property <string> message;
       in property <bool> show-cancel: true;

       callback confirmed();
       callback cancelled();

       preferred-width: 400px;

       FluentCard {
           title: dialog-title;

           VerticalLayout {
               spacing: 16px;

               Text {
                   text: message;
                   color: FluentPalette.text-primary;
                   wrap: word-wrap;
               }

               HorizontalLayout {
                   spacing: 8px;
                   alignment: end;

                   if show-cancel: FluentButton {
                       text: "Cancel";
                       clicked => { cancelled(); }
                   }

                   FluentButton {
                       text: "OK";
                       primary: true;
                       clicked => { confirmed(); }
                   }
               }
           }
       }
   }
   ```

7. **Add native file browser integration**
   - Use `rfd` crate for native file dialogs on Windows
   ```rust
   // Add to Cargo.toml:
   // rfd = "0.14"

   use rfd::FileDialog;

   fn show_file_picker() -> Option<PathBuf> {
       FileDialog::new()
           .add_filter("Executable", &["exe"])
           .set_title("Select xEdit Executable")
           .pick_file()
   }
   ```

**Deliverable:** Functional Fluent Design GUI with EventLoopBridge abstraction and state binding

### Phase 5: Integration & Async Orchestration (Weeks 11-12) ✅ COMPLETED

**Goal:** Connect all components with proper async coordination

**Tasks:**
1. Create main application coordinator
   ```rust
   pub struct Application {
       state_manager: Arc<StateManager>,
       config_manager: ConfigManager,
       cleaning_service: CleaningService,
       gui_controller: GuiController,
       runtime: tokio::runtime::Runtime,
   }

   impl Application {
       pub fn new() -> anyhow::Result<Self> {
           // Create tokio runtime first
           let runtime = tokio::runtime::Builder::new_multi_thread()
               .enable_all()
               .build()?;

           let state_manager = Arc::new(StateManager::new());
           let config_manager = ConfigManager::new("AutoQAC Data")?;
           let cleaning_service = CleaningService::new(
               Arc::clone(&state_manager),
               config_manager.clone(),
           );

           // Pass runtime handle to GUI controller for EventLoopBridge
           let gui_controller = GuiController::new(
               Arc::clone(&state_manager),
               runtime.handle().clone(),
           );

           Ok(Self {
               state_manager,
               config_manager,
               cleaning_service,
               gui_controller,
               runtime,
           })
       }

       pub fn run(self) -> anyhow::Result<()> {
           // Keep runtime alive while GUI runs
           let _rt_guard = self.runtime.enter();
           self.gui_controller.run()?;
           Ok(())
       }
   }
   ```

2. Implement graceful shutdown
   ```rust
   use tokio::sync::Notify;

   pub struct ShutdownCoordinator {
       notify: Arc<Notify>,
       tasks: Vec<tokio::task::JoinHandle<()>>,
   }

   impl ShutdownCoordinator {
       pub async fn shutdown(self) {
           self.notify.notify_waiters();
           for task in self.tasks {
               let _ = task.await;
           }
       }
   }
   ```

3. Add concurrent subprocess limiting (semaphore)
   ```rust
   use tokio::sync::Semaphore;

   pub struct CleaningService {
       // ...
       subprocess_semaphore: Arc<Semaphore>,
   }

   async fn clean_plugin_with_limit(&self, plugin: String) {
       let permit = self.subprocess_semaphore.acquire().await.unwrap();
       // Clean plugin...
       drop(permit);  // Release semaphore
   }
   ```

4. Error handling and recovery

**Deliverable:** Fully integrated application with Fluent Design UI

### Phase 6: Testing & Polish (Weeks 13-14)

**Goal:** Achieve feature parity with comprehensive testing

**Tasks:**
1. Unit tests for all modules (target: 90% coverage)
   ```rust
   #[cfg(test)]
   mod tests {
       use super::*;

       #[tokio::test]
       async fn test_clean_plugin_success() {
           // Mock setup...
       }

       #[test]
       fn test_state_update() {
           let state = StateManager::new();
           state.update(|s| s.is_cleaning = true);
           assert!(state.read().is_cleaning);
       }

       #[test]
       fn test_event_loop_bridge_threading() {
           // Verify bridge correctly marshals updates between threads
       }

       #[test]
       fn test_fluent_design_components() {
           // Test Fluent components render correctly
       }
   }
   ```

2. Integration tests
   ```rust
   #[tokio::test]
   async fn test_full_cleaning_workflow() {
       // Test end-to-end cleaning process
   }
   ```

3. Property-based tests for parsing
   ```rust
   use proptest::prelude::*;

   proptest! {
       #[test]
       fn test_parse_cleaning_output_never_panics(s in "\\PC*") {
           let mut stats = CleaningStats::default();
           parse_cleaning_output(&s, &mut stats);
       }
   }
   ```

4. Performance benchmarks
   ```rust
   use criterion::{black_box, criterion_group, criterion_main, Criterion};

   fn bench_state_updates(c: &mut Criterion) {
       c.bench_function("state update", |b| {
           let state = StateManager::new();
           b.iter(|| state.update(|s| s.progress += 1));
       });
   }

   fn bench_event_loop_bridge(c: &mut Criterion) {
       c.bench_function("bridge update", |b| {
           let rt = tokio::runtime::Runtime::new().unwrap();
           let ui = MainWindow::new().unwrap();
           let bridge = EventLoopBridge::new(&ui, rt.handle().clone());

           b.iter(|| {
               bridge.update_ui(|ui| {
                   ui.set_progress_current(42);
               });
           });
       });
   }
   ```

5. Windows installer setup (using `cargo-wix` or NSIS)
6. Documentation (rustdoc + user guide with screenshots of Fluent UI)

**Deliverable:** Production-ready application with modern Fluent Design UI

## 4. Risk Areas & Mitigation

### 4.1 High-Risk Areas

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Event loop coordination** | High - Core architecture | Medium | Dedicated EventLoopBridge abstraction; thorough testing |
| **Fluent Design implementation** | Medium - UI polish | Medium | Modular Slint components; iterative refinement |
| **Slint maturity gaps** | High - May lack needed features | Medium | Early prototyping; fallback to `egui` or `iced` |
| **Windows subprocess behavior** | High - Core functionality | Low | Extensive testing on Windows; use `tokio::process` |
| **Async/GUI integration** | Medium - Complexity | Low | EventLoopBridge abstracts complexity |
| **Binary size increase** | Low - Distribution | Low | Use `strip` and LTO; acceptable tradeoff |
| **Performance regression** | Medium - User experience | Low | Benchmark during development |

### 4.2 Technical Challenges

**Challenge 1: Event loop coordination (tokio + Slint)**
- **Issue:** Two separate event loops must coexist without blocking
- **Solution:** `EventLoopBridge` abstraction with:
  - `invoke_from_event_loop` for tokio → Slint updates
  - Channels for Slint → tokio communication
  - Weak references to prevent memory leaks

**Challenge 2: Implementing Fluent Design in Slint**
- **Issue:** Slint doesn't have built-in Fluent components
- **Solution:** Custom Fluent components in Slint markup:
  - Define Fluent color palette and styles
  - Create reusable components (buttons, cards, inputs)
  - Implement Fluent animations and effects
  - Use drop shadows for depth perception

**Challenge 3: Real-time subprocess output**
- **Python:** Uses `run_process_with_realtime_output` with callbacks
- **Rust Solution:** `tokio::process` with async line reading + EventLoopBridge for GUI updates

**Challenge 4: State synchronization**
- **Python:** Qt signals auto-connect across threads
- **Rust Solution:** Explicit channels + EventLoopBridge marshaling

**Challenge 5: Configuration hot-reloading**
- **Python:** File watching implicit in some cases
- **Rust Solution:** `notify` crate for file system events (if needed)

### 4.3 Fallback Options

If Slint proves insufficient:
1. **Plan B:** `egui` (immediate mode, simpler, but harder to implement Fluent Design)
2. **Plan C:** `iced` (Elm architecture, reactive, has some theming support)
3. **Plan D:** Tauri + web frontend (easiest for Fluent with web components)

## 5. Testing Strategy

### 5.1 Test Pyramid

```
             /\
            /  \  E2E Tests (5%)
           /    \  - Full workflow tests
          /------\ - UI/UX validation
         /        \ Integration Tests (15%)
        /          \ - Component interaction
       /------------\ - Event loop bridge
      /              \ Unit Tests (80%)
     /________________\ - Pure functions, state logic
```

### 5.2 Critical Test Scenarios

1. **Event Loop Bridge**
   - UI updates from tokio tasks are properly marshaled
   - Async tasks spawned from Slint callbacks execute correctly
   - No memory leaks from weak references
   - Thread safety under concurrent updates

2. **Fluent Design Components**
   - Components render correctly with Fluent styling
   - Animations are smooth and performant
   - Color palette applied consistently
   - Responsive to user interactions

3. **State Management**
   - Concurrent updates don't lose data
   - Event emission is ordered correctly
   - Read-write lock doesn't deadlock

4. **Subprocess Handling**
   - Timeout enforcement
   - Process cleanup on abort
   - Output parsing accuracy

5. **Configuration**
   - Invalid YAML handling
   - Missing files graceful degradation
   - Path validation

6. **GUI**
   - State changes reflect in UI
   - Callbacks trigger correct actions
   - Progress updates are smooth
   - Fluent Design principles maintained

### 5.3 Performance Targets

- Startup time: < 1 second
- State updates: < 1ms
- UI update latency (via bridge): < 10ms
- UI rendering: 60 FPS for animations
- Memory usage: < 100MB idle
- Subprocess overhead: < 50ms per plugin

## 6. Migration Validation Checklist

### Feature Parity
- [ ] All configuration options preserved
- [ ] All games supported (FO3, FNV, FO4, SSE)
- [ ] MO2 integration working
- [ ] Partial forms support
- [ ] Skip list functionality
- [ ] Real-time progress updates
- [ ] Timeout handling
- [ ] Logging to rotating files

### Non-Functional Requirements
- [ ] Cross-platform (Windows primary)
- [ ] Single executable distribution
- [ ] Config migration tool from Python version
- [ ] Performance ≥ Python version
- [ ] Memory usage ≤ Python version
- [ ] Error messages are actionable
- [ ] Modern Fluent Design UI
- [ ] Native Windows look and feel

### Testing
- [ ] Unit test coverage ≥ 90%
- [ ] Integration test coverage ≥ 80%
- [ ] All critical paths tested
- [ ] EventLoopBridge thoroughly tested
- [ ] Fluent Design components tested
- [ ] Windows 10/11 tested
- [ ] Regression tests for known bugs

## 7. Open Questions & Decisions Needed

1. **Single-threaded vs multi-threaded GUI updates?**
   - **Decision:** Single-threaded (Slint's requirement)
   - Use EventLoopBridge to marshal updates to GUI thread

2. **Embed UI in binary or separate .slint files?**
   - Recommendation: Embed for single-exe distribution

3. **Logging format: JSON or plaintext?**
   - Recommendation: JSON for parsing, plaintext for debugging

4. **Config migration strategy?**
   - Provide `autoqac-migrate` tool to convert Python YAML to Rust format

5. **Versioning strategy?**
   - Start at 3.0.0 to indicate major rewrite

6. **EventLoopBridge error handling?**
   - Should failed UI updates be logged, ignored, or propagated?
   - Recommendation: Log at debug level, don't crash application

7. **Fluent Design light mode support?**
   - Should we implement light theme after launch?
   - Recommendation: Dark theme first (v3.0), light theme in v3.1

8. **Acrylic effects in Fluent Design?**
   - True acrylic requires platform APIs
   - Recommendation: Use simulated acrylic with translucency and blur

## 8. Success Metrics

- [ ] 100% feature parity with Python version
- [ ] ≤ 20MB binary size (release build, stripped)
- [ ] ≤ 2 second startup time cold, ≤ 0.5s warm
- [ ] Zero crashes in 1000 plugin cleanings
- [ ] EventLoopBridge adds < 10ms latency to UI updates
- [ ] UI maintains 60 FPS during animations
- [ ] Fluent Design components match Windows 11 aesthetic
- [ ] User-facing documentation complete
- [ ] CI/CD pipeline with automated releases

## 9. Fluent Design Principles Applied

### Light
- Directional shadows on cards and elevated elements
- Hover effects with subtle lighting changes
- Drop shadows for depth perception

### Depth
- Layered UI with z-axis positioning
- Card-based layout with elevation
- Shadows and blur for spatial relationships

### Motion
- 150ms fast animations for immediate feedback
- 250ms normal animations for state transitions
- 400ms slow animations for complex changes
- Smooth easing functions (ease-in-out)

### Material
- Simulated acrylic backgrounds
- Subtle translucency effects
- Consistent corner radii (4px buttons, 8px cards)
- 1px borders for definition

### Scale
- Responsive to window resizing
- Consistent spacing (8px, 12px, 16px, 24px)
- Typography hierarchy (28px titles, 16px headings, 14px body)

## Conclusion

This migration leverages Rust's strengths (safety, performance, zero-cost abstractions) while Slint provides a modern, lightweight GUI framework. The **EventLoopBridge abstraction** is critical for coordinating tokio's async runtime with Slint's event loop, ensuring smooth operation without blocking either loop.

The **Fluent Design System** implementation provides a modern, professional appearance that aligns with Windows 11 and Microsoft's design language, making the application feel native and polished for Windows users.

The phased approach minimizes risk by validating each layer before building on top. The hybrid async model balances simplicity with performance, using tokio for I/O and Slint's event loop for GUI updates, with EventLoopBridge handling the coordination.

**Estimated Timeline:** 14 weeks (3.5 months)
**Team Size:** 1-2 developers
**Complexity:** Medium-High (significant but well-scoped)

The key to success is thorough testing at each phase, particularly the EventLoopBridge abstraction and Fluent Design components, and maintaining the clean architecture from the Python version. The investment will pay off in maintainability, performance, distribution simplicity, and a modern user experience.
