#!/bin/sh

if [ -z "$GOOGLE_FONTS_API_KEY" ]; then
	printf "GOOGLE_FONTS_API_KEY is missing\n" >&2
	exit 1
fi

output="$(dirname "$(dirname "$0")")/data/webfonts.json"
url="https://www.googleapis.com/webfonts/v1/webfonts?key=$GOOGLE_FONTS_API_KEY"

if command -v curl > /dev/null; then
	curl -o "$output" "$url"
elif command -v wget > /dev/null; then
	wget -O "$output" "$url"
elif command -v aria2c > /dev/null; then
	aria2c -o "$output" "$url"
elif command -v busybox > /dev/null; then
	busybox wget -O "$output" "$url"
else
	printf "No downloader is found on your system\n" >&2
	exit 1
fi
