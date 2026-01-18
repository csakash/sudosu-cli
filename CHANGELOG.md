# Changelog

All notable changes to Sudosu will be documented in this file.

## [0.1.4] - 2026-01-19

### Changed
- Version bump for new release
- Improved stability and performance

## [0.1.2] - 2026-01-18

### Changed
- **Zero-config experience**: Sudosu now works immediately after installation with no setup required
- **Production backend by default**: Uses hosted backend (`sudosu-cli.trysudosu.com`) out of the box
- **Silent auto-initialization**: Config is created automatically without prompts when first run
- **Updated default URLs**: Production URL now correctly points to `wss://sudosu-cli.trysudosu.com/ws`

### Removed
- Removed mandatory `sudosu init` step - no longer needed for first-time users
- Removed backend URL prompt during initialization

### Fixed
- Fixed issue where new users were prompted for backend URL configuration
- Fixed incorrect default production backend URL

## [0.1.1] - 2026-01-15

### Added
- Initial public release
- AI coworker functionality with file operations
- Tool integrations (Gmail, Slack, Linear, GitHub, Notion)
- Interactive CLI session
- Agent creation and management
- Real-time streaming responses

## [0.1.0] - 2026-01-10

### Added
- Initial development release
