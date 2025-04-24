# plugins/plugin_save.py

# This is a plugin for the Simple Editor.
# It adds the ability to save the file by pressing Ctrl+S.

import os # Needed for checking if a filename is a directory

# --- Global storage for tools from the core editor ---
# We store the functions given to us by the core editor when 'register' is called.
core_tools = {}

# --- The actual save logic ---
def do_save_file(editor_state):
    """
    This function runs when the user presses the save key (Ctrl+S).
    It asks for a filename if needed, and writes the editor content to disk.
    It uses functions provided by the core editor via 'core_tools'.
    """
    # Get necessary tools from our stored dictionary
    ask_user = core_tools.get('ask_user')
    show_message = core_tools.get('show_message')
    get_lines = core_tools.get('get_lines')
    get_filename = core_tools.get('get_filename')
    set_filename = core_tools.get('set_filename')
    mark_as_saved = core_tools.get('mark_as_saved')

    # Check if we got all the tools we need
    if not all([ask_user, show_message, get_lines, get_filename, set_filename, mark_as_saved]):
        # If not, something is wrong - maybe show an error message if possible
        if show_message:
            show_message(editor_state, "Error: Save plugin missing core tools!")
        return # Cannot proceed

    # Get the current filename from the editor's memory
    current_filename = get_filename(editor_state)

    # If the editor doesn't have a filename yet (e.g., new file)
    if not current_filename:
        # Ask the user for a filename
        try:
            filename_from_user = ask_user(editor_state, "Save As: ")
        except Exception as e:
            show_message(editor_state, f"Error asking for filename: {e}")
            return # Stop if asking failed

        # If the user cancelled (e.g., pressed Esc) or entered nothing
        if filename_from_user is None or not filename_from_user.strip():
            show_message(editor_state, "Save cancelled.")
            return # Stop saving

        # Use the filename provided by the user
        current_filename = filename_from_user.strip()

        # Basic check: don't let the user save if the name is a folder
        if os.path.isdir(current_filename):
            show_message(editor_state, f"Error: '{current_filename}' is a folder.")
            # Reset filename in state so it asks again next time
            set_filename(editor_state, None)
            return # Stop saving

        # Tell the editor to remember this new filename
        set_filename(editor_state, current_filename)

    # --- Now we have a filename, let's try to save ---
    try:
        # Get all the lines of text from the editor's memory
        lines_to_save = get_lines(editor_state)

        # Open the file for writing ('w').
        # 'utf-8' is a good standard text encoding.
        # This will overwrite the file if it already exists!
        with open(current_filename, 'w', encoding='utf-8') as f:
            # Write each line from the editor's memory to the file,
            # adding a newline character ('\n') at the end of each.
            for line in lines_to_save:
                f.write(line + '\n')

        # If saving worked, show a success message
        num_lines = len(lines_to_save)
        show_message(editor_state, f"Saved {num_lines} lines to {current_filename}")
        # Mark the file as 'not dirty' (saved) in the editor's memory
        mark_as_saved(editor_state)

    except IOError as e:
        # If there was a problem writing to the file (e.g., permissions denied)
        show_message(editor_state, f"Error saving! Could not write to file: {e}")
    except Exception as e:
        # Catch any other unexpected problems during saving
        show_message(editor_state, f"Error saving! An unexpected error occurred: {e}")


# --- Registration Function (Called by the Core Editor) ---
def register(editor_state, provided_core_tools):
    """
    This function is called by the main editor script when it loads plugins.
    Its job is to tell the core editor about the features this plugin provides.
    """
    global core_tools
    # Store the tools provided by the core editor so 'do_save_file' can use them
    core_tools = provided_core_tools

    # Get the function needed to register a keybinding
    register_key_func = core_tools.get('tell_core_about_key')

    if register_key_func:
        # Tell the core editor: "When the user presses Ctrl+S (key code 19),
        # please run my 'do_save_file' function."
        ctrl_s_key_code = 19
        register_key_func(editor_state, ctrl_s_key_code, do_save_file)
    else:
        # This should not happen if the core editor is working correctly
        print("Error: Save plugin could not find 'tell_core_about_key' tool.", file=sys.stderr)
