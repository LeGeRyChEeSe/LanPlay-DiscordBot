import re

def fix_lan_command(content):
    # Pattern for the lan command function
    pattern = r'(@commands\.slash_command\(name=\"lan\"\)\s*\n\s*async def lan_command\(self,\s*inter: disnake\.ApplicationCommandInteraction\):\s*\n)(.*?)(?=@commands\.slash_command|\Z)'
    # We want to capture the entire function body until the next decorator or end of file.
    # We'll use a more specific pattern: match from the decorator to the next decorator or end of file, but we'll do it by processing the file line by line in the function.
    # Instead, we'll do a simpler approach: we know the exact lines we want to replace for the lan command from the previous output.
    # But let's try a regex that matches the function and captures the body.
    # We'll use a regex that matches from the decorator to the line before the next decorator or end of file, but we'll make it non-greedy for the body.
    # Actually, let's split the content by lines and process line by line.
    return content  # placeholder

# Since we are having trouble with regex, let's do a line-by-line processing in a simpler way.
# We'll read the file, split into lines, and then iterate.

with open('src/bot/commands.py', 'r') as f:
    lines = f.readlines()

# We'll look for the lan command decorator and then rebuild the function.
i = 0
while i < len(lines):
    if lines[i].strip() == '@commands.slash_command(name=\"lan\")':
        # Found the lan command decorator.
        # We'll collect the decorator and the next lines until we have the full function.
        # We know the next line should be blank or the function definition.
        # Let's collect until we see a line that is not indented (or another decorator/function at module level).
        start = i
        # Skip the decorator line
        i += 1
        # Skip any blank lines
        while i < len(lines) and lines[i].strip() == '':
            i += 1
        # Now we should be at the function definition line.
        if i < len(lines) and lines[i].strip().startswith('async def lan_command('):
            # We have the function definition.
            # We'll now collect the function body until we see a line that is not empty and has less than 4 leading spaces.
            # But note: we want to include the docstring and the body.
            # We'll collect lines until we see a line that is not empty and has less than 4 leading spaces (meaning it's at the module level).
            # We'll store the lines of the function (from the decorator to the end of the body) in a list.
            func_lines = lines[start:i]  # decorator and definition
            # Now collect the body
            while i < len(lines):
                line = lines[i]
                stripped = line.lstrip()
                if stripped == '':
                    func_lines.append(line)
                    i += 1
                    continue
                # Check if this line starts a decorator or function definition at the module level
                if stripped.startswith('@') or stripped.startswith('async def ') or stripped.startswith('def '):
                    break
                # Check indentation: if the line has less than 4 leading spaces, it's not part of the function body.
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces < 4:
                    break
                func_lines.append(line)
                i += 1
            # Now we have the entire function in func_lines (from decorator to the line before the next function/decorator).
            # We now need to reconstruct the function with the docstring first and then the rate limit check.
            # We'll split func_lines into:
            #   decorator lines (until the function definition)
            #   function definition line
            #   the rest (the body)
            # But note: we already have the decorator and the function definition in func_lines.
            # Let's separate:
            #   The first line is the decorator.
            #   The second line might be blank? We'll skip blank lines until we get to the function definition.
            # Actually, we collected the decorator and then skipped blank lines and then the function definition.
            # So in func_lines, we have:
            #   [0]: decorator line
            #   [1:?]: blank lines (if any)
            #   [last]: function definition line
            # We want to remove the blank lines between the decorator and the function definition.
            # Let's rebuild the function from scratch:
            new_func_lines = []
            # Add the decorator
            new_func_lines.append(lines[start])  # the decorator line
            # Skip blank lines until the function definition
            j = start + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            # Now j should be at the function definition line.
            new_func_lines.append(lines[j])  # the function definition line
            # Now we expect the docstring. We'll look for the docstring in the original body.
            # We'll search for a line that starts with three quotes in the original body (from j+1 to the end of the original function).
            # But note: we have already collected the body in func_lines (from the decorator to the end of the body). We have the function definition at index (j - start) in func_lines? Let's not overcomplicate.
            # Instead, let's take the original body (from j+1 to i-1) and extract the docstring and the rest.
            body_start = j + 1
            body_end = i  # because we stopped at i (the line after the body)
            original_body = lines[body_start:body_end]
            # Now extract the docstring from original_body.
            docstring_lines = []
            rest_of_body = []
            in_docstring = False
            docstring_quote = None
            for k, line in enumerate(original_body):
                stripped = line.strip()
                if not in_docstring:
                    if stripped.startswith('\"\"\"') or stripped.startswith(\"'''\"):
                        in_docstring = True
                        if stripped.startswith('\"\"\"'):
                            docstring_quote = '\"\"\"'
                        else:
                            docstring_quote = \"'''\"
                        docstring_lines.append(line)
                        # Check if the docstring ends on the same line
                        opening_index = line.find(docstring_quote)
                        if opening_index != -1:
                            closing_index = line.find(docstring_quote, opening_index + len(docstring_quote))
                            if closing_index != -1:
                                in_docstring = False
                                rest_of_body = original_body[k+1:]
                                break
                    else:
                        # No docstring, the entire body is rest_of_body
                        rest_of_body = original_body[k:]
                        break
                else:
                    docstring_lines.append(line)
                    if docstring_quote in line:
                        in_docstring = False
                        rest_of_body = original_body[k+1:]
                        break
            if in_docstring:
                docstring_lines = original_body
                rest_of_body = []
            # Now we have the docstring and the rest of the body.
            # Build the new function:
            #   decorator
            #   function definition
            #   docstring_lines
            #   rate limit check
            #   rest_of_body
            new_func_lines.extend(docstring_lines)
            # Add the rate limit check
            new_func_lines.append('        # Rate limit check\n')
            new_func_lines.append('        if not DISCOVERY_RATE_LIMITER.is_allowed(inter.author.id):\n')
            new_func_lines.append('            await inter.response.send_message(\n')
            new_func_lines.append('                \"You are using this command too frequently. Please wait a moment before trying again.\",\n')
            new_func_lines.append('                ephemeral=True\n')
            new_func_lines.append('            )\n')
            new_func_lines.append('            return\n')
            # Add the rest of the body
            new_func_lines.extend(rest_of_body)
            # Now we have the new function lines from the decorator to the end of the body.
            # Replace the old function in the lines list with the new function lines.
            # We need to replace from start to i (exclusive of i) with new_func_lines.
            lines[start:i] = new_func_lines
            # Set i to start + len(new_func_lines) to continue after the new function.
            i = start + len(new_func_lines)
            continue
    i += 1

# Now do the same for the add command.
i = 0
while i < len(lines):
    if lines[i].strip() == '@commands.slash_command(name=\"add\")':
        start = i
        i += 1
        while i < len(lines) and lines[i].strip() == '':
            i += 1
        if i < len(lines) and lines[i].strip().startswith('async def add_server_command('):
            # Collect the function
            func_lines = lines[start:i]  # decorator and definition
            while i < len(lines):
                line = lines[i]
                stripped = line.lstrip()
                if stripped == '':
                    func_lines.append(line)
                    i += 1
                    continue
                if stripped.startswith('@') or stripped.startswith('async def ') or stripped.startswith('def '):
                    break
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces < 4:
                    break
                func_lines.append(line)
                i += 1
            # Now reconstruct the add command.
            new_func_lines = []
            # Add the decorator
            new_func_lines.append(lines[start])
            # Skip blank lines to the function definition
            j = start + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            new_func_lines.append(lines[j])  # function definition
            # Extract the body
            body_start = j + 1
            body_end = i
            original_body = lines[body_start:body_end]
            # Extract docstring and rest of body
            docstring_lines = []
            rest_of_body = []
            in_docstring = False
            docstring_quote = None
            for k, line in enumerate(original_body):
                stripped = line.strip()
                if not in_docstring:
                    if stripped.startswith('\"\"\"') or stripped.startswith(\"'''\"):
                        in_docstring = True
                        if stripped.startswith('\"\"\"'):
                            docstring_quote = '\"\"\"'
                        else:
                            docstring_quote = \"'''\"
                        docstring_lines.append(line)
                        opening_index = line.find(docstring_quote)
                        if opening_index != -1:
                            closing_index = line.find(docstring_quote, opening_index + len(docstring_quote))
                            if closing_index != -1:
                                in_docstring = False
                                rest_of_body = original_body[k+1:]
                                break
                    else:
                        rest_of_body = original_body[k:]
                        break
                else:
                    docstring_lines.append(line)
                    if docstring_quote in line:
                        in_docstring = False
                        rest_of_body = original_body[k+1:]
                        break
            if in_docstring:
                docstring_lines = original_body
                rest_of_body = []
            # Build the new function
            new_func_lines.extend(docstring_lines)
            # Rate limit check for add command
            new_func_lines.append('        # Rate limit check\n')
            new_func_lines.append('        if not ADD_SERVER_RATE_LIMITER.is_allowed(inter.author.id):\n')
            new_func_lines.append('            await inter.response.send_message(\n')
            new_func_lines.append('                \"You are using this command too frequently. Please wait a moment before trying again.\",\n')
            new_func_lines.append('                ephemeral=True\n')
            new_func_lines.append('            )\n')
            new_func_lines.append('            return\n')
            new_func_lines.extend(rest_of_body)
            # Replace the old function
            lines[start:i] = new_func_lines
            i = start + len(new_func_lines)
            continue
    i += 1

# Now write the file back
with open('src/bot/commands.py', 'w') as f:
    f.writelines(lines)

print("File updated.")
