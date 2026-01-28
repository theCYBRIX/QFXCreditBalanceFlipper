import os
import argparse
from colorama import Fore, Style


START_CATEGORY: str = "<LEDGERBAL>"
END_CATEGORY: str = "</LEDGERBAL>"
PROPERTY_NAME: str = "<BALAMT>"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert credit card balance in .qfx files to a negative value."
    )

    parser.add_argument(
        "-p", "--pause",
        action="store_true",
        help="Wait for user input before exiting"
    )

    parser.add_argument(
        "files",
        nargs="+",
        type=str,
        help="File/s to process (drag and drop supported)"
    )

    return parser.parse_args()


def main():
    args = parse_args()
    cmd_line_paths: list[str] = args.files
    pause: bool = args.pause

    if len(cmd_line_paths) == 0:
        raise ValueError(
            "No file specified.\nUsage: CreditBalanceFlipper \"filepath\"...")

    for path in cmd_line_paths:
        if not path.endswith(".qfx"):
            raise ValueError(
                "Specified file does not appear to be in qfx format: " + os.path.basename(path))

    success_count: int = 0

    for path in cmd_line_paths:
        file_path: str = path
        file_contents: list[str]

        with open(file_path, "r", encoding="UTF-8") as file:
            file_contents = file.readlines()

        inside_category: bool = False
        value_found: bool = False
        value_flipped: bool = False

        for i in range(len(file_contents)):
            line: str = file_contents[i]

            if START_CATEGORY in line:
                inside_category = True

            elif PROPERTY_NAME in line and inside_category:
                value_found = True

                value_index: int = line.find(PROPERTY_NAME) + len(PROPERTY_NAME)
                value = line[value_index:].strip()
                as_float = float(value)

                if as_float > 0:
                    value_flipped = True

                line = line.replace(value, str(-abs(as_float)))
                file_contents[i] = line
                break

            elif END_CATEGORY in line:
                inside_category = False

        if not value_found:
            print(Fore.YELLOW + "[Warning]" + Style.RESET_ALL +
                  " Unable to locate value to flip in: \"{}\"".format(os.path.basename(file_path)))
            continue

        success_count += 1

        if value_flipped:
            with open(file_path, "w", encoding="UTF-8") as file:
                file.writelines(file_contents)

        print(Fore.GREEN + "[OK] " + Style.RESET_ALL +
              ("Flipped value" if value_flipped else "Balance already negative") +
              " in: \"{}\"".format(os.path.basename(file_path)))

    if success_count == len(cmd_line_paths):
        print(Fore.GREEN + "Process completed Successfully." + Style.RESET_ALL)
    else:
        print(Fore.GREEN + "Finished." + Style.RESET_ALL +
              (" No files could be updated. [{}/{}]" if success_count == 0 else
               " Updated/Validated {} of {} files successfully.")
              .format(success_count, len(cmd_line_paths))
              )
        pause = True

    if pause:
        input("Press Enter to continue...")


if __name__ == "__main__":
    main()
