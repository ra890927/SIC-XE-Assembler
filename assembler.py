class Assembler:
    def __init__(self) -> None:
        self.opcode = {}
        self.instruction = []

    def init_opcode(self) -> None:
        with open("config/opcode", mode="r") as f:
            for line in f.readlines():
                opcode_arr = list(filter(None, line.split(" ")))
                print(opcode_arr)
                self.opcode[opcode_arr[0]] = {
                    "format": opcode_arr[1].split('/'),
                    "code": int(opcode_arr[2].replace("\n", ""), base=16)
                }

    def read_file(self, file_name) -> None:
        with open(file_name, mode="r") as f:
            for line in f.readlines():
                line = line.replace(",", " ").replace("\t", " ").replace("\n", "")
                instruction_arr = list(filter(None, line.split(" ")))
                # print(instruction_arr)
                if not len(instruction_arr) or instruction_arr[0] == '.':
                    continue
                else:
                    if len(instruction_arr) > 2 \
                        and instruction_arr[0] != "EXTDEF" and instruction_arr[0] != "EXTREF":
                        instruction_arr = instruction_arr[1:] + instruction_arr[0 : 1]
                        self.instruction.append(instruction_arr)
                    else:
                        self.instruction.append(instruction_arr)



    def pass_one(self) -> None:
        pass

    def pass_two(self) -> None:
        pass

if __name__ == "__main__":
    asm = Assembler()
    asm.read_file("test.asm")
    for instruction in asm.instruction:
        print(instruction)