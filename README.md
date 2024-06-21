# Browse and install fonts from fonts.google.com

⚠️ **Warning:** this project is still in development and doesn't support the Windows yet

- [Installation](#installation)
  - [Requirements](#requirements)
    - [Runtime Dependencies](#runtime-dependencies)
    - [Development Dependencies](#development-dependencies)
- [Usages](#usages)
  - [Install](#install)
  - [Search](#search)
  - [Veiw information](#veiw-information)
  - [Remove](#remove)
  - [Preview](#preview)
  - [List installed font families](#list-installed-font-families)
  - [Pack as webfont](#pack-as-webfont)
  - [For mor information](#for-mor-information)
- [Related files](#related-files)


## Installation

```sh
git clone https://github.com/nureon22/gfont.git <dir>

cd <dir>

sh devscripts/build.sh

pip install dist/gfont-<version>-py3-none-any.whl
```

**Note:** For linux, pipx is recommended instead of pip

### Requirements

* python 3.7 or newer
* python-venv
* git

#### Runtime Dependencies

* requests
* imagemagick (optional) - Require to preview the font

#### Development Dependencies

* poetry (development)

## Usages

All commands support case-insensitive family names\
You can also use underscore (\_) instead of space character

### Install

```sh
gfont install "Noto Sans"
```

### Pack as webfont
Pack a font family to use in websites as self-hosted fonts

```sh
gfont webfont "Noto Sans" --dir <dir>
```

### Search

```sh
gfont search "Noto Sans"
```

### Veiw information

```sh
gfont info "Noto Sans"
```

### Remove

```sh
gfont remove "Noto Sans"
```

### List installed font families

```sh
gfont list
```

### Preview

Please install imagemagick first
```sh
gfont preview "Noto Sans"
```

### Refresh
Refresh metadata of all available families into local cache (Optional).
```sh
gfont refresh
```

### For mor information
`gfont <command> --help`


## Related files and directories

List of all available font families. This file will be refreshed every 7 days

Linux: `~/.cache/gfont/families.json`\
Mac: `~/Library/Caches/gfont/families.json`


Directory for families metadata. Store as single JSON file per family.

Linux: `~/.cache/gfont/families/`\
Mac: `~/Library/Caches/gfont/families/`


Image of last previewed font family

Linux: `~/.cache/gfont/preview.png`\
Mac: `~/Library/Caches/gfont/preview.png`


Directory for installed fonts

Linux: `~/.local/share/fonts/gfont`\
Mac: `~/Library/Fonts/gfont`
