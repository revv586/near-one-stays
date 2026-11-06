#!/bin/bash
set -e
cd "$(dirname "$0")"
if ! command -v node >/dev/null 2>&1; then
  echo 'ต้องมี Node.js 20 ขึ้นไปก่อน เปิด https://nodejs.org เพื่อติดตั้ง แล้วคลิกไฟล์นี้อีกครั้ง'
  read -r -p 'กด Enter เพื่อปิด'; exit 1
fi
node scripts/validate.mjs
(open 'http://localhost:4173' 2>/dev/null || true) &
node scripts/serve.mjs
