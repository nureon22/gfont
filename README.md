# Browse and install fonts from fonts.google.com

<!-- Browse and install fonts from fonts.google.com directly from your terminal -->

## Usages
All commands support case-insensitive family names\
You can also use underscore (_) instead of space character

### search a font family
```sh
gfont search "Noto Sans"
```

### Install a font family
```sh
gfont install "Noto Sans"
```

### List font families
```sh
gfont list
```

### List only installed font families
```sh
gfont list --installed
```

### view information of a font family
```sh
gfont info "Noto Sans"
```

### view information of a font family in raw json format
This will show all the informations
```sh
gfont info --raw "Noto Sans"
```


### Files Places

Metadata of all available families. This file will be refreshed every 24 hours.\
`$HOME/.cache/gfont/families_metadata.json`

Directory for installed fonts\
`$HOME/.local/share/fonts/gfont`