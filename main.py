#!/usr/bin/env python3
import os
import shutil
import zipfile
import argparse
from pathlib import Path
import re
import csv
import mimetypes

def load_codes(codes_files):
    """Load codes from the CSV codes file into a dictionary."""
    
    codes = {}
    for codes_file in codes_files:
        with open(codes_file, 'r', newline='') as f:
            reader = csv.reader(f)
            for line in reader:
                if len(line) >= 4:
                    # Extract components
                    board, level, general_subject, detailed_subject, master_code, *codes_list = line
                    
                    # Normalize master code
                    master_code = master_code.strip().upper()
                    
                    if master_code:
                        codes_list.append(master_code)  # Append master code to the list
                    
                    # Add each code to the dictionary with board-specific keys
                    for code in codes_list:
                        code = code.strip().upper()

                        if code:  # Ignore empty codes
                            unique_key = f"{board.strip()}_{code}"  # Ensure uniqueness by appending board name
                            
                            # Check if the key already exists and append to the list of codes
                            if unique_key in codes:
                                codes[unique_key]["codes"].append(code)
                            else:
                                codes[unique_key] = {
                                    "board": board.strip(),
                                    "level": level.strip(),
                                    "general_subject": general_subject.strip(),
                                    "detailed_subject": detailed_subject.strip(),
                                    "master_code": master_code.strip() if master_code else None,
                                    "codes": [code]  # Initialize with the current code
                                }
                else:
                    if line:
                        print(f"Skipping incorrect line: {line}")
                continue
                
    return codes

def create_pattern(items, delimiter="|"):
    return delimiter.join(items)

months = ["j", "m", "s", "w", "y"]
types = ["qp", "sp", "ms", "sm", "in", "pm", "gt", "er", "ab", "ci", "sc", "ir", "ss", "sf", "sy", "su", "gd", "fq"]

edexcel = {
    "types":  ["que", "msc", "mcs", "rms", "pef"],
}

types_pattern = create_pattern(types)
edexcel_types_pattern = create_pattern(edexcel["types"])
months_pattern = create_pattern(months)

def is_valid_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type is not None

def parse_board(board, human=True):
    board = str(board).lower()
    board_map = {
        'Cambridge': ['cie', 'caie'],
        'Edexcel': ['edx', 'edex']
    }

    # Normalize type_map to allow bidirectional lookup
    abbreviation_map = {abbr: full for full, abbrs in board_map.items() for abbr in abbrs}

    # Convert abbreviation to human-readable or vice versa
    if human:
        # Check if the input is an abbreviation
        if board in abbreviation_map:
            return abbreviation_map[board]  # Return the full name if abbreviation matches
        # If it's not an abbreviation, check if it's a full name
        for full_name in board_map:
            if board == full_name.lower():
                return full_name  # Return full name if matches
        return None  # Return None if no match is found
    else:
        for full_name, abbrs in board_map.items():
            if board == full_name.lower() or board in abbrs:
                return abbrs[0]  # Return the first abbreviation
    return None

def parse_pattern(file_path):
    """
    Parse the file name to extract board, code, month, year, type, paper number, and variant.
    Returns a dictionary with the extracted details or None if no match is found.
    """
    patterns = [
        {
            "pattern_number": 1,
            "board": "Cambridge",
            "regex": rf"^([a-z0-9]+)?(?:[-_]+)?([0-9]{{4}})[-_]+({months_pattern})([0-9]{{2}})[-_]+({types_pattern})(?:[-_]+)?([0-9]+)?(?:.*)?$",
            "fields": ["board", "code", "month", "year", "type_str", "paper"]
        },
        {
            "pattern_number": 2,
            "board": "Edexcel",
            "regex": rf"^([a-z0-9]+)[-_]+([a-z0-9]+)[-_]+({edexcel_types_pattern})[-_]+([0-9]+)(?:.*)?$",
            "fields": ["code", "paper", "type_str", "date"]
        },
        {
            "pattern_number": 3,
            "board": "Edexcel",
            "regex": r"^(mark.*|question.*|examiner.*)[-_]+(?:paper|unit)([a-z0-9]+)[-_(]+?([a-z0-9]+)[-_)]+?(?:[-_(]+?legacy[-_)]+?|[-_]?paper[a-z0-9]+)?[-_]+([a-z]+)([0-9]{4})(?:.*)?$",
            "fields": ["type_str", "paper", "code", "month", "year"]
        },
    ]

    
    file_path = Path(file_path)
    file_name = file_path.name.lower()

    if args.fuzzy:
        if "jan" in file_name:
            month="January"
        elif "feb" in file_name or "mar" in file_name:
            month="Feb-March"
        elif "may" in file_name or "jun" in file_name:
            month="May-June"
        elif "oct" in file_name or "nov" in file_name:
            month="Oct-Nov"

    for pattern in patterns:
        regex = pattern["regex"]
        match = re.match(regex, file_name)
        if match:
            pattern_number = pattern["pattern_number"]
            groups = match.groups()
            
            extracted_values = {field: groups[i].upper() if field in ["code", "paper"] else groups[i] for i, field in enumerate(pattern["fields"]) if i < len(groups) and field and groups[i]}
            
            if extracted_values.get("board"):
                board = extracted_values.get("board")
            else:
                board = pattern["board"]

            if board:
                board = parse_board(board)
            else:
                print("Skipping, board does not exist")
                return None

            paper = extracted_values.get("paper")
            if paper:
                if paper.startswith("0"): 
                    number, variant = paper[1], "0"
                elif len(paper) == 1:
                    number, variant = paper, "0"
                elif paper[-1].lower() == "r":
                    number, variant = paper[:-1], "R"
                elif len(paper) == 2 and paper.isdigit():
                    number, variant = paper[0], paper[1]
                else:
                    number, variant = paper, "0"
            else:
                number, variant = None, None
           
            date = extracted_values.get("date")
            if date and len(date) >= 8:
                year = date[:4]
                month = date[4:6]
            else:
                year = extracted_values.get("year")
                month = extracted_values.get("month")

            type_str = parse_type(extracted_values.get("type_str"))
            month, year = parse_date(month, year, type_str, board, pattern_number)
            code = extracted_values.get("code")
            
            name = f"{board}_{code}"
            if name in codes:
                details = codes[name]
            else:
                print(f"Code {name} not found in codes, skipping")
                return None


            level, general_subject, detailed_subject, master_code = (details.get(key) for key in ["level", "general_subject", "detailed_subject", "master_code"])

            if not code or not board or not level or not general_subject or not month or not year:
                print(f"Skipping: {file_path}, missing details")
                return None

            return general_subject, detailed_subject, board, level, master_code, code, type_str, number, variant, year, month, pattern_number, regex
    
    return None

def parse_date(month, year, type_str, board, pattern):
    year = parse_year(year)
    if not year or not isinstance(year, int):
        print(f"Invalid year: {year}")
        return None, None

    month = parse_month(month)
    if board == "Edexcel" and pattern == 2:
        if type_str == "Mark Scheme" or type_str == "Examiner Report":
            if month == "January":
                month = "Oct-Nov"
                year = year - 1 
            elif month == "Feb-March":
                month = "January"
            elif month == "Oct-Nov":
                month = "May-June"

    return month, year

def parse_type(type_str, human=True):
    """Convert type abbreviations to standardized names and vice versa."""
    type_str = str(type_str).lower()
    
    type_map = {
        'Question Paper': ['qp', 'que', 'questionpaper', 'question paper', 'examiner-paper', 'examination-paper', 'sp', 'specimen', 'specimen question paper', 'specimen paper'],
        'Mark Scheme': ['ms', 'msc', 'mcs', 'rms', 'markscheme', 'mark scheme', 'mark-scheme', 'sm', 'specimen mark scheme'],
        'Inserts': ['in', 'insert', 'inserts'],
        'Pre-release Materials': ['pm', 'pre-release', 'prerelease'],
        'Grade Thresholds': ['gt', 'grade threshold', 'grade thresholds'],
        'Examiner Report': ['er', 'pef', 'examinerreport', 'examinerreports', 'examiner report', 'examiner reports'],
        'Answer Booklet': ['ab', 'answer', 'answers', 'booklet', 'formula', 'formula sheet', 'sheet'],
        'Confidential Instructions': ['ci', 'sc', 'ir', 'confidential instructions', 'specimen confidential instructions'],
        'Support Files': ['sf', 'ss'],
        'Syllabus': ['sy', 'su', 'tu'],
        'Grade Descriptions': ['gd'],
        'Frequently Asked Questions': ['fq']
    }

    # Normalize type_map to allow bidirectional lookup
    abbreviation_map = {abbr: full for full, abbrs in type_map.items() for abbr in abbrs}

    # Convert abbreviation to human-readable or vice versa
    if human:
        # Check if the input is an abbreviation
        if type_str in abbreviation_map:
            return abbreviation_map[type_str]  # Return the full name if abbreviation matches
        # If it's not an abbreviation, check if it's a full name
        for full_name in type_map:
            if type_str == full_name.lower():
                return full_name  # Return full name if matches
        return None  # Return None if no match is found
    else:
        for full_name, abbrs in type_map.items():
            if type_str == full_name.lower() or type_str in abbrs:
                return abbrs[0]  # Return the first abbreviation

    return None
    
def parse_month(month, human=True):
    """Convert month abbreviations or numbers into session format and vice versa."""
    month = str(month).lower()
    
    if month.isdigit():
        month = month.zfill(2)  # Ensure 2-digit format for numbers

    # Define the mapping
    month_map = {
        'January': ['j', '01', 'jan', 'january'],
        'Feb-March': ['m', '02', '03', 'feb', 'february', 'mar', 'march'],
        'May-June': ['s', '04', '05', '06', '07', '08', 'apr', 'april', 'may', 'jun', 'june', 'aug', 'august', 'summer'],
        'Oct-Nov': ['w', '09', '10', '11', '12', 'sept', 'september', 'oct', 'october', 'nov', 'dec', 'december', 'winter'],
        'Specimen': ['y', 'sp', 'spec', 'specimen']
    }

    # Reverse the mapping for easy lookup in both directions
    abbreviation_map = {abbr: full for full, abbrs in month_map.items() for abbr in abbrs}

    if human:
        # Check if the input is an abbreviation
        if month in abbreviation_map:
            return abbreviation_map[month]  # Return the full name if abbreviation matches
        # If it's not an abbreviation, check if it's a full name
        for full_name in month_map:
            if month == full_name.lower():
                return full_name  # Return full name if matches
        return None  # Return None if no match is found
    else:
        for full_name, abbrs in month_map.items():
            if month == full_name.lower() or month in abbrs:  # If it's a full name
                return abbrs[0]  # Return the first abbreviation
    return None

def parse_year(year, short=False):
    """Adjust 2-digit year to 4 digits."""
    year = str(year).strip()

    if not year.isdigit():
        print(f"Invalid input: no year provided")
        return None  # Return None if the year is not a number

    if short:
        return year[-2:]  # Return the last 2 digits of the year
    else:
        return int(f"20{year[-2:]}" if len(year) == 2 else year)  # Convert to 4 digits if necessary

def unzip_rm_file(zip_file, target_dir, file_name):
    """Unzip a file into the target directory without moving the zip file, then deletes the original file."""
    try:
        # Create the folder for the zip file
        extracted_folder = Path(target_dir) / file_name
        extracted_folder.mkdir(parents=True, exist_ok=True)

        # Extract the contents of the zip file
        if args.dry_run:
            print(f"Would extract {zip_file} to {extracted_folder}")
        else:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_files = zip_ref.namelist()
                for zip_file_name in zip_files:
                    target_file = extracted_folder / zip_file_name
                    if target_file.exists():
                        print(f"File {target_file} already exists, skipping extraction")
                    else:
                        zip_ref.extract(zip_file_name, extracted_folder)
                        print(f"Extracted {zip_file_name} to {extracted_folder}")
            # Delete the original zip file
            if not args.copy:
                zip_file.unlink()  # Deletes the file
                if args.verbose:
                    print(f"Deleted original zip file: {zip_file}")
            
            return extracted_folder
    except Exception as e:
        print(f"Error extracting {zip_file}: {e}")
        return None

def normalize_file(file_path, board, type_str, number, variant, year, month, code, human=False, short=True):
    file_name = Path(file_path.name)

    code = code.lower()
    board_short = parse_board(board, human).lower()
    type_str = parse_type(type_str, human).lower()
    month = parse_month(month, human).lower()
    year = parse_year(year, short).lower()

    if file_name and board_short:
        if code and month and year and type_str and number and variant:
            file_name = f"{board_short}_{code}_{month}{year}_{type_str}_{number}{variant}{file_name.suffix}"
        elif code and month and year and type_str and number:
            file_name = f"{board_short}_{code}_{month}{year}_{type_str}_{number}{file_name.suffix}"
        elif code and month and year and type_str:
            file_name = f"{board_short}_{code}_{month}{year}_{type_str}{file_name.suffix}"
        elif code and year and type_str:
            file_name = f"{board_short}_{code}_{year}_{type_str}{file_name.suffix}"
        elif code and year:
            file_name = f"{board_short}_{code}_{year}{file_name.suffix}"
        else:
            print(f"Error normalizing file {file_path}: missing details")
            return None
    else:
        print(f"Error normalizing file {file_path}: missing details")
        return None

    file_path = Path(file_path.parent / file_name)
    return file_path

def process_file(file_path, output_dir, files):
    """Process a single file."""
    try:
        *details, pattern = parse_pattern(file_path)
        if details:

            general_subject, detailed_subject, board, level, master_code, code, type_str, number, variant, year, month, pattern_number = [ item if item is not None else None for item in details ]            
            year = str(year)

            if args.verbose:
                print(f"File path: {file_path}")
                print(f"File details: {details}")
            if args.output_pattern:
                print(f"Pattern details: {pattern}")

            main_dir = Path(output_dir) / board / level / general_subject

            if detailed_subject:
                if master_code:
                    main_dir = main_dir / f"{detailed_subject} ({master_code})"
                else:
                    main_dir = main_dir / f"{detailed_subject}"

            if args.fuzzy and not type_str:
                file_path_lower = file_path.parent.lower()

                if "syllabus" in file_path_lower:
                    type_str = "Syllabus"
                elif "notes" in file_path_lower or "resources" in file_path_lower:
                    type_str = "Notes"


            if type_str == "Syllabus":
                target_dir = main_dir / "Syllabus"
            elif type_str == "Notes":
                target_dir = main_dir / "Notes"
            elif type_str:
                target_dir = main_dir / year / f"{month} {year}"

            modified_file_path = normalize_file(file_path, board, type_str, number, variant, year, month, code)
            modified_file_name = modified_file_path.name 

            target_file = target_dir / modified_file_name

            if target_file in files:
                print(f"Skipping: {file_path}, already processed")
                return None
            else:
                files.append(target_file)

            if not is_valid_type(file_path):
                print(f"Error handling file {file_path}: file is not valid")
                return None

            # Check if it's a dry run
            if args.dry_run:
                if not args.quiet: 
                    if file_path.suffix == ".zip":
                        print(f"Would unzip {file_path} to {target_file}")
                    elif args.copy:
                        print(f"Would copy {file_path} to {target_file}")
                    else:
                        print(f"Would move {file_path} to {target_file}")
            else:
                if os.path.exists(target_file):
                    print(f"Skipping: {file_path}, already exists at {target_file}")
                    return None
                # Create the target directory structure
                target_dir.mkdir(parents=True, exist_ok=True)

                # Handle zip files separately
                if file_path.suffix == ".zip":
                    unzip_rm_file(file_path, target_dir, modified_file_name)
                else:
                    if args.copy:
                        if not args.quiet:
                            print(f"Copying {file_path} to {target_file}")
                        shutil.copy(file_path, target_file)
                    else:
                        if not args.quiet:
                            print(f"Moving {file_path} to {target_file}")
                        shutil.move(file_path, target_file)

        else:
            if args.verbose:
                print(f"Skipping: {file_path}, no matching details")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    global args
    global codes

    parser = argparse.ArgumentParser(description="A custom-built tool to sort IGCSE past paper files.")
    parser.add_argument("paths", nargs='+', help="paths to files or directories to process")
    parser.add_argument("-o", "--output", required=True, help="directory to store sorted files")
    parser.add_argument("-c", "--codes", nargs='+', required=True, help="files containing board codes")
    parser.add_argument("-r", "--recursive", action="store_true", help="index files recursively")
    parser.add_argument("-n", "--dry-run", action="store_true", help="show what would happen without making changes")
    parser.add_argument("-v", "--verbose", action="store_true", help="print detailed information")
    parser.add_argument("-q", "--quiet", action="store_true", help="output only errors")
    parser.add_argument("-C", "--copy", action="store_true", help="copy instead of moving files")
    parser.add_argument("-P", "--output-pattern", action="store_true", help="output the pattern being matched")
    parser.add_argument("-F", "--fuzzy", action="store_true", help="find data using fuzzy matching if pattern matching fails")

    args = parser.parse_args()

    # Load the codes
    codes = load_codes(args.codes)

    # Prepare an array for files
    files = []

    # Add each file to the array
    for path in args.paths:
        path = Path(path)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            if args.recursive:
                for file in path.rglob("*"):
                    files.append(file)
            else:
                for file in path.glob("*"):
                    files.append(file)

    # Filter out unwanted files if directory is a match for the pattern
    filtered_files = [
        file for file in files
        if file.is_file() and not any(parse_pattern(str(parent)) for parent in Path(file).parents)
    ]

    # Process the remaining files
    processed_files = []
    for file in filtered_files:
        process_file(file, args.output, processed_files)

if __name__ == "__main__":
    main()