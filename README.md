# Browse and install fonts from fonts.google.com

⚠️ **Warning: this project is still in development**\
⚠️ **Warning: Doesn't support the Windows yet**

- [Installation](#installation)
  - [Requirements](#requirements)
- [Usages](#usages)
- [Related files and directories](#related-files-and-directories)

## Installation

```sh
git clone https://github.com/nureon22/gfont.git <dir>

cd <dir>

python3 -m venv .

. bin/activate

pip install -U pip

pip install -U poetry

poetry install
```

### Requirements

python 3.7 or newer

#### Development Dependencies

* poetry

#### Runtime Dependencies

* requests
* imagemagick (optional) - Require to preview the font

## Usages

All commands support case-insensitive family names\
You can also use underscore (\_) instead of space character

#### Install a font family

```sh
gfont install "Noto Sans"
```

#### Search font families

```sh
gfont search "Noto Sans"
```

#### Veiw information of a font family

```sh
gfont info "Noto Sans"
```

#### View information of a font family in raw json format
This will show all the information

```sh
gfont info --raw "Noto Sans"
```

#### Remove a installed font family

```sh
gfont remove "Noto Sans"
```

#### Preview a font family

**Please install imagemagick first**
```sh
gfont preview "Noto Sans"
```

#### List all available font families

```sh
gfont list
```

#### List only installed font families

```sh
gfont list --installed
```

#### Pack a font family to use in websites as self-hosted fonts

```sh
gfont webfont "Noto Sans" --dir <dir>
```

### Related files and directories

Metadata of all available families. This file will be refreshed every 24 hours.

Linux: `~/.cache/gfont/families_metadata.json`\
Mac: `~/Library/Caches/gfont/families_metadata.json`

Image of last previewed font family

Linux: `~/.cache/gfont/preview.png`\
Mac: `~/Library/Caches/gfont/preview.png`

Directory for installed fonts

Linux: `~/.local/share/fonts/gfont`\
Mac: `~/Library/Fonts/gfont`
