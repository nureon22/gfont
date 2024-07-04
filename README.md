# Browse and install fonts from fonts.google.com

⚠️ **Warning:** this project is still in development and doesn't support the Windows yet

**Note:** If you encounter some errors, clean cache files described at the end of the page.

- [Google Fonts API](#google-fonts-api)
- [Installation](#installation)
  - [Using pip](#using-pip)
  - [Using pipx](#using-pipx)
  - [Requirements](#requirements)
    - [Runtime Dependencies](#runtime-dependencies)
    - [Development Dependencies](#development-dependencies)
- [Usages](#usages)
  - [Search](#search)
  - [Install](#install)
  - [Remove](#remove)
  - [Info](#info)
  - [List](#list)
  - [Update](#update)
  - [webfont](#webfont)
  - [Preview](#preview)
  - [For mor information](#for-mor-information)
- [Related files](#related-files)

## Google Fonts API

By default, **gfont** doesn't need google font API key, instead it uses generated data/webfonts.json. This generated file won't be refreshed very often and contain older fonts. If you want more up-to-date fonts, add '**GOOGLE_FONTS_API_KEY**' environment variable inside ~/.bashrc or ~/.profile.

See, [Google Fonts Developer API](https://developers.google.com/fonts/docs/developer_api) to generate your API key.

## Installation

**Note:** For linux, pipx is recommended instead of pip

### Using pip

```sh
pip install "git+https://github.com/nureon22/gfont.git"
```

### Using pipx

```sh
pipx install "git+https://github.com/nureon22/gfont.git"
```

### Requirements

- python 3.7 or newer
- python-venv
- git

#### Runtime Dependencies

- requests
- imagemagick (optional) - Require to preview the font

#### Development Dependencies

- poetry (development)

## Usages

All commands support case-insensitive family names\
You can also use underscore (\_) instead of space character

### Search

```sh
gfont search "Noto Sans"
```

### Install

```sh
gfont install "Noto Sans"
```

### Remove

```sh
gfont remove "Noto Sans"
```

### Info

View overview information of the family

```sh
gfont info "Noto Sans"
```

### List

List installed families

```sh
gfont list
```

### Update

Update installed families

```sh
gfont update
```

### webfont

Pack a font family to use in websites as self-hosted fonts

```sh
gfont webfont "Noto Sans" --dir <dir>
```

### Preview

Install imagemagick first

```sh
gfont preview "Noto Sans"
```

### For mor information

`gfont <command> --help`

## Related files and directories

Directory for cached metadata of families

Linux: `~/.cache/gfont`\
Mac: `~/Library/Caches/gfont`

Directory for installed fonts

Linux: `~/.local/share/fonts/gfont`\
Mac: `~/Library/Fonts/gfont`
