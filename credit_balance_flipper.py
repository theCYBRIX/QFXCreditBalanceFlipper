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
from enum import Enum
from argparse import ArgumentParser, Namespace
from colorama import Fore, Style


TARGET_CATEGORY: str = "<LEDGERBAL>"
END_TARGET_CATEGORY: str = "</LEDGERBAL>"
TARGET_PROPERTY: str = "<BALAMT>"
BYTES_PER_MEBIBYTE : int = 1024 * 1024
MAX_FILE_SIZE: int = 100 * BYTES_PER_MEBIBYTE
"""Arbitrary maximum file size, in bytes. (100 Mebibytes) \n
This was added to avoid freezing the application by accidentally parsing huge files."""


class ParserState(Enum):
    """
    Enum describing the state of the QFX file parser.
    """
    TAG = 0
    VALUE = 1


def main() -> None:
    """
    Initializes the main logic of the program then waits for user input if required.
    """
    args : Namespace = parse_args()
    success : bool = process_files(args.files, args.undo)
    if args.pause or not success:
        input("Press Enter to continue...")


def parse_args() -> Namespace:
    """
    Uses argparse to parse command line arguments.
    """

    parser : ArgumentParser = ArgumentParser(
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
        file_paths : list[str], make_balance_negative : bool = True) -> bool:
    """
    Validates file paths and types and updates the credit balance signage
    in files as specified by make_balance_negative.
    
    Parameters:
        file_paths (list[str]): List of files in which to flip credit balance value.
        make_balance_negative (bool): Weather to make credit balance negative (default)
                                      or positive.
    
    Returns:
        success (bool): Weather all files could be updated/validated successfully.
    """

    validate_files(file_paths)

    success_count: int = 0

    for path in file_paths:
        try:
            file_contents: str

            with open(path, "r", encoding="UTF-8") as file:
                file_contents = file.read()

            file_contents, value_found, value_updated = update_qfx_contents(
                file_contents, make_balance_negative
            )

            if value_updated:
                with open(path, "w", encoding="UTF-8") as file:
                    file.write(file_contents)

            if not value_found:
                print(
                    f"{Fore.YELLOW}[Warning]{Style.RESET_ALL}" +
                    " Unable to locate value to flip in: " +
                    f"\"{os.path.basename(path)}\""
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
        except (SyntaxError, ValueError) as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} " + "\n\t".join(e.args))


    if success_count == len(file_paths):
        print(f"{Fore.GREEN}Process completed Successfully.{Style.RESET_ALL}")
        return True

    print(f"{Fore.GREEN}Finished.{Style.RESET_ALL} " +
            (
                f"No files could be updated. [{success_count}/{len(file_paths)}]"
                if success_count == 0 else
                f"Updated/Validated {success_count} of {len(file_paths)} files successfully."
            )
        )

    return False


def validate_files(file_paths : list[str]) -> None:
    """
    Checks if the specified files exist, are QFX files and are
    not too large to be parsed safely. 
    
    file_paths (list[str]): List of files to validate.
    """
    if not file_paths:
        raise ValueError(
            "No file specified.\nUsage: CreditBalanceFlipper \"filepath\"..."
        )

    errors : int = 0

    for path in file_paths:
        error_msg : str

        if not os.path.exists(path):
            error_msg = "File does not exist"
        elif not path.endswith(".qfx"):
            error_msg = "File does not appear to be in qfx format"
        elif os.path.getsize(path) > MAX_FILE_SIZE:
            error_msg = f"File is too large to process safely \
                ({os.path.getsize(path) * BYTES_PER_MEBIBYTE} Mebibyes)"
        else:
            continue

        errors += 1
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {error_msg}: {os.path.basename(path)}")


    if errors > 0:
        raise ValueError("Unable to process files. Check console output for details.")


def update_qfx_contents(file_contents : str, make_negative : bool = True) -> tuple[str, bool, bool]:
    """
    Finds and corrects the credit balance value/s if needed. 
    
    Parameters:
        file_contents (list[str]): File contents in which to correct the credit balance signage.
        make_negative (bool): Weather to make the credit balance negative (default) or positive.

    Returns:
        results (tuple[bool, bool]):
            [0] updated_contents: The updated file contents. \n
            [1] value_found: Weather the credit balance could be found. \n
            [2] value_corrected: Weather the credit balance needed to be corrected.
    """

    state : ParserState = ParserState.VALUE

    current_tag = ""
    category_stack : list[str] = []
    inside_category : bool = False

    output : list[str] = []
    buffer : list[str] = []

    value_found_count : int = 0
    value_flipped_count : int = 0

    num_chars : int = len(file_contents)
    i : int = 0

    while i < num_chars:
        char : str = file_contents[i]
        i += 1

        if state == ParserState.TAG:
            buffer.append(char)

            if char != ">":
                continue

            tag : str = "".join(buffer)
            buffer.clear()
            output.append(tag)
            tag = tag.strip()

            if tag.startswith("</"):
                closed_category : str = f"<{tag[2:]}".upper()
                if closed_category == current_tag:
                    current_tag = category_stack.pop()

                elif closed_category in category_stack:
                    last_index : int = len(category_stack) - 1 \
                            - category_stack[::-1].index(closed_category)
                    category_stack = category_stack[0:last_index]

                else:
                    for index, category in enumerate(category_stack):
                        category_stack[index] = f"\"{category[1:-1]}\""
                    raise SyntaxError(
                        f"Malformatted QFX file. Found \"{tag}\" \
                            while in category: {" > ".join(category_stack)}"
                    )
            else:
                category_stack.append(current_tag)
                inside_category = current_tag == TARGET_CATEGORY
                current_tag = tag.upper()
                state = ParserState.VALUE

        elif state == ParserState.VALUE:
            if char == "<":
                value_string : str = "".join(buffer)
                buffer.clear()

                if inside_category and current_tag == TARGET_PROPERTY:
                    value_found_count += 1

                    try:
                        value_string, value_flipped = flip_value(value_string, make_negative)
                        if value_flipped:
                            value_flipped_count += 1
                    except ValueError as e:
                        raise SyntaxError(
                            f"Found value but failed flip it. \
                            ({TARGET_CATEGORY[1:-1]} > {TARGET_PROPERTY[1:-1]} > {value_string})"
                        ) from e

                output.append(value_string)
                state = ParserState.TAG

            buffer.append(char)


    output.append("".join(buffer))
    updated_contents : str = file_contents if (value_flipped_count == 0) else "".join(output)

    return updated_contents, (value_found_count >= 1), (value_flipped_count >= 1)


def flip_value(value_string : str, make_negative : bool = True) -> tuple[str, bool]:
    """
    Converts a numeric value in a string to be positive or negative. 
    
    Parameters:
        value_string (str): String in which to correct the signage.
        make_negative (bool): Weather to make the value negative (default) or positive.

    Returns:
        results (tuple[bool, bool]):
            [0] updated_string: The updated string. \n
            [1] value_flipped: Weather the value needed to be flipped.
    """
    trimmed_value : str = value_string.strip()
    as_float : float = float(trimmed_value)
    value_flipped : bool = False

    if (as_float > 0 and make_negative) or (as_float < 0 and not make_negative):
        value_flipped = True
        value_string = value_string.replace(trimmed_value, \
                        str(
                            (-abs(as_float))
                            if make_negative else
                            abs(as_float)
                        )
        )
    return value_string, value_flipped



if __name__ == "__main__":
    main()
