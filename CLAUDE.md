# CLAUDE.md - AI Assistant Guide for BarbAAS

## Project Overview

**BarbAAS** (Barbora As A Service) is a monitoring script designed to check the Barbora.lt website API for available delivery slots and send notifications when slots become available. This project was created during the COVID-19 pandemic when delivery slots were scarce.

### Purpose
- Monitor Barbora.lt API for available delivery time slots
- Send notifications via SMS (Twilio) and/or MS Teams webhooks
- Run continuously in Docker container
- Implement throttling to avoid notification spam

### Tech Stack
- **Language**: Python 3.7
- **Dependencies**: Twilio, requests
- **Deployment**: Docker
- **External APIs**: Barbora.lt, Twilio SMS, MS Teams Webhooks

---

## Repository Structure

```
BarbAAS/
├── barbora.py          # Main application script (single file)
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker container configuration
├── .env               # Environment variables (not in git)
├── .gitignore         # Git ignore rules
├── LICENSE            # MIT License
├── README.md          # User-facing documentation
└── CLAUDE.md          # This file - AI assistant guide
```

### Key Files

#### barbora.py (141 lines)
The entire application logic in a single Python script:
- **Lines 1-23**: Configuration and environment variable loading
- **Lines 26-41**: Client initialization (Twilio, MS Teams)
- **Lines 44-58**: Barbora API configuration and headers
- **Lines 60-73**: Notification sending functions
- **Lines 75-82**: MS Teams message formatting
- **Lines 85-106**: API request handling with error management
- **Lines 109-141**: Main polling loop with throttling logic

#### Dockerfile
- Base image: `python:3.7`
- Installs dependencies from requirements.txt
- Copies barbora.py to /app
- Entry point: Python running barbora.py with unbuffered output

#### .env
Template/example environment variables (contains placeholder values)

---

## Architecture & Key Components

### Application Flow

```
[Start] → [Initialize Clients] → [Main Loop]
                                       ↓
                    ┌──────────────────┴─────────────────┐
                    ↓                                    ↓
            [Check Throttle]                    [Get Delivery Data]
                    ↓                                    ↓
            [Sleep if needed]                   [Parse Response]
                    ↓                                    ↓
                    └──────────────→ [Slot Available?] ─┐
                                            ↓            ↓
                                          [Yes]        [No]
                                            ↓            ↓
                                    [Send Notifications] [Log]
                                            ↓            ↓
                                    [Decrement Throttle] │
                                            ↓            ↓
                                    [Sleep PUSH_BACK_SECONDS]
                                            ↓
                                    [Loop continues...]
```

### Core Components

#### 1. Environment Configuration
All configuration is done via environment variables:
- **Required**: `BARBORA_COOKIE` (authentication for Barbora API)
- **Optional SMS**: Twilio credentials (4 variables)
- **Optional Teams**: `MS_TEAMS_WEBHOOK`
- **Behavior**: `HOURS_TO_SLEEP_AFTER_GETTING_SLOT`, `NOTIFICATIONS_TO_SEND`, `PUSH_BACK_BARBORA_API_IN_SECONDS`, `DRY_RUN`

#### 2. Notification System
Two notification channels (both optional):
- **Twilio SMS**: Sends text message to configured phone number
- **MS Teams**: Posts MessageCard to webhook URL

Function: `send_notifications()` (line 60-73)
- Checks if clients are initialized
- Sends to all configured channels simultaneously

#### 3. API Polling
Function: `get_delivery_data()` (line 85-106)
- Makes GET request to Barbora API
- Handles errors: HTTP errors, connection issues, timeouts
- Special case: 401 (expired cookie) → stops the bot and notifies
- Returns response object or None on error

#### 4. Throttling Mechanism
Prevents notification spam:
- `NOTIFICATIONS_THROTTLE`: Countdown from `NOTIFICATIONS_TO_SEND`
- Each notification decrements counter
- When reaches 0: sleep for `HOURS_TO_SLEEP` hours
- After sleep: reset counter and continue

#### 5. Main Loop (line 110-141)
Infinite loop that:
1. Checks throttle state (sleep if needed)
2. Gets current time
3. Fetches delivery data (unless DRY_RUN)
4. Parses JSON response
5. Checks for slot availability via regex
6. Sends notifications if found
7. Sleeps for `PUSH_BACK_SECONDS` before next iteration

---

## Environment Variables

### Required Variables
| Variable | Purpose | Example |
|----------|---------|---------|
| `BARBORA_COOKIE` | Authentication cookie for Barbora.lt API | `session=abc123...` |

### Optional: Twilio SMS
| Variable | Purpose | Example |
|----------|---------|---------|
| `TWILIO_ACCOUNT_ID` | Twilio account SID | `ACxxxxx...` |
| `TWILIO_ACCOUNT_AUTH_TOKEN` | Twilio auth token | `token123...` |
| `TWILIO_FROM_NUMBER` | Sender phone number | `+1234567890` |
| `TWILIO_NUMBER_TO_SEND` | Recipient phone number | `+0987654321` |

**Note**: All 4 Twilio variables must be set to enable SMS notifications.

### Optional: MS Teams
| Variable | Purpose | Example |
|----------|---------|---------|
| `MS_TEAMS_WEBHOOK` | Incoming webhook URL | `https://outlook.office.com/webhook/...` |

### Behavior Configuration
| Variable | Default | Purpose |
|----------|---------|---------|
| `HOURS_TO_SLEEP_AFTER_GETTING_SLOT` | `6` | Hours to sleep after throttle limit |
| `NOTIFICATIONS_TO_SEND` | `2` | Number of notifications before sleeping |
| `PUSH_BACK_BARBORA_API_IN_SECONDS` | `30` | Delay between API polls |
| `DRY_RUN` | unset | If set, always reports "slot found" |

---

## Development Workflows

### Local Development

#### Prerequisites
- Python 3.7+
- pip for dependency installation

#### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env .env.local
# Edit .env.local with your credentials

# Run locally
python barbora.py
```

### Docker Development

#### Build Image
```bash
docker build . -t barbar
```

#### Run Container
```bash
# Using .env file
docker run --env-file .env barbar

# With specific environment variables
docker run -e BARBORA_COOKIE="cookie_value" -e DRY_RUN=True barbar
```

#### Testing with DRY_RUN
```bash
# Always trigger "slot found" logic
docker run --env-file .env -e DRY_RUN=True barbar
```

---

## Code Conventions & Style

### Naming Conventions
- **UPPER_SNAKE_CASE**: Constants and environment-derived configuration
  - Examples: `BARBORA_URL`, `TWILIO_ACCOUNT_ID`, `HOURS_TO_SLEEP`
- **lower_snake_case**: Functions and variables
  - Examples: `send_notifications()`, `get_delivery_data()`, `twilio_client`

### Error Handling
- Uses try/except blocks for network requests
- Specific handling for different request exceptions:
  - `RequestException`: General errors
  - `HTTPError`: HTTP-specific errors
  - `ConnectionError`: Network connection issues
  - `Timeout`: Request timeouts
- Special case: 401 response triggers sys.exit(0) with notification

### Code Organization
- Single-file architecture for simplicity
- Linear flow: imports → config → functions → main loop
- No classes, purely functional approach
- Global state via module-level variables

### Dependencies
Current versions (from requirements.txt):
- `twilio==6.37.0`: SMS notifications
- `requests==2.23.0`: HTTP client
- Development tools: `pylint`, `astroid`, `isort`

**Note**: Versions are from 2020 and may have security vulnerabilities. Consider updating for new development.

---

## Common Tasks for AI Assistants

### 1. Adding New Notification Channels

**Pattern to follow**: Examine existing Twilio or MS Teams implementation

Steps:
1. Add environment variable loading (top of file)
2. Initialize client if credentials provided (after line 41)
3. Create send function (near line 75)
4. Call from `send_notifications()` function (line 60-73)

Example structure:
```python
# Step 1: Load env var
NEW_SERVICE_URL = os.environ.get("NEW_SERVICE_URL")

# Step 2: Initialize (conditional)
if NEW_SERVICE_URL:
    print("New Service Notifications Enabled")
else:
    print("New Service Notifications disabled")

# Step 3: Create sender function
def send_to_new_service(message):
    # Implementation here
    pass

# Step 4: Add to send_notifications()
def send_notifications():
    # ... existing code ...
    if NEW_SERVICE_URL:
        send_to_new_service(f"Slot found at {today}")
```

### 2. Modifying API Request Logic

**Location**: `get_delivery_data()` function (line 85-106)

When modifying:
- Preserve error handling structure
- Keep 401 special case (expired cookie detection)
- Maintain return type consistency (response object or None)
- Test all error paths

### 3. Changing Polling Behavior

**Location**: Main loop (line 110-141)

Key variables to modify:
- `PUSH_BACK_SECONDS`: Time between polls
- Slot detection regex: `'"available": true'` (line 131)
- Empty response detection: `'"title": null'` (line 135)

**Warning**: Be careful with regex patterns - they must match Barbora API response format exactly.

### 4. Adjusting Throttling Logic

**Location**: Lines 111-118 (throttle check), line 134 (decrement)

Throttling state machine:
- `NOTIFICATIONS_THROTTLE`: Current remaining notifications
- `NOTIFICATIONS_TO_SEND`: Reset value
- When throttle hits 0: sleep, then reset

To modify behavior:
- Change sleep calculation (line 23)
- Adjust notification count logic (line 134)
- Modify reset condition (line 113)

### 5. Updating Dependencies

**Important**: This project uses old dependencies (2020)

Process:
1. Update `requirements.txt` with new versions
2. Test in local environment first
3. Rebuild Docker image
4. Watch for API changes in Twilio library

Known considerations:
- Twilio 6.x → 7.x had breaking changes
- requests library is stable
- urllib3 version may need updating for security

### 6. Environment Variable Changes

When adding new env vars:
1. Load at top of file (lines 9-22)
2. Provide sensible defaults with `os.environ.get()`
3. Use `os.environ[...]` only for required variables
4. Update `.env` file with example values
5. Document in this file (Environment Variables section)
6. Add validation if needed (see Twilio validation, lines 26-36)

---

## Testing & Debugging

### DRY_RUN Mode
Set `DRY_RUN=True` to test notification logic without hitting Barbora API:
- Skips actual API call (line 122-123)
- Always triggers "slot found" path (line 131)
- Tests all notification channels
- Useful for verifying Twilio/Teams integration

### Debug Output
The script prints status messages to stdout:
- Client initialization status (lines 33-34, 36, 39, 41)
- Slot detection results (lines 132, 136, 138)
- Error messages from request failures (lines 91, 100, 102, 104)
- Sleep notifications (line 114)

Docker runs with `-u` flag (unbuffered output) for real-time logs.

### Common Issues

#### 1. "No need to run, cookie expired"
- **Cause**: BARBORA_COOKIE is invalid/expired
- **Solution**: Get fresh cookie from browser DevTools (Application → Cookies)
- **Location**: Line 93

#### 2. Notifications not sending
- **Check**: Are credentials configured? (print statements at startup)
- **Twilio**: All 4 variables must be set
- **Teams**: Webhook URL must be valid
- **Debug**: Enable DRY_RUN to test notification path

#### 3. JSON parsing errors
- **Cause**: Unexpected API response format
- **Location**: Line 125-129
- **Solution**: Inspect actual response format, adjust parsing

#### 4. Too many notifications
- **Cause**: Throttling not configured properly
- **Solution**: Adjust `NOTIFICATIONS_TO_SEND` and `HOURS_TO_SLEEP_AFTER_GETTING_SLOT`

---

## Deployment

### Docker Deployment

**Build**:
```bash
docker build . -t barbar
```

**Run**:
```bash
docker run --env-file .env barbar
```

**Run in background**:
```bash
docker run -d --env-file .env --name barbora-monitor barbar
```

**View logs**:
```bash
docker logs -f barbora-monitor
```

**Stop**:
```bash
docker stop barbora-monitor
```

### Production Considerations

1. **Cookie Management**: Barbora cookie expires periodically
   - Monitor for 401 errors
   - Set up alerts when bot stops
   - Have process to refresh cookie

2. **Restart Policy**: Configure Docker restart policy
   ```bash
   docker run -d --restart=unless-stopped --env-file .env barbar
   ```

3. **Resource Usage**: Very lightweight
   - CPU: Minimal (sleeps most of time)
   - Memory: <50MB typically
   - Network: One API call every PUSH_BACK_SECONDS

4. **Monitoring**: Application sends Teams message when:
   - Cookie expires (line 95-97)
   - Going to sleep (line 116-118)

---

## Important Notes for AI Assistants

### Code Quality & Maintenance

1. **Single File Design**: All logic is in barbora.py
   - Don't split into modules unless necessary
   - Keep simplicity - this is a single-purpose script

2. **No Tests**: No test suite exists
   - Use DRY_RUN for manual testing
   - Be extra careful with changes to main loop

3. **Global State**: Uses module-level variables
   - `NOTIFICATIONS_THROTTLE` is mutable global (line 109)
   - This is acceptable for single-threaded script
   - Don't introduce thread/async without major refactor

4. **Old Dependencies**: Be cautious
   - Versions from 2019-2020
   - May have security vulnerabilities
   - If updating, test thoroughly

### Regex Patterns

The script uses regex to detect API response states:
- `'"available": true'` (line 131): Slot is available
- `'"title": null'` (line 135): Empty response

**Critical**: These patterns are fragile
- API changes can break detection
- Always test after modifying
- Consider asking user to verify current API format

### API Integration

**Barbora API**:
- Endpoint: `https://www.barbora.lt/api/eshop/v1/cart/deliveries`
- Auth: Basic auth + Cookie (line 50, 57)
- No official documentation (reverse-engineered)
- May change without notice

**Twilio API**:
- Uses official Twilio Python SDK
- Standard SMS sending

**MS Teams**:
- Uses Incoming Webhook connector
- MessageCard format (deprecated but still works)
- Consider Adaptive Cards for future updates

### Modification Guidelines

**When making changes**:
1. Read the entire barbora.py file first (only 141 lines)
2. Preserve error handling patterns
3. Test with DRY_RUN before production
4. Don't over-engineer - match existing simplicity
5. Update this CLAUDE.md if adding major features

**What NOT to do**:
- Don't add unnecessary abstractions
- Don't introduce async/await (script is I/O bound but simple)
- Don't add logging framework (print statements are fine)
- Don't add config files (env vars are sufficient)
- Don't add type hints unless doing full modernization

### Git Workflow

- **Default branch**: Appears to be `main` or `master`
- **License**: MIT (permissive, see LICENSE file)
- **Contributors**: Original author tadasm, contributor vyckou

When committing:
- Keep commit messages clear and concise
- Reference issues if applicable
- Don't commit .env file (in .gitignore)

---

## API Reference

### Functions

#### `send_notifications()`
Sends notifications to all configured channels.
- **Parameters**: None (uses global `today` variable)
- **Returns**: None
- **Side effects**: Sends SMS and/or Teams message

#### `send_message_to_teams(webhook, message)`
Sends formatted message to MS Teams.
- **Parameters**:
  - `webhook` (str): MS Teams webhook URL
  - `message` (str): Message text (supports markdown)
- **Returns**: None
- **Format**: MessageCard schema

#### `get_delivery_data()`
Fetches delivery slot data from Barbora API.
- **Parameters**: None (uses global `BARBORA_HEADERS`)
- **Returns**: Response object or None
- **Error handling**: Catches all request exceptions
- **Special behavior**: Exits on 401 (expired cookie)

---

## Version History & Context

### Original Purpose
Created during COVID-19 pandemic when grocery delivery slots were scarce. Users needed to monitor constantly to grab available slots.

### Major Changes (from git history)
- Initial implementation: Basic slot checking
- PR #2: Added MS Teams webhook support
- Recent: Cosmetic changes, .gitignore additions

### Current State (as of 2026)
- Fully functional for intended purpose
- May need dependency updates for security
- Barbora.lt API may have changed since 2020
- Consider this a maintenance-mode project

---

## Quick Reference

### File Locations
- Main code: `barbora.py`
- Config: `.env`
- Dependencies: `requirements.txt`
- Container: `Dockerfile`

### Key Line Numbers
- Config loading: 9-22
- Client init: 26-41
- API config: 44-58
- Notifications: 60-82
- API request: 85-106
- Main loop: 110-141

### Environment Variables Quick List
Required: `BARBORA_COOKIE`
Optional SMS: `TWILIO_*` (4 variables)
Optional Teams: `MS_TEAMS_WEBHOOK`
Behavior: `HOURS_TO_SLEEP_AFTER_GETTING_SLOT`, `NOTIFICATIONS_TO_SEND`, `PUSH_BACK_BARBORA_API_IN_SECONDS`, `DRY_RUN`

### Docker Commands
```bash
docker build . -t barbar
docker run --env-file .env barbar
docker run -d --restart=unless-stopped --env-file .env --name barbora-monitor barbar
docker logs -f barbora-monitor
```

---

## Questions to Ask Users

When users request changes, consider asking:

1. **New notification channels**: "What credentials/configuration does this service require?"
2. **API changes**: "Has the Barbora API response format changed? Can you provide a sample response?"
3. **Behavior changes**: "Should this apply when DRY_RUN is enabled?"
4. **Dependency updates**: "Would you like to update all dependencies or just specific ones?"
5. **Testing**: "Do you have a way to test this with the actual Barbora API?"

---

## Conclusion

BarbAAS is a straightforward, single-purpose monitoring script. Its strength is simplicity - a single Python file that does one thing well. When working with this codebase:

- **Respect the simplicity**: Don't over-engineer
- **Test carefully**: No automated tests exist
- **Watch for API changes**: Depends on undocumented Barbora API
- **Update cautiously**: Old dependencies may have breaking changes

The codebase is well-suited for quick modifications and easy deployment via Docker. Keep changes focused and test with DRY_RUN mode whenever possible.

---

*This documentation was generated for AI assistants working with the BarbAAS codebase. Last updated: 2026-01-04*
