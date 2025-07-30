json# WebAgent JSON Data Cleaning Rules

## Field Removal Configuration

This document defines the standard field removal rules for WebAgent JSON data processing.

### Core Removal Fields

#### UI/Display Related
- `drop` - UI drop state
- `mask` - UI masking information  
- `favicon` - Website favicon data
- `screenshot` - Raw screenshot paths
- `marked_screenshot` - Annotated screenshot paths

#### Browser/DOM Related
- `path` - DOM element path
- `tabId` - Browser tab identifier
- `hostTitle` - Page title information
- `movementX`, `movementY` - Mouse movement data
- `attributes` - DOM element attributes

#### UI Control Related
- `buttonText` - UI button text
- `buttonColor`, `buttonWidth`, `buttonRadius` - Button styling
- `buttonPosition` - Button positioning
- `cancelable` - Event cancelable state

#### Automation/Processing Related
- `model` - Processing model information
- `orderList` - UI element ordering
- `imgMarkValue` - Image marking coordinates
- `isShowGuideModelMedia` - Guide display flags
- `matchRuleSetting` - Rule matching configuration
- `actionRuleSetting` - Action rule configuration

#### Metadata/Debug Related
- `annotations` - Manual annotations
- `recrop_rect` - Image cropping data

### Preserved Core Fields

#### Essential Data
- `id` - Unique step identifier
- `recordingId` - Recording session identifier
- `type` - Action type (click, type, etc.)
- `title` - Human-readable action description
- `value` - Input/action value
- `timestamp` - Action timing
- `href` - Target URL
- `host` - Target hostname

#### Positioning Data
- `rect` - Element bounding rectangle
- `pageX`, `pageY` - Page coordinates
- `clientX`, `clientY` - Client coordinates
- `viewport` - Viewport dimensions

#### Technical Data
- `selector` - CSS selector
- `automationExecType` - Execution type
- `createdTime` - Creation timestamp

## Usage

Use this configuration with the `clean_json_fields.py` script to maintain consistent data cleaning across all WebAgent JSON files.

## Version History

- v1.0: Initial field removal rules
- v1.1: Added matchRuleSetting and actionRuleSetting removal