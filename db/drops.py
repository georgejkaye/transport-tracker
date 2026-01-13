import re
import sys

with open(sys.argv[1]) as f:
    text = f.read()

text_line = text.replace("\n", " ")
statements = text_line.split(";")

create_function_regex = r"CREATE\s+FUNCTION\s+([A-z_]+)"

for statement in statements:
    result = re.search(create_function_regex, statement)
    if result is not None and result.group(1):
        print(f"DROP FUNCTION IF EXISTS {result.group(1)} CASCADE;")

print()

create_domain_regex = r"CREATE\s+DOMAIN\s+([A-z_]+)"

for statement in statements:
    result = re.search(create_domain_regex, statement)
    if result is not None and result.group(1):
        print(f"DROP DOMAIN IF EXISTS {result.group(1)} CASCADE;")

print()

create_type_regex = r"CREATE\s+TYPE\s+([A-z_]+)"

for statement in statements:
    result = re.search(create_type_regex, statement)
    if result is not None and result.group(1):
        print(f"DROP TYPE IF EXISTS {result.group(1)} CASCADE;")
