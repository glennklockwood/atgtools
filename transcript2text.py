#!/usr/bin/env python3
#
# Takes the transcript of a Teams meeting (from the docx) and converts it into
# a more concise text file. Useful for feeding a transcript back into Copilot
# for Word.

def transform_text_file(input_file, output_file):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    transformed_lines = []
    last_speaker = None
    current_text = ""

    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        idx += 1
        if '-->' in line:
            # read another line; it is the speaker
            line = lines[idx].strip()
            idx += 1

            this_speaker = line.strip()

            line = lines[idx].strip()
            idx += 1

            if last_speaker is None or this_speaker != last_speaker:
                if current_text:
                    transformed_lines.append(current_text)
                last_speaker = this_speaker
                current_text = f"{this_speaker}: {line}"
            else:
                # if current_text ends in an alphanumeric character, add a space
                if current_text[-1].isalnum():
                    current_text += "."
                current_text += " " + line
        elif line == "":
            continue
        else:
            raise ValueError("Non-standard line: " + line)

    transformed_lines.append(current_text)

    # Write transformed lines to output file
    with open(output_file, 'w') as file:
        for line in transformed_lines:
            file.write(line + "\n")

# Example usage
input_file = "input.txt"
output_file = "output.txt"
transform_text_file(input_file, output_file)
