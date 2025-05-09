# Browse and install google fonts using terminal

**Note:** If you encounter some errors after upgrade, clean cache files described at the end of the page.

- [Supported Platforms](#supported-platforms)
- [Google Fonts API](#google-fonts-api)
- [Installation](#installation)
  - [Using pip](#using-pip)
  - [Using pipx](#using-pipx)
  - [Using zipapp](#using-zipapp)
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
  - [Tricks](#tricks)
  - [For mor information](#for-mor-information)
- [Related directories](#related-directories)

## Supported platforms
- Linux
- MacOS

## Google Fonts API

By default, **gfont** doesn't need google font API key, instead it uses generated data/webfonts.json. This generated file won't be refreshed very often and contains older fonts. If you want more up-to-date fonts, add '**GOOGLE_FONTS_API_KEY**' environment variable inside ~/.bashrc or ~/.profile.

See [Google Fonts Developer API](https://developers.google.com/fonts/docs/developer_api) to generate your API key.

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

### Using zipapp

- Download **gfont.pyz** from [Release Page](https://github.com/nureon22/gfont/releases/latest)
- Give gfont.pyz executable permission. `chmod +x gfont.pyz`
- Copy gfont.pyz to your PATH and you're ready to go

**Notes:** To get the new version, you need to follow the steps above again if you're using this method.

### For ArchLinux

For ArchLinux [gfont](https://aur.archlinux.org/packages/gfont) package is available in AUR

### Requirements

- python 3.8 or newer
- python-venv
- git

#### Runtime Dependencies

- requests

#### Development Dependencies

- hatch (development)

## Usages

All commands support case-insensitive family names.\
You can also use underscore (\_) or dash (-) or plus (+) instead of space character in family name.

### Search

Search available families

```sh
gfont search noto sans
```

### Install

Install one or more families

```sh
gfont install noto-sans
```

### Remove

Remove one or more families

```sh
gfont remove noto-sans
```

### Info

View overview information of the family

```sh
gfont info noto-sans
```

### List

List installed families

```sh
gfont list
```

### Update

Update installed families to latest version

```sh
gfont update
```

### Webfont

Pack woff2 fonts and it's css to be used as self-hosted fonts in websites.\
Don't forget to use single or double quotes for safety.

```sh
gfont webfont "noto-sans" --dir <dir>
```

```sh
gfont webfont "noto-sans:ital,wght@0,400;0,700" --dir <dir>
```

```sh
gfont webfont "open-sans:ital,wght@0,300..700" --dir <dir>
```

### Tricks

Install search results

```sh
gfont install $(gfont search noto sans | sed 's/ /_/g')
```

### For mor information

`gfont <command> --help`

## Related directories

Directory for cached metadata of families

Linux: `~/.cache/gfont`\
Mac: `~/Library/Caches/gfont`

Directory for installed fonts

Linux: `~/.local/share/fonts/gfont`\
Mac: `~/Library/Fonts/gfont`
