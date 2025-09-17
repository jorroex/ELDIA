# Telegram Deezer Music Bot

## Overview

This is a Telegram bot that integrates with the Deezer music platform to allow users to search and download music tracks, albums, and artist top songs. The bot leverages the Deezer public API for searching music content and uses the deemix library for downloading music files. Users can interact with the bot through Telegram commands and inline keyboard buttons to browse and download music content directly to a local directory.

**Current Status**: Bot is operational and running successfully. All core features are working: search functionality, user interface, and music downloads.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (September 17, 2025)

- ✅ Successfully migrated code from user's notebook to main.py
- ✅ Fixed critical import errors with python-telegram-bot library (upgraded to v22.3)
- ✅ Resolved permission issues by changing config directory from /root to ~/.config
- ✅ Secured credentials by moving API keys to environment variables (TELEGRAM_BOT_TOKEN, DEEZER_ARL)
- ✅ Updated bot framework to use ApplicationBuilder instead of deprecated Application.builder()
- ✅ Bot workflow configured and running successfully

### Known Issues to Address (Future Improvements)
- Blocking HTTP calls in async handlers (should use async HTTP client)
- Download process uses os.system which could be more secure with subprocess
- Missing error handling for network failures
- Dependencies need to be properly declared in pyproject.toml for reproducibility

## System Architecture

### Bot Framework
- **Telegram Bot API Integration**: Uses python-telegram-bot library (version 20.6) for handling Telegram interactions
- **Asynchronous Processing**: Implements nest_asyncio for handling concurrent operations within the bot
- **Command and Callback Handlers**: Supports both text commands and inline keyboard interactions for user input

### Music Service Integration
- **Deezer API**: Utilizes Deezer's public REST API for searching tracks, artists, and albums
- **Search Functionality**: Implements three main search types:
  - Track search with 10-result limit
  - Artist search leading to top tracks
  - Album search leading to track listings

### Download System
- **Deemix Integration**: Uses deemix library for actual music file downloads from Deezer
- **ARL Authentication**: Requires Deezer ARL (Authentication Request Library) token for premium content access
- **Local Storage**: Downloads are stored in a dedicated `deezer_downloads` directory

### Configuration Management
- **Environment Variables**: Secure handling of sensitive tokens (Telegram Bot Token and Deezer ARL)
- **Config Directory**: Automatically creates and manages deemix configuration directory
- **Error Handling**: Validates required environment variables on startup

### User Interface
- **Inline Keyboards**: Provides interactive button-based navigation for search results
- **Message Formatting**: Supports rich text formatting through Telegram's ParseMode
- **Result Pagination**: Limits search results to manageable quantities (10 tracks, 1 artist/album)

## External Dependencies

### APIs and Services
- **Telegram Bot API**: Core messaging and interaction platform
- **Deezer Public API**: Music search and metadata retrieval
  - Track search endpoint: `https://api.deezer.com/search/track`
  - Artist search endpoint: `https://api.deezer.com/search/artist`
  - Album search endpoint: `https://api.deezer.com/search/album`
  - Artist top tracks: `https://api.deezer.com/artist/{id}/top`
  - Album tracks: `https://api.deezer.com/album/{id}/tracks`

### Python Libraries
- **python-telegram-bot (v20.6)**: Telegram bot framework
- **nest_asyncio**: Nested event loop support
- **requests**: HTTP client for API calls
- **deemix**: Deezer music download library

### Authentication Requirements
- **Telegram Bot Token**: Required for bot API access
- **Deezer ARL Token**: Required for premium music download access

### File System
- **Local Downloads Directory**: `deezer_downloads/` for storing music files
- **Configuration Directory**: `~/.config/deemix/` for storing ARL authentication