#!/usr/bin/env python

# https://pypi.org/project/simple-term-menu/
from simple_term_menu import TerminalMenu
import subprocess


def list_profiles():
    profiles = subprocess.check_output(["aws", "configure", "list-profiles"])


def main():
    options = ["[1] entry ABC", "[2] entry DEF", "[3] entry GHI"]
    terminal_menu = TerminalMenu(options, title="Choose an option")
    menu_entry_index = terminal_menu.show()

    print(f"You have selected {options[menu_entry_index]}!")
    subprocess.call("aws ecs execute-command ...", shell=True)


if __name__ == "__main__":
    main()
