#!/usr/bin/env python3

# Import necessary tools
import curses         # For handling the terminal screen and keys
import os             # For working with files (like checking if they exist)
import sys            # For getting command line arguments (like the filename)
import importlib      # For loading plugin files dynamically
import glob           # For finding plugin files easily
import traceback      # For showing helpful error messages

# --- Setting up the Editor's Memory ---

def setup_editor_state(screen, filename=None):
    """
    Creates a dictionary to hold all the information about our editor.
    Think of this like the editor's brain or memory.
    """
    editor_state = {
        "screen": screen,            # The actual terminal screen object from curses
        "filename": None,            # The name of the file we are editing
        "lines": [""],               # The text content, stored as a list of strings (one string per line)
        "cursor_row": 0,             # Which line number the cursor is on (0 is the first line)
        "cursor_col": 0,             # Which column number the cursor is on (0 is the first character)
        "top_screen_line": 0,        # Which line from our file is shown at the very top of the screen
        "left_screen_col": 0,        # Which column from our file is shown at the very left of the screen
        "screen_height": 0,          # How many rows the terminal window has (we set this later)
        "screen_width": 0,           # How many columns the terminal window has (we set this later)
        "key_actions": {},           # Stores actions linked to specific keys (added by plugins)
        "status_message": "SimpleEdit | Ctrl+Q: Quit", # Message shown at the bottom
        "is_dirty": False,           # Tracks if the file has been changed since opening/saving (starts as False)
    }

    # If a filename was given when starting the editor, try to load it
    if filename:
        load_file_into_editor(editor_state, filename)
        # Update status bar if file loaded, otherwise load_file sets an error message
        if editor_state["filename"]:
            editor_state["status_message"] = f"File: {filename} | Ctrl+Q: Quit"

    return editor_state

# --- Working with Files ---

def load_file_into_editor(editor_state, filename):
    """
    Reads a file from the disk and puts its content into the editor's memory.
    """
    try:
        # Make sure the file exists and it's not a folder
        if os.path.exists(filename) and not os.path.isdir(filename):
            # Open the file, read all lines, and remove trailing newline characters
            # Use 'utf-8' which is common, replace weird characters if needed
            with open(filename, 'r', encoding='utf-8', errors='replace') as f:
                editor_state["lines"] = [line.rstrip('\n\r') for line in f]
            # If the file was empty, make sure we still have one empty line to type on
            if not editor_state["lines"]:
                editor_state["lines"] = [""]
            editor_state["filename"] = filename # Remember the filename
            editor_state["is_dirty"] = False   # It's clean just after loading
            # Reset cursor and scroll position for the new file
            editor_state["cursor_row"], editor_state["cursor_col"] = 0, 0
            editor_state["top_screen_line"], editor_state["left_screen_col"] = 0, 0
            editor_state["status_message"] = f"Opened: {filename}" # Update status

        elif os.path.isdir(filename):
            # We can't edit folders! Show an error.
            editor_state["status_message"] = f"Error: '{filename}' is a folder."
            editor_state["filename"] = None
            editor_state["lines"] = [""] # Keep an empty line
            editor_state["is_dirty"] = False
            editor_state["cursor_row"], editor_state["cursor_col"] = 0, 0
            editor_state["top_screen_line"], editor_state["left_screen_col"] = 0, 0

        else:
            # File doesn't exist, so we're creating a new one
            editor_state["filename"] = filename
            editor_state["lines"] = [""] # Start with one empty line
            editor_state["is_dirty"] = False # A new file isn't dirty yet
            editor_state["cursor_row"], editor_state["cursor_col"] = 0, 0
            editor_state["top_screen_line"], editor_state["left_screen_col"] = 0, 0
            editor_state["status_message"] = f"New File: {filename} | Ctrl+Q: Quit"

    except Exception as e:
        # If anything went wrong during loading
        editor_state["lines"] = [""] # Start fresh
        editor_state["status_message"] = f"Error loading {filename}: {e}"
        editor_state["filename"] = None
        editor_state["is_dirty"] = False
        editor_state["cursor_row"], editor_state["cursor_col"] = 0, 0
        editor_state["top_screen_line"], editor_state["left_screen_col"] = 0, 0

# --- Plugin System (Like adding extra Lego blocks) ---

def find_and_load_plugins(editor_state):
    """
    Looks for Python files in the 'plugins' folder and tells them to register
    their features (like new key actions) with the editor.
    """
    # Find the 'plugins' folder next to this script file
    script_dir = os.path.dirname(__file__)
    plugins_dir = os.path.join(script_dir, 'plugins')

    # If the 'plugins' folder doesn't exist, we can't load any plugins
    if not os.path.isdir(plugins_dir):
        return

    # Look for all files ending with '.py' inside the 'plugins' folder
    # We use a pattern like 'plugin_*.py' to be specific
    plugin_files = glob.glob(os.path.join(plugins_dir, 'plugin_*.py'))

    # Go through each plugin file found
    for plugin_file_path in plugin_files:
        # Get the base name of the file (e.g., 'plugin_save')
        module_name = os.path.basename(plugin_file_path)[:-3] # Remove '.py'

        try:
            # Try to load the plugin file as a Python module
            # We tell Python to look inside the 'plugins' package
            plugin_module = importlib.import_module(f"plugins.{module_name}")

            # Check if the plugin has a function called 'register'
            if hasattr(plugin_module, 'register') and callable(plugin_module.register):
                # Prepare the tools (functions) the plugin might need from the core editor
                core_editor_tools = {
                    'tell_core_about_key': tell_core_about_key, # Function to link a key to an action
                    'ask_user': ask_user_for_input,          # Function to ask the user something
                    'show_message': show_message_in_status, # Function to show status messages
                    'get_lines': lambda state: state["lines"],         # Function to get all text lines
                    'get_filename': lambda state: state["filename"],    # Function to get the current filename
                    'set_filename': lambda state, name: state.update({"filename": name}), # Function to set filename
                    'mark_as_changed': mark_file_as_changed, # Function to mark file dirty
                    'mark_as_saved': mark_file_as_saved,     # Function to mark file clean
                    'get_cursor_pos': lambda state: (state["cursor_row"], state["cursor_col"]), # Get cursor position
                }
                # Call the plugin's 'register' function, giving it the editor's memory
                # and the toolbox of core functions it can use.
                plugin_module.register(editor_state, core_editor_tools)
                # print(f"Loaded plugin: {module_name}") # For debugging

            else:
                # The plugin file is missing the 'register' function
                print(f"Warning: Plugin '{module_name}' has no register() function.", file=sys.stderr)

        except Exception as e:
            # If loading the plugin failed, stop the editor and show the error
            curses.endwin() # Clean up the screen first
            print(f"\nError loading plugin '{module_name}': {e}", file=sys.stderr)
            traceback.print_exc() # Show detailed error info
            sys.exit(1) # Quit the program

def tell_core_about_key(editor_state, key_code, action_function):
    """
    Lets a plugin link a specific key (like Ctrl+S) to a function
    that should run when that key is pressed.
    """
    if not callable(action_function):
        print("Error: Plugin tried to register a non-function for a key.", file=sys.stderr)
        return
    # Store the link: key -> function
    editor_state["key_actions"][key_code] = action_function

# --- Functions for Plugins to Use (via core_editor_tools) ---

def show_message_in_status(editor_state, message):
    """Updates the message shown at the bottom of the screen."""
    editor_state["status_message"] = message

def mark_file_as_changed(editor_state):
    """Marks the file as having unsaved changes."""
    if not editor_state["is_dirty"]:
        editor_state["is_dirty"] = True

def mark_file_as_saved(editor_state):
    """Marks the file as saved (no unsaved changes)."""
    editor_state["is_dirty"] = False

# --- Drawing the Editor on the Screen ---

def show_editor_on_screen(editor_state):
    """
    Clears the screen and draws the text lines, status bar, and cursor.
    This function runs repeatedly to update what the user sees.
    """
    screen = editor_state["screen"]
    try:
        # Get the current size of the terminal window
        editor_state["screen_height"], editor_state["screen_width"] = screen.getmaxyx()

        # Make sure the window isn't impossibly small
        if editor_state["screen_height"] <= 1 or editor_state["screen_width"] <= 0:
            if editor_state["screen_height"] > 0 and editor_state["screen_width"] > 0:
                screen.addstr(0, 0, "Window too small!") # Show error if possible
            return # Don't try to draw if too small

        # Clear the whole screen
        screen.erase()

        # Calculate how many lines of text can fit (screen height minus status bar)
        display_height = editor_state["screen_height"] - 1

        # Draw the lines of text that should be visible
        for screen_row in range(display_height):
            # Figure out which line from our file corresponds to this screen row
            file_line_index = editor_state["top_screen_line"] + screen_row

            # Check if this line actually exists in our file
            if file_line_index < len(editor_state["lines"]):
                line_text = editor_state["lines"][file_line_index]

                # Figure out which part of the line to show based on horizontal scroll
                start_col = editor_state["left_screen_col"]
                end_col = start_col + editor_state["screen_width"]
                display_text = line_text[start_col:end_col]

                # Add spaces to the end to clear any old text from the screen line
                display_text += " " * (editor_state["screen_width"] - len(display_text))

                # Draw the text on the screen at the correct row and column 0
                # Use try/except because the window might resize while drawing
                try:
                    screen.addstr(screen_row, 0, display_text)
                except curses.error:
                    pass # Ignore if we can't draw this line (e.g., window shrunk)
            else:
                # If there are no more lines in the file, maybe draw a '~' like Vim (optional)
                # try:
                #     screen.addstr(screen_row, 0, "~" + " " * (editor_state["screen_width"] - 1))
                # except curses.error:
                #     pass
                 pass # Or just leave it blank


        # --- Draw the Status Bar at the bottom ---
        status_text = editor_state["status_message"]
        # Add a '*' if the file has unsaved changes
        if editor_state["is_dirty"]:
            status_text += " *"

        # Shorten status text if it's too long for the screen width
        status_text = status_text[:editor_state["screen_width"]]

        # Add spaces to fill the rest of the status bar line
        status_line = status_text + " " * (editor_state["screen_width"] - 1 - len(status_text))

        try:
            # Set background color for status bar (A_REVERSE swaps background/foreground)
            screen.attron(curses.A_REVERSE)
            # Draw the status bar on the last screen line
            screen.addstr(editor_state["screen_height"] - 1, 0, status_line[:editor_state["screen_width"]-1])
            screen.attroff(curses.A_REVERSE) # Turn off reverse color
        except curses.error:
            pass # Ignore drawing errors

        # --- Position the actual blinking cursor ---
        # Calculate where the cursor should appear on the screen based on its
        # position in the file and the current scrolling offsets.
        screen_cursor_row = editor_state["cursor_row"] - editor_state["top_screen_line"]
        screen_cursor_col = editor_state["cursor_col"] - editor_state["left_screen_col"]

        # Make sure the calculated screen position is actually visible
        screen_cursor_row = max(0, min(screen_cursor_row, display_height - 1))
        screen_cursor_col = max(0, min(screen_cursor_col, editor_state["screen_width"] - 1))

        try:
            # Move the terminal's cursor to the calculated position
            screen.move(screen_cursor_row, screen_cursor_col)
        except curses.error:
            # If the position is somehow invalid (e.g., during resize), move to top-left corner
            try:
                screen.move(0, 0)
            except curses.error:
                pass # Ignore if even (0,0) fails

        # Tell curses to update the actual terminal display
        screen.refresh()

    except curses.error as e:
        # Catch potential errors during drawing, often related to window resizing
        # We can't easily show messages here, so we just ignore them for now
        pass

# --- Scrolling Logic ---

def move_cursor_and_scroll(editor_state):
    """
    Checks if the cursor has moved off the visible screen area.
    If so, it adjusts the `top_screen_line` or `left_screen_col`
    so the cursor becomes visible again (this makes the text scroll).
    """
    # Make sure screen dimensions are valid
    if editor_state["screen_height"] <= 1 or editor_state["screen_width"] <= 0:
        return # Can't scroll if screen is too small

    display_height = editor_state["screen_height"] - 1
    screen_width = editor_state["screen_width"]

    # --- Vertical Scrolling ---
    # If cursor is above the top visible line
    if editor_state["cursor_row"] < editor_state["top_screen_line"]:
        editor_state["top_screen_line"] = editor_state["cursor_row"]
    # If cursor is below the bottom visible line
    elif editor_state["cursor_row"] >= editor_state["top_screen_line"] + display_height:
        editor_state["top_screen_line"] = editor_state["cursor_row"] - display_height + 1

    # --- Horizontal Scrolling ---
    # If cursor is left of the first visible column
    if editor_state["cursor_col"] < editor_state["left_screen_col"]:
        editor_state["left_screen_col"] = editor_state["cursor_col"]
    # If cursor is right of the last visible column
    elif editor_state["cursor_col"] >= editor_state["left_screen_col"] + screen_width:
        editor_state["left_screen_col"] = editor_state["cursor_col"] - screen_width + 1

    # --- Make sure scroll values don't go out of bounds ---
    # Don't scroll past the beginning of the file
    editor_state["top_screen_line"] = max(0, editor_state["top_screen_line"])
    editor_state["left_screen_col"] = max(0, editor_state["left_screen_col"])
    # Don't scroll too far down (though drawing logic often handles this)
    # max_top_line = max(0, len(editor_state["lines"]) - display_height)
    # editor_state["top_screen_line"] = min(editor_state["top_screen_line"], max_top_line)


# --- Asking the User for Input (like for filename) ---

def ask_user_for_input(editor_state, prompt_message=""):
    """
    Shows a message in the status bar and waits for the user to type something.
    Returns the text the user typed, or None if they cancelled (e.g., pressed Esc).
    """
    screen = editor_state["screen"]
    height = editor_state["screen_height"]
    width = editor_state["screen_width"]

    # Need a valid screen size to show the prompt
    if height <= 1 or width <= 1:
        return None # Cannot show prompt

    original_status = editor_state["status_message"] # Remember the current status

    input_text = None # Default to None (cancel)
    try:
        # --- Show the prompt message ---
        prompt_display = prompt_message[:width - 1] # Truncate if too long
        status_line = prompt_display + " " * (width - 1 - len(prompt_display))
        screen.attron(curses.A_REVERSE)
        screen.addstr(height - 1, 0, status_line)
        screen.attroff(curses.A_REVERSE)

        # --- Position cursor for typing ---
        input_start_col = len(prompt_display)
        # Make sure cursor fits on the screen
        if input_start_col >= width - 1:
            input_start_col = width - 2
        screen.move(height - 1, input_start_col)

        # --- Enable typing echo and blinking cursor ---
        curses.echo()       # Show characters as they are typed
        curses.curs_set(1)  # Make cursor visible
        screen.refresh()    # Update screen to show prompt and cursor

        # --- Get the user's input ---
        # curses.getstr is simpler for getting a whole line of input
        max_len = width - input_start_col - 1 # Max chars that fit
        if max_len < 0: max_len = 0
        # getstr returns bytes, need to decode to a string
        input_bytes = screen.getstr(height - 1, input_start_col, max_len)
        input_text = input_bytes.decode('utf-8', errors='replace')

    except KeyboardInterrupt:
        # User pressed Ctrl+C - treat as cancellation
        input_text = None
    except curses.error:
        # Any other screen error during input - treat as cancellation
        input_text = None
    finally:
        # --- Restore normal terminal settings ---
        curses.noecho()     # Stop echoing typed characters
        curses.curs_set(1)  # Keep cursor visible for editor
        # Restore the original status message (the main loop will redraw it fully)
        editor_state["status_message"] = original_status
        # No need to redraw here, the main loop does it after this function returns

    return input_text

# --- Handling Key Presses ---

def handle_key_press(editor_state, key_pressed):
    """
    This function decides what to do based on the key the user pressed.
    It might move the cursor, insert text, delete text, or run a plugin action.
    Returns `False` if the editor should quit, `True` otherwise.
    """
    action_was_taken = False # Flag to know if we need to re-check scrolling

    # Get the current state for easier access
    screen = editor_state["screen"]
    lines = editor_state["lines"]
    row = editor_state["cursor_row"]
    col = editor_state["cursor_col"]

    # --- 1. Check if a Plugin handles this key ---
    if key_pressed in editor_state["key_actions"]:
        action_function = editor_state["key_actions"][key_pressed]
        action_function(editor_state) # Call the plugin's function
        action_was_taken = True # Assume plugin did something

    # --- 2. Handle Built-in Editor Keys ---

    # --- Cursor Movement ---
    elif key_pressed == curses.KEY_UP:
        if row > 0:
            editor_state["cursor_row"] -= 1
            # Snap cursor to end of shorter line if needed
            new_col = min(col, len(lines[editor_state["cursor_row"]]))
            editor_state["cursor_col"] = new_col
            action_was_taken = True
    elif key_pressed == curses.KEY_DOWN:
        if row < len(lines) - 1:
            editor_state["cursor_row"] += 1
            # Snap cursor to end of shorter line if needed
            new_col = min(col, len(lines[editor_state["cursor_row"]]))
            editor_state["cursor_col"] = new_col
            action_was_taken = True
    elif key_pressed == curses.KEY_LEFT:
        if col > 0:
            editor_state["cursor_col"] -= 1
            action_was_taken = True
        elif row > 0: # Wrap to end of previous line
            editor_state["cursor_row"] -= 1
            editor_state["cursor_col"] = len(lines[editor_state["cursor_row"]])
            action_was_taken = True
    elif key_pressed == curses.KEY_RIGHT:
        current_line_len = len(lines[row])
        if col < current_line_len:
            editor_state["cursor_col"] += 1
            action_was_taken = True
        elif row < len(lines) - 1: # Wrap to start of next line
            editor_state["cursor_row"] += 1
            editor_state["cursor_col"] = 0
            action_was_taken = True
    elif key_pressed == curses.KEY_HOME:
        editor_state["cursor_col"] = 0
        action_was_taken = True
    elif key_pressed == curses.KEY_END:
        editor_state["cursor_col"] = len(lines[row])
        action_was_taken = True
    elif key_pressed == curses.KEY_PPAGE: # Page Up
        if editor_state["screen_height"] > 1:
             display_height = editor_state["screen_height"] - 1
             editor_state["cursor_row"] = max(0, row - display_height)
             editor_state["top_screen_line"] = max(0, editor_state["top_screen_line"] - display_height)
             # Adjust column to new line length
             new_col = min(col, len(lines[editor_state["cursor_row"]]))
             editor_state["cursor_col"] = new_col
             action_was_taken = True
    elif key_pressed == curses.KEY_NPAGE: # Page Down
        if editor_state["screen_height"] > 1:
             display_height = editor_state["screen_height"] - 1
             max_row = len(lines) - 1
             editor_state["cursor_row"] = min(max_row, row + display_height)
             editor_state["top_screen_line"] = min(max(0, len(lines) - display_height), editor_state["top_screen_line"] + display_height)
             # Adjust column to new line length
             new_col = min(col, len(lines[editor_state["cursor_row"]]))
             editor_state["cursor_col"] = new_col
             action_was_taken = True

    # --- Deleting Text ---
    elif key_pressed == curses.KEY_BACKSPACE or key_pressed == 127 or key_pressed == 8:
        if col > 0: # If not at the start of the line, delete char before cursor
            current_line = lines[row]
            lines[row] = current_line[:col-1] + current_line[col:]
            editor_state["cursor_col"] -= 1
            mark_file_as_changed(editor_state)
            action_was_taken = True
        elif row > 0: # If at start of line (not first line), join with previous line
            line_to_move = lines.pop(row) # Remove current line
            editor_state["cursor_row"] -= 1
            # Move cursor to end of the (now longer) previous line
            editor_state["cursor_col"] = len(lines[editor_state["cursor_row"]])
            lines[editor_state["cursor_row"]] += line_to_move # Append removed line
            mark_file_as_changed(editor_state)
            action_was_taken = True
    elif key_pressed == curses.KEY_DC: # Delete key
        current_line = lines[row]
        if col < len(current_line): # If not at end of line, delete char under cursor
            lines[row] = current_line[:col] + current_line[col+1:]
            # Cursor stays in the same column position
            mark_file_as_changed(editor_state)
            action_was_taken = True
        elif row < len(lines) - 1: # If at end of line (not last line), join with next line
            line_to_join = lines.pop(row + 1) # Remove next line
            lines[row] += line_to_join        # Append it to current line
            # Cursor stays in the same position (end of the now longer line)
            mark_file_as_changed(editor_state)
            action_was_taken = True

    # --- Inserting Newline (Enter Key) ---
    elif key_pressed == curses.KEY_ENTER or key_pressed in [10, 13]:
        current_line = lines[row]
        # Text before cursor stays on current line
        lines[row] = current_line[:col]
        # Text after cursor goes to a new line inserted below
        line_after_cursor = current_line[col:]
        lines.insert(row + 1, line_after_cursor)
        # Move cursor to beginning of the new line
        editor_state["cursor_row"] += 1
        editor_state["cursor_col"] = 0
        mark_file_as_changed(editor_state)
        action_was_taken = True

    # --- Quitting (Ctrl+Q) ---
    elif key_pressed == 17: # ASCII code for Ctrl+Q
        if editor_state["is_dirty"]: # Check for unsaved changes
            # Ask for confirmation
            confirm = ask_user_for_input(editor_state, "Unsaved changes! Quit anyway? (y/N): ")
            action_was_taken = True # Need redraw after prompt anyway
            if confirm and confirm.lower() == 'y':
                return False # Signal to quit
            else:
                show_message_in_status(editor_state, "Quit cancelled.")
                # Stay in editor, return True
        else:
            return False # No unsaved changes, signal to quit

    # --- Typing Printable Characters ---
    # Check if the key code is in the range of standard printable ASCII characters
    elif 32 <= key_pressed <= 126:
        char_to_insert = chr(key_pressed) # Convert number code to character
        current_line = lines[row]
        # Insert character at cursor position
        lines[row] = current_line[:col] + char_to_insert + current_line[col:]
        editor_state["cursor_col"] += 1 # Move cursor forward
        mark_file_as_changed(editor_state)
        action_was_taken = True

    # --- Handle Terminal Resize Event ---
    elif key_pressed == curses.KEY_RESIZE:
         # Curses handles the resize internally. We just need to redraw.
         # The main loop will call show_editor_on_screen which updates dimensions.
         # We might also need to re-check scrolling.
         action_was_taken = True


    # --- If any action changed cursor or text, make sure we scroll if needed ---
    if action_was_taken:
        move_cursor_and_scroll(editor_state)

    # Return True to keep the editor running
    return True

# --- The Main Editor Loop ---

def run_editor_loop(editor_state):
    """
    The heart of the editor. It repeatedly:
    1. Draws the screen.
    2. Waits for a key press.
    3. Handles the key press.
    It stops when handle_key_press returns False (usually on Ctrl+Q).
    """
    screen = editor_state["screen"]

    # Load plugins *before* starting the loop
    find_and_load_plugins(editor_state)

    # Loop indefinitely until we're told to stop
    while True:
        # Draw the current state of the editor on the screen
        show_editor_on_screen(editor_state)

        # Wait for the user to press a key
        key_pressed = -1 # Default value
        try:
            key_pressed = screen.getch() # Get character/key code
        except KeyboardInterrupt: # Handle Ctrl+C as a way to quit
            if editor_state["is_dirty"]:
                confirm = ask_user_for_input(editor_state, "Unsaved changes! Quit anyway? (y/N): ")
                if confirm and confirm.lower() == 'y':
                    break # Exit loop
                else:
                    continue # Go back to waiting for keys
            else:
                break # Exit loop if no unsaved changes
        except curses.error:
            # Ignore other curses errors during getch (like temporary resize issues)
            continue

        # Process the key press. If it returns False, exit the loop.
        if not handle_key_press(editor_state, key_pressed):
            break # Exit the while loop

# --- Starting the Editor ---

def start_editor(screen, filename=None):
    """
    This function is called by curses.wrapper. It sets up the editor state
    and starts the main loop.
    """
    # Basic curses setup
    curses.raw()        # React to keys instantly (don't wait for Enter)
    screen.keypad(True) # Interpret special keys like Arrows, Home, End
    curses.noecho()     # Don't automatically print typed keys on screen
    curses.curs_set(1)  # Show the blinking cursor (0=invisible, 1=normal, 2=very visible)

    # Create the editor's memory (state)
    editor_state = setup_editor_state(screen, filename)

    # Run the main loop
    run_editor_loop(editor_state)

# --- Main execution block (runs when script is executed) ---
if __name__ == "__main__":
    # Get the filename from command line arguments, if provided
    file_to_edit = None
    if len(sys.argv) > 1:
        file_to_edit = sys.argv[1]

    try:
        # curses.wrapper is important!
        # It sets up the terminal nicely for curses, calls our start_editor function,
        # and (crucially) restores the terminal to normal when our function finishes
        # or crashes, preventing a messed-up terminal.
        curses.wrapper(start_editor, file_to_edit)

    except Exception as e:
        # If a totally unexpected error happens outside the wrapper's control
        print("\nOh no! An unexpected error occurred:", file=sys.stderr)
        print(e, file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
