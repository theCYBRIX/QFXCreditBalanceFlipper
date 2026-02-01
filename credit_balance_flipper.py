"""
This module flips the credit balance found in QFX files to be negative
to reflect a debt in financial apps such as Quicken.

Args:
    file_path... (str): The path/s to the .qfx file/s to process.

Flags:
    -p, --pause     Wait for user input before exiting
    -u, --undo      Make credit balance positive in the specified files
    -h, --help      Show help message

This module can be called via the command line, or by dragging and dropping one
or multiple files onto the executable.

Example command line usage:
    .\\credit_balance_flipper.exe ".\\transactions.qfx" ".\\transactions(1).qfx" --pause
"""

import os
import argparse
from colorama import Fore, Style


START_CATEGORY: str = "<LEDGERBAL>"
END_CATEGORY: str = "</LEDGERBAL>"
PROPERTY_NAME: str = "<BALAMT>"


def main():
    """
    Initializes the main logic of the program then waits for user input if required
    """
    args = parse_args()
    success = process_files(args.files, args.undo)
    if args.pause or not success:
        input("Press Enter to continue...")


def parse_args():
    """
    Uses argparse to parse command line arguments
    """

    parser = argparse.ArgumentParser(
        description="Convert credit card balance in .qfx files to a negative value."
    )

    parser.add_argument(
        "files",
        nargs="+",
        type=str,
        help="File/s to process (drag and drop supported)"
    )

    parser.add_argument(
        "-p", "--pause",
        action="store_true",
        help="Wait for user input before exiting"
    )

    parser.add_argument(
        "-u", "--undo",
        action="store_false",
        help="Make credit balance positive in the specified files"
    )

    return parser.parse_args()


def process_files(
        file_paths : list[str], make_balance_negative : bool = True):
    """
    Validates file paths and types and updates the credit balance signage
    in files as specified by make_balance_negative.
    
    Parameters:
        file_paths (list[str]): List of files in which to flip credit balance value
        make_balance_negative: Weather to make credit balance negative (default) or positive
    
    Returns:
        success (bool): Weather all files could be updated/validated successfully
    """

    if not file_paths:
        raise ValueError(
            "No file specified.\nUsage: CreditBalanceFlipper \"filepath\"..."
        )

    for path in file_paths:
        if not os.path.exists(path):
            raise ValueError(
                "Specified file does not exist: "
                + os.path.basename(path)
            )
        if not path.endswith(".qfx"):
            raise ValueError(
                "Specified file does not appear to be in qfx format: "
                + os.path.basename(path)
            )

    success_count: int = 0

    for path in file_paths:
        file_contents: list[str]

        with open(path, "r", encoding="UTF-8") as file:
            file_contents = file.readlines()

        value_found, value_updated = correct_balance(file_contents, make_balance_negative)

        if value_updated:
            with open(path, "w", encoding="UTF-8") as file:
                file.writelines(file_contents)

        if not value_found:
            print(
                f"{Fore.YELLOW}[Warning]{Style.RESET_ALL}" +
                f" Unable to locate value to flip in: \"{os.path.basename(path)}\""
            )
            continue

        success_count += 1

        print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} " +
            (
                "Flipped value"
                if value_updated else
                f"Balance already {"negative" if make_balance_negative else "positive"}"
            )
            + f" in: \"{os.path.basename(path)}\""
        )

    if success_count == len(file_paths):
        print(Fore.GREEN + "Process completed Successfully." + Style.RESET_ALL)
        return True

    print(Fore.GREEN + "Finished. " + Style.RESET_ALL +
            (
                f"No files could be updated. [{success_count}/{len(file_paths)}]"
                if success_count == 0 else
                f"Updated/Validated {success_count} of {len(file_paths)} files successfully."
            )
        )

    return False


def correct_balance(file_contents : list[str], make_negative : bool = True):
    """
    Finds and corrects the credit balance value if needed. 
    
    Parameters:
        file_contents (list[str]): File contents in which to correct the credit balance signage
        make_negative (bool): Weather to make the credit balance negative (default) or positive

    returns:
        value_found (bool): Weather the credit balance could be found
        value_corrected (bool): Weather the credit balance needed to be corrected
    """

    inside_category: bool = False
    value_found: bool = False
    value_flipped: bool = False

    for index, line in enumerate(file_contents):

        if START_CATEGORY in line:
            inside_category = True

        elif PROPERTY_NAME in line and inside_category:
            value_found = True

            value_index: int = line.find(PROPERTY_NAME) + len(PROPERTY_NAME)
            value = line[value_index:].strip()
            as_float = float(value)

            if (as_float > 0 and make_negative) or (as_float < 0 and not make_negative):
                value_flipped = True
                line = line.replace(value, str(
                    (-abs(as_float)) if make_negative else abs(as_float)
                ))
                file_contents[index] = line

            break

        elif END_CATEGORY in line:
            inside_category = False

    return value_found, value_flipped


if __name__ == "__main__":
    main()
