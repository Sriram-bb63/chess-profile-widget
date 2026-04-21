# chess-profile-widget

Showcase your Chess.com/lichess profile as a widget in your GitHub home page and/or in your portfolio, blogs, social media etc. You can practically use it anywhere since it is a fully self contained SVG.

## Sample widget

<img src="https://chess-profile-widget.onrender.com/widget?platform=chess-dot-com&username=hikaru" alt="chess-profile-widget"/>

<img src="https://chess-profile-widget.onrender.com/widget?platform=lichess&username=ArtOfDeception&theme=brown" alt="chess-profile-widget"/>

<img src="https://chess-profile-widget.onrender.com/widget?platform=chess-dot-com&username=1234bb63&logo=true&theme=blues" alt="chess-profile-widget"/>

<img src="https://chess-profile-widget.onrender.com/widget?platform=lichess&username=Kurald_Galain&theme=dracula&logo=true" alt="chess-profile-widget"/>

## How to use

Provide the following inputs as URL params to get started:
- Platform - "chess-dot-com" or "lichess"
- Username - your Chess.com or Lichess username
- Footer with logo (optional) - "true" or "false" (default is "false")
- Theme (optional) - choose from the available themes listed below

### URL parameters

1. `platform` *required* - "chess-dot-com" or "lichess" to get your account data
2. `username` *required* - Your username
3. `theme` *optional* - Any of the themes listed below. If a theme could not be found, the default theme is used
4. `logo` *optional* - `true` to display a footer section with the platform logo. Default value is `false`

### Embed in a ``*.md`` file

```md
![chess-profile-widget](https://chess-profile-widget.onrender.com/widget?platform=your-platform&username=your-username&theme=your-theme&logo=false)
```
or
```md
<p align="center">
  <img src="https://chess-profile-widget.onrender.com/widget?platform=your-platform&username=your-username&theme=your-theme&logo=false" alt="chess-profile-widget"/>
</p>
```

### Embed in a ``*.html`` file

```html
<img src="https://chess-profile-widget.onrender.com/widget?platform=your-platform&username=your-username&theme=your-theme&logo=false" alt="chess-profile-widget">
```

> You can also use ``iframe`` / ``div`` / ``embed`` tags if you prefer



### Available themes

1. default
2. black
3. github-dark
4. blues
5. white
6. red
7. dracula
8. terminal
9. brown
10. solarized-dark
