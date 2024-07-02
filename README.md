# Browse and install fonts from fonts.google.com

⚠️ **Warning:** this project is still in development and doesn't support the Windows yet

**Note:** If you encounter some errors, clean cache files described at the end of the page.

- [Installation](#installation)
  - [Requirements](#requirements)
    - [Runtime Dependencies](#runtime-dependencies)
    - [Development Dependencies](#development-dependencies)
- [Usages](#usages)
  - [Install](#install)
  - [Pack as webfont](#pack-as-webfont)
  - [Search](#search)
  - [Veiw information](#veiw-information)
  - [Remove](#remove)
  - [List installed font families](#list-installed-font-families)
  - [Preview](#preview)
  - [Refresh](#refresh)
  - [For mor information](#for-mor-information)
- [Related files](#related-files)


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

### For mor information
`gfont <command> --help`


## Related files and directories

Directory for cached metadata of families

Linux: `~/.cache/gfont`\
Mac: `~/Library/Caches/gfont`


Directory for installed fonts

Linux: `~/.local/share/fonts/gfont`\
Mac: `~/Library/Fonts/gfont`
