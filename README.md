# fman-fuzzy-search-files

Forked from https://github.com/kszcode/FuzzySearchFilesInCurrentFolder

This is a plugin to locate files and folders with fuzzy search in [fman](https://fman.io/).

It uses a regex to match the filenames and sort the results by match length which makes the result more usable when dealing with a lot of files.

## Features

- Search file in current sub folders: pressing CMD+F or CTRL+F will popup the quick search and you can fuzzy find the file or folder looking into all the subfolders. For performance reasons only 15000 files are loaded, this is also signaled in the status bar.

## Installation

Go to the command pallete: SHIFT+CMD+P > Install Plugin >FuzzySearchFilesInCurrentFolder

You can also install it manually just copy the contents of this folder to:

```~/Library/Application Support/fman/Plugins/User/fman-fuzzy-search-files```

For development I suggest you symlink it:
```
ln -s "$(pwd)" "$HOME/Library/Application Support/fman/Plugins/User/fman-fuzzy-search-files"
```
