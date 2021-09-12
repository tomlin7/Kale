import sys
import time

from codeanalysis.Parsing.lexer import Lexer
from codeanalysis.Parsing.parser import Parser
from codeanalysis.Emitting.emitter import Emitter


print("Kale")
text = None

if len(sys.argv) != 2:
    sys.exit("Error: compiler needs input files")
with open(sys.argv[1], 'r') as source_file:
    source = source_file.read()

filename = sys.argv[1].split(".")[0]

lexer   = Lexer(source)
token_list = lexer.lex()
print("--------")
emitter = Emitter(filename)
parser  = Parser(token_list, emitter, debug=True)


# ------------
bar_width = 20
sys.stdout.write("□□" * bar_width)
sys.stdout.flush()
sys.stdout.write("\b" * 2 * (bar_width+1))

for i in range(bar_width):
    time.sleep(0.000000001)
    sys.stdout.write("■■")
    sys.stdout.flush()

sys.stdout.write(" 100%\n")
# ------------


parser.program()
# emitter.output()

print("\nCompilation complete.")

exit(0)
try:
    # emitter.build(filename)
    print("build complete.")
except:
    print("Compiling to executable failed. \nCouldn't find a C compiler. GCC/MSVC should be installed")
