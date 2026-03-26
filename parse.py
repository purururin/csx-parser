import re
import json

def parse_cotopha_script(file_path):
    output = []
    current_scene = "unknown"
    current_label = "start"
    
    # Buffers to track the stack
    string_stack = []
    
    # Regex patterns
    re_load_string = re.compile(r'Load String "(.*?)"')
    re_out_msg = re.compile(r'ExCall "WitchWizard::OutMsg"')
    re_scene_name = re.compile(r'ExCall "WitchWizard::SetCurrentScriptName"')
    re_label = re.compile(r'Enter "(.*?)@')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 1. Track Loaded Strings (Arguments)
            str_match = re_load_string.search(line)
            if str_match:
                string_stack.append(str_match.group(1))
                # Keep stack small to avoid memory issues, only need last few for OutMsg
                if len(string_stack) > 10:
                    string_stack.pop(0)
                continue

            # 2. Track Scene Changes
            if re_scene_name.search(line):
                if string_stack:
                    current_scene = string_stack[-1]
                continue
                
            # 3. Track Labels
            label_match = re_label.search(line)
            if label_match:
                current_label = label_match.group(1)
                continue

            # 4. Handle Dialogues (OutMsg)
            if re_out_msg.search(line):
                # Based on the log, the name is loaded 2nd to last and text is last
                # Or based on <8> args, we look back:
                if len(string_stack) >= 2:
                    dialogue_text = string_stack[-1]
                    char_name = string_stack[-2]
                    
                    # If the name is empty, it's usually narration
                    msg_type = "dialogue" if char_name else "narration"
                    
                    output.append({
                        "scene": f"{current_scene} > {current_label}",
                        "character": char_name,
                        "dialogue": dialogue_text,
                        "type": msg_type
                    })
                continue

            # 5. Handle Choices (Based on Manual Page 135-136)
            # Typically choices in this engine appear as SendCommand or Menu calls
            if 'SendCommand' in line and "ID_CHOICE" in line:
                output.append({
                    "scene": f"{current_scene} > {current_label}",
                    "character": "SYSTEM",
                    "dialogue": string_stack[-1] if string_stack else "Choice Option",
                    "type": "choice"
                })

    return output

# Run the parser
data = parse_cotopha_script('script-RAW.txt')

# Save to JSON
with open('translation_file.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Successfully extracted {len(data)} entries.")