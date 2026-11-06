#!/bin/bash
set -e
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/local.nearone.refresh.plist" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/local.nearone.refresh.plist"
echo 'ปิดการอัปเดตรายชั่วโมงบน Mac แล้ว'
