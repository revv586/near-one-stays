#!/bin/bash
set -e
src="$(cd "$(dirname "$0")" && pwd)"
dest="$HOME/Desktop/near-one-stays"
if [ "$src" != "$dest" ]; then
  if [ -e "$dest" ]; then dest="$HOME/Desktop/near-one-stays-$(date +%Y%m%d-%H%M%S)"; fi
  mkdir -p "$dest"
  ditto "$src" "$dest"
fi
chmod +x "$dest/Start.command" "$dest/Enable-hourly-updates.command" "$dest/Disable-hourly-updates.command"
open "$dest"
echo "ติดตั้งแล้วที่ $dest"
echo 'ดับเบิลคลิก Start.command เพื่อเปิดเว็บ'
