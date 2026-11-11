import sys
import re

def parse_readme(file_path):
    entries = {}
    target_apis = {"Bitquery", "Blockscout", "Chainlink"}
    
    in_blockchain_section = False
    in_code_block = False
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            stripped_line = line.strip()
            
            # Toggle code blocks
            if stripped_line.startswith("```"):
                in_code_block = not in_code_block
                continue
            
            # Detect Blockchain section header (flexible search)
            if "blockchain" in stripped_line.lower() and stripped_line.startswith("##"):
                in_blockchain_section = True
                continue
            elif stripped_line.startswith("## ") and in_blockchain_section:
                # Reached the next section
                break
                
            # Parse table rows inside Blockchain section
            if in_blockchain_section and not in_code_block and stripped_line.startswith("|"):
                parts = [p.strip() for p in stripped_line.split("|")]
                if len(parts) >= 3:
                    api_cell = parts[1]
                    match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", api_cell)
                    if match:
                        name = match.group(1).strip()
                        url = match.group(2).strip()
                        if name in target_apis:
                            entries[name] = {
                                "line_number": line_num,
                                "name": name,
                                "url": url,
                                "description": parts[2],
                                "auth": parts[3] if len(parts) > 3 else "",
                                "https": parts[4] if len(parts) > 4 else "",
                                "cors": parts[5] if len(parts) > 5 else ""
                            }
                            
    return entries

def run_self_test():
    print("Running self-test for R02-T011...")
    try:
        results = parse_readme("README.md")
        print(f"Parsed entries found: {list(results.keys())}")
        
        assert "Bitquery" in results, "Bitquery entry missing!"
        assert "Blockscout" in results, "Blockscout entry missing!"
        assert "Chainlink" in results, "Chainlink entry missing!"
        
        for api, data in results.items():
            assert isinstance(data["line_number"], int) and data["line_number"] > 0, \
                f"Invalid line number for {api}"
                
        print("Self-test passed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"Self-test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        run_self_test()
    else:
        data = parse_readme("README.md")
        for api, info in data.items():
            print(f"{api}: Line {info['line_number']} | URL: {info['url']}")