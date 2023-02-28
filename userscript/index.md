% Teodle for Twitch

<style>
header {
    margin-bottom: 1.5em;
}
</style>
<script src="./static/darkreader.min.js"></script>
<script>
    DarkReader.enable({
        brightness: 100,
        contrast: 100,
        sepia: 10
    })
</script>

<center>

A handy userscript for Twitch.tv which adds some more Teodle integration.

![](./static/2023-02-28_10-10-36.png)

</center>

## Features 💫

- Tracks your personal score ⭐️
- Lists current clip ranks
- Indicates your vote (yellow dot)
- Indicates the correct answer (yellow border)
- Very lightweight with realtime updates

## How to install 💾

1. Install a userscript manager, for example:

|     Name      |                                 Link                                 | Chrome | Firefox | OpenSource |
| :-----------: | :------------------------------------------------------------------: | :----: | :-----: | :--------: |
| Violentmonkey |           [Link](https://violentmonkey.github.io/get-it/)            |   ✔    |    ✔    |     ✔      |
| Greasemonkey  | [Link](https://addons.mozilla.org/en-US/firefox/addon/greasemonkey/) |        |    ✔    |     ✔      |
| Tampermonkey  |                  [Link](https://tampermonkey.net/)                   |   ✔    |    ✔    |            |

2. Open the script and click <code>Install</code>:<br>
   [https://teodle.monicz.dev/teodle.user.js](https://teodle.monicz.dev/teodle.user.js)

<center>![](./static/2023-02-28_10-57-05.png)</center>

3. Done, don't forget to refresh the Twitch website

## How to uninstall 🗑️

1. Open the userscript manager
2. Find the "Teodle for Twitch" and click <code>Remove</code>

<center>![](./static/2023-02-28_10-45-27.png)</center>

## FAQ

### Is it safe?

The script is open source and is [publicly available](https://github.com/Zaczero/teodle/blob/main/userscript/teodle.user.js).
Everyone can audit its functionality and verify that it does not contain any malicious code.
Only basic JavaScript knowledge is required to do so.

### Does it track me?

No.

### Does it collect any data?

It only collects your Twitch username for the purpose of score keeping.

### How to update the script?

Whenever there is a new version available, the userscript manager will notify you about it.
You will have to simply confirm the update with a single click.

### How to report a bug?

Please use the [GitHub issue tracker](https://github.com/Zaczero/teodle/issues) or contact me directly (email below).
Don't forget to describe the problem and include the steps to reproduce it.
It would be helpful if you could also attach the console output from the browser (<kbd>F12</kbd>).

<center>![](./static/2023-02-28_11-06-27.png)</center>

## Extra resources 📚

- Email: [kamil@monicz.pl](mailto:kamil@monicz.pl)

- Source code on GitHub: [Zaczero/teodle](https://github.com/Zaczero/teodle)

- License: [AGPL-3.0](https://github.com/Zaczero/teodle/blob/main/LICENSE)
