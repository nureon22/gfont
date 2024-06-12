# Browse and install fonts from fonts.google.com

⚠️ **Warning: this project is still in development**

## Installation

```sh
git clone https://github.com/nureon22/gfont.git <dir>

cd <dir>

poetry install

poetry build

pip install dist/gfont-<version>-py3-none-any.whl
```

**In Debian, pipx is recommended instead of pip.**

### Requirements
#### Development Dependencies

* poetry

#### Runtime Dependencies

* requests
* imagemagick (optional) - Require to preview the font


#### Installing poetry in different Linux distributions

Debian based distributions
```sh
sudo apt install python3-poetry
```

Fedora based distributions
```sh
sudo dnf install poetry
```

Arch based distributions
```sh
sudo pacman -Sy python-poetry
```

## Usages

All commands support case-insensitive family names\
You can also use underscore (\_) instead of space character

### Search font families

```sh
gfont search "Noto Sans"
```

### Veiw information of a font family

```sh
gfont info "Noto Sans"
```

### View information of a font family in raw json format
This will show all the information

```sh
gfont info --raw "Noto Sans"
```

### Install a font family

```sh
gfont install "Noto Sans"
```

### Remove a installed font family

```sh
gfont remove "Noto Sans"
```

### Preview a font family

**Please install imagemagick first**
```sh
gfont preview "Noto Sans"
```

### List all available font families

```sh
gfont list
```

### List only installed font families

```sh
gfont list --installed
```

### Related files and directories

Metadata of all available families. This file will be refreshed every 24 hours.\
`$HOME/.cache/gfont/families_metadata.json`

Image of last previewed font family\
`$HOME/.cache/gfont/preview.png`

Directory for installed fonts\
`$HOME/.local/share/fonts/gfont`
