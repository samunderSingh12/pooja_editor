# SimpleModEdit - A Simple, Modular Terminal Text Editor

Welcome to SimpleModEdit! This is a basic text editor that runs in your terminal. It's built with Python and designed to be easy to understand and modify.

The coolest part? It's **modular**! You can add new features (like syntax highlighting, search, etc.) by creating simple "plugin" files, without changing the main editor code.

**Status:** Very basic, proof-of-concept.

## Features

*   Basic text editing (typing, deleting, moving the cursor)
*   File loading and saving (via the included 'Save' plugin)
*   Extremely simple codebase (hopefully!)
*   Modular plugin system

## Included Plugins

*   **Save:** Allows saving the current file using `Ctrl+S`.

## How to Run

1.  Make sure you have Python 3 installed.
2.  Clone or download this project code.
3.  Open your terminal or command prompt.
4.  Navigate (`cd`) into the `pooja_code_editor` directory (or whatever you named it).
5.  Run the editor:
    *   To edit a new, unnamed file: `python3 simple_editor.py`
    *   To edit an existing file (or create a new named one): `python3 simple_editor.py my_file.txt`

## Basic Usage

*   **Arrow Keys:** Move the cursor (Up, Down, Left, Right).
*   **Home/End:** Move cursor to the beginning/end of the line.
*   **PageUp/PageDown:** Scroll the view up/down by a screen height.
*   **Typing:** Inserts characters at the cursor position.
*   **Enter:** Creates a new line.
*   **Backspace:** Deletes the character *before* the cursor. Joins lines if at the beginning of a line.
*   **Delete:** Deletes the character *under* the cursor. Joins lines if at the end of a line.
*   **Ctrl+S:** Save the file (provided by the `plugin_save.py`). Will ask for a filename if the file is new.
*   **Ctrl+Q:** Quit the editor. Will ask for confirmation if you have unsaved changes.

## How to Create Your Own Plugin

This is where the fun begins! Adding features is easy:

1.  **Create a Plugin File:**
    *   Go into the `plugins/` directory.
    *   Create a new Python file. Name it starting with `plugin_` (e.g., `plugin_myfeature.py`).

2.  **Write the `register` Function:**
    *   Every plugin file *must* have a function called `register`.
    *   The main editor will automatically call this function when it starts.
    *   This function receives two arguments:
        *   `editor_state`: A dictionary holding all the editor's current information (like the text lines, cursor position, filename, etc.). You can look at this dictionary but try not to change it directly unless you use the provided tools.
        *   `core_tools`: A dictionary containing useful functions provided by the main editor that your plugin can use.

3.  **Use the `core_tools`:**
    *   Inside your `register` function (and any other functions your plugin uses), you'll use the functions from the `core_tools` dictionary to interact with the editor. Store this dictionary globally in your plugin or pass it around.
    *   **Key Tools Available:**
        *   `tell_core_about_key(editor_state, key_code, your_function)`: Links a key press to *your* plugin function. When the user presses that key, your function will run. (Key codes are numbers, e.g., `19` for `Ctrl+S`, `curses.KEY_F1` for F1, etc.)
        *   `ask_user(editor_state, prompt_message)`: Shows a message at the bottom and waits for the user to type something. Returns the typed text.
        *   `show_message(editor_state, message)`: Displays a message in the status bar at the bottom.
        *   `get_lines(editor_state)`: Returns the list of all text lines currently in the editor.
        *   `get_filename(editor_state)`: Returns the current filename (or `None`).
        *   `set_filename(editor_state, new_name)`: Tells the editor to use a new filename.
        *   `mark_as_changed(editor_state)`: Marks the file as having unsaved changes.
        *   `mark_as_saved(editor_state)`: Marks the file as saved.
        *   `get_cursor_pos(editor_state)`: Returns the current cursor position as `(row, column)`.
        *   *(More tools could be added to the core editor later)*

4.  **Write Your Action Function(s):**
    *   If your plugin responds to a key press (using `tell_core_about_key`), you need to write the function that actually does the work!
    *   This "action function" will receive the `editor_state` dictionary as its only argument.
    *   Inside your action function, use the `core_tools` (which you should have stored from the `register` step) to interact with the editor (e.g., show messages, get lines, etc.).

### Example: A Simple "Show Cursor Position" Plugin (`plugins/plugin_showpos.py`)

```python
# plugins/plugin_showpos.py

# A very simple plugin to show the cursor position on Ctrl+G

# Store the core tools globally
core_tools = {}

def show_cursor_position_action(editor_state):
    """Runs when Ctrl+G is pressed."""
    # Get the functions we need from the stored tools
    show_message = core_tools.get('show_message')
    get_cursor_pos = core_tools.get('get_cursor_pos')

    if show_message and get_cursor_pos:
        # Get the current row and column
        row, col = get_cursor_pos(editor_state)
        # Show them in the status bar
        show_message(editor_state, f"Cursor at Line: {row + 1}, Column: {col + 1}")
    else:
        # Should not happen, but good to handle
        print("Error: ShowPos plugin missing core tools!", file=sys.stderr)


def register(editor_state, provided_core_tools):
    """Registers the Ctrl+G keybinding."""
    global core_tools
    core_tools = provided_core_tools # Store the tools

    register_key_func = core_tools.get('tell_core_about_key')

    if register_key_func:
        ctrl_g_key_code = 7 # ASCII code for Ctrl+G
        # Link Ctrl+G to our action function
        register_key_func(editor_state, ctrl_g_key_code, show_cursor_position_action)
    else:
        print("Error: ShowPos plugin could not find 'tell_core_about_key'.", file=sys.stderr)

```

Just save this code as plugins/plugin_showpos.py, and the next time you run simple_editor.py, pressing Ctrl+G will show the cursor position in the status bar!
Contributing
This is a basic project. Feel free to fork it, improve it, add plugins, and submit pull requests! Ideas:
Search/Replace plugin
Syntax highlighting (this is hard!)
Copy/Paste plugin
Line numbering display
More robust error handling
