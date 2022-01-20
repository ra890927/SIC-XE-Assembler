from ast import arg
import opcode
from statistics import mode
import sys
from getopt import getopt

class Assembler:
    # init
    def __init__(self) -> None:
        self.__opcode = {}
        self.instruction = []
        self.__opcode_list = []
        self.__directive_list = [
            'START',
            'END',
            'BYTE',
            'WORD',
            'RESW',
            'RESB',
            'BASE',
            'CSECT',
            'EXTDEF',
            'EXTREF',
            'LTORG',
            'EQU',
        ]

        self.__extdef_table = []
        self.__extref_table = []
        self.__symbol_table = {}
        self.__literal_table = []

        self.__init_opcode()
        self.__get_format_list()
    # get opcode list
    def __get_format_list(self) -> None:
        self.__opcode_list = self.__opcode.keys()
    # check mnemonic
    def __check_mnemonic(self, mneonic) -> bool:
        if mneonic[0] == '+':
            return mneonic[1:] in self.__opcode_list
        else:
            return mneonic in self.__opcode_list or mneonic in self.__directive_list
    # check opcode
    def __check_opcode(self, opcode) -> bool:
        return opcode in self.__opcode_list
    # check directive
    def __check_directive(self, directive) -> bool:
        return directive in self.__directive_list
    # get opcode list
    def __init_opcode(self) -> None:
        with open("config/opcode", mode="r") as f:
            for line in f.readlines():
                opcode_arr = list(filter(None, line.split(" ")))
                self.__opcode[opcode_arr[0]] = {
                    "format": opcode_arr[1].split('/'),
                    "code": int(opcode_arr[2].replace("\n", ""), base=16)
                }
    # generate code list
    def __gen_code_list(self, opcode, type, format, offset) -> list:
        # format 4
        if format & 1 == 1:
            return [
                self.__opcode[opcode]['code'] + type,
                format << 4 | ((offset & 0xf0000) >> 16),
                (offset & 0xff00) >> 8,
                offset & 0xff,
            ]
        # format 3
        else:
            return [
                self.__opcode[opcode]['code'] + type,
                format << 4 | ((offset & 0xf00) >> 8),
                offset & 0xff,
            ]
    # read file
    def read_file(self, file_name) -> bool:
        format1_list = ['FIX', 'FLOAT', 'HIO', 'NORM', 'SIO', 'TIO', 'CSECT', 'LTORG']
        format2_list = ['ADDR', 'COMPR', 'DIVR', 'MULR', 'RMO' 'SHIFTL', 'SHIFTR']

        with open(file_name, mode="r") as f:
            for index, line in enumerate(f.readlines()):
                # read line remove ',', '\t', '\n' and split
                line = line.replace(",", " ").replace("\t", " ").replace("\n", "")
                instruction_arr = list(filter(None, line.split(" ")))

                # filter comment and empty line
                if not len(instruction_arr) or instruction_arr[0] == '.':
                    continue

                instruct_set = {}   # define instruction format

                # special process EXTDEF
                if 'EXTDEF' in instruction_arr:
                    if instruction_arr.index('EXTDEF') != 0:
                        print(f'Syntax Error, line {index + 1}: "EXTDEF" can not have symbol')
                        return False
                    
                    instruct_set = {
                        'mnemonic': instruction_arr[0],
                        'operand': instruction_arr[1:],
                    }
                # special process EXTREF
                elif 'EXTREF' in instruction_arr:
                    if instruction_arr.index('EXTREF') != 0:
                        print(f'Syntax Error, line {index + 1}: "EXTREF" can not have symbol')
                        return False
                    
                    instruct_set = {
                        'mnemonic': instruction_arr[0],
                        'operand': instruction_arr[1:],
                    }
                # process length = 4
                elif len(instruction_arr) == 4:
                    if self.__check_mnemonic(instruction_arr[1]):
                        instruct_set = {
                            'symbol': instruction_arr[0],
                            'mnemonic': instruction_arr[1],
                            'operand': instruction_arr[2:],
                        }
                    else:
                        print(f'Syntax Error, line {index + 1}: nonexistent symbol')
                        return False
                # process length = 3
                elif len(instruction_arr) == 3:
                    for mnemonic in format2_list:
                        if mnemonic in instruction_arr:
                            if instruction_arr.index(mnemonic) == 0:
                                instruct_set = {
                                    'mnemonic': instruction_arr[0],
                                    'operand': instruction_arr[1:],
                                }
                                break
                            else:
                                print(f'Syntax Error, line {index + 1}: format error')
                                return False
                    # instruct has set and continue
                    if len(instruct_set):
                        self.instruction.append(instruct_set)
                        continue

                    # X exist
                    if 'X' in instruction_arr:
                        if self.__check_mnemonic(instruction_arr[0]):
                            instruct_set = {
                                'mnemonic': instruction_arr[0],
                                'operand': instruction_arr[1:],
                            }
                    
                    if len(instruct_set):
                        self.instruction.append(instruct_set)
                        continue

                    if self.__check_mnemonic(instruction_arr[1]):
                        instruct_set = {
                            'symbol': instruction_arr[0],
                            'mnemonic': instruction_arr[1],
                            'operand': instruction_arr[2],
                        }
                    else:
                        print(f'Syntax Error, line {index + 1}: nonexistent symbol')
                        return False
                # proces length = 2
                elif len(instruction_arr) == 2:
                    for mnemonic in format1_list:
                        if mnemonic in instruction_arr:
                            if instruction_arr.index(mnemonic) == 1:
                                instruct_set = {
                                    'symbol': instruction_arr[0],
                                    'mnemonic': instruction_arr[1],
                                }
                                break
                            else:
                                print(f'Syntax Error, line {index + 1}: format error')
                                return False
                    # instruct has set and continue
                    if len(instruct_set):
                        self.instruction.append(instruct_set)
                        continue
                    
                    if instruction_arr[0] == 'EQU':
                        print(f'Syntax Error, line {index + 1}: EQU must have symbol')
                        return False
                    elif self.__check_mnemonic(instruction_arr[0]):
                        instruct_set = {
                            'mnemonic': instruction_arr[0],
                            'operand': instruction_arr[1],
                        }
                    else:
                        print(f'Syntax Error, line {index + 1}: nonexistent symbol')
                        return False
                else:
                    if self.__check_mnemonic(instruction_arr[0]):
                        instruct_set = {
                            'mnemonic': instruction_arr[0],
                        }
                    else:
                        print(f'Syntax Error, line {index + 1}: nonexistent symbol')
                        return False

                self.instruction.append(instruct_set)

        return True
    # pass one
    def pass_one(self) -> None:
        cur_block = None        # record current program block
        cur_location = None     # record memory location
        cur_symbol_table = {}   # record current symbol table

        for index, instr in enumerate(self.instruction):
            # add literal
            if 'operand' in instr and instr['operand'][0] == '=':
                if instr['operand'] not in self.__literal_table:
                    self.__literal_table.append(instr['operand'])
            
            # directive operation
            if instr['mnemonic'] == 'START':
                cur_block = instr['symbol']     # update current program block
                cur_symbol_table.clear()        # reset symbol table
                self.__literal_table.clear()    # reset literal table
                cur_location = 0                # for relocation program, start with 0
                instr['location'] = cur_location
            # add extdef symbol
            elif instr['mnemonic'] == 'EXTDEF':
                self.__extdef_table += instr['operand']
            # add extref symbol
            elif instr['mnemonic'] == 'EXTREF':
                self.__extref_table += instr['operand']
            # declare variable
            elif instr['mnemonic'] == 'RESW':
                instr['location'] = cur_location
                cur_location += int(instr['operand']) * 3
            elif instr['mnemonic'] == 'RESB':
                instr['location'] = cur_location
                cur_location += int(instr['operand'])
            # clear literal
            elif instr['mnemonic'] == 'LTORG' or instr['mnemonic'] == 'END':
                it = index  # record next literal position
                for literal in self.__literal_table:
                    it += 1
                    cur_symbol_table[literal] = cur_location
                    # add new instruction at next one
                    self.instruction.insert(it, {
                        'symbol': '*',
                        'mnemonic': literal,
                        'location': cur_location
                    })
                    # compute memory displacement
                    if literal[1] == 'C':
                        cur_location += len(list(literal[3:].split('\''))[0])
                    elif literal[1] == 'X':
                        cur_location += len(list(literal[3:].split('\''))[0]) // 2
                # update symbol table
                if instr['mnemonic'] == 'END':
                    # [notice]: must use copy before reset
                    self.__symbol_table[cur_block] = cur_symbol_table.copy()
                    cur_symbol_table.clear()
                    self.__literal_table.clear()
            # define memory position
            elif instr['mnemonic'] == 'EQU':
                if instr['operand'] == '*':
                    instr['location'] = cur_location
            # reset and use new block
            elif instr['mnemonic'] == 'CSECT':
                cur_location = 0
                instr['location'] = cur_location
                # [notice]: must use copy before reset
                self.__symbol_table[cur_block] = cur_symbol_table.copy()
                cur_block = instr['symbol']
                cur_symbol_table.clear()
            # const variable
            elif instr['mnemonic'] == 'BYTE':
                instr['location'] = cur_location
                # uncertain the number of byte, must be calculated first
                if instr['operand'][0] == 'X':
                    cur_location += len(list(instr['operand'][2:].split('\''))[0]) // 2
                elif instr['operand'][0] == 'C':
                    cur_location += len(list(instr['operand'][2:].split('\''))[0])
            elif instr['mnemonic'] == 'WORD':
                # WORD length must be equal to 3
                instr['location'] = cur_location
                cur_location += 3
            # format 4
            elif instr['mnemonic'][0] == '+':
                instr['location'] = cur_location
                cur_location += 4
            else:
                # skip added literal instrcution and BASE
                if 'symbol' in instr and instr['symbol'] == '*' or instr['mnemonic'] == 'BASE':
                    pass
                else:
                    instr['location'] = cur_location
                    opcode = instr['mnemonic'][1:] if instr['mnemonic'][0] == '+' else instr['mnemonic']
                    format = self.__opcode[opcode]['format'][0]
                    # format 1
                    if format == '1':
                        cur_location += 1
                    # format 2
                    elif format == '2':
                        cur_location += 2
                    # format 3
                    else:
                        cur_location += 3
            # calculate EQU with symbol
            if instr['mnemonic'] == 'EQU':
                # add literal in symbol table
                if instr['operand'] == '*':
                    cur_symbol_table[instr['symbol']] = instr['location']
                elif '-' in instr['operand']:
                    symbol_1, symbol_2 = instr['operand'].split('-')
                    cur_symbol_table[instr['symbol']] = \
                        cur_symbol_table[symbol_1] - \
                        cur_symbol_table[symbol_2]
                elif '+' in instr['operand']:
                    symbol_1, symbol_2 = instr['operand'].split('+')
                    cur_symbol_table[instr['symbol']] = \
                        cur_symbol_table[symbol_1] + \
                        cur_symbol_table[symbol_2]
            # add other symbol in symbol table
            elif 'symbol' in instr and instr['symbol'] != '*':
                cur_symbol_table[instr['symbol']] = instr['location']
    # pass two
    def pass_two(self) -> None:
        b_loc = None        # rocord register BASE
        cur_block = None    # specify current program block
        # these has processed in pass one, skip
        skip_instr = ['EXTDEF', 'EXTREF', 'RESW', 'RESB', 'LTORG', 'EQU', 'END']
        for index, instr in enumerate(self.instruction):
            if instr['mnemonic'] in skip_instr:
                continue
            # update program block
            elif instr['mnemonic'] == 'START':
                cur_block = instr['symbol']
            elif instr['mnemonic'] == 'CSECT':
                cur_block = instr['symbol']
            # update B register content
            elif instr['mnemonic'] == 'BASE':
                b_loc = self.__symbol_table[cur_block][instr['operand']]
            # literal instruction
            elif instr['mnemonic'][0] == '=':
                data = list(instr['mnemonic'][3:].split('\''))[0]
                if instr['mnemonic'][1] == 'C':
                    opcode = []
                    for c in data:
                        opcode.append(ord(c))
                    instr['opcode'] = opcode
                elif instr['mnemonic'][1] == 'X':
                    opcode = []
                    for i in range(0, len(data), 2):
                        opcode.append(int(data[i : i + 2], base=16))
                    instr['opcode'] = opcode
            elif instr['mnemonic'] == 'WORD':
                if '-' in instr['operand']:
                    symbol_1, symbol_2 = instr['operand'].split('-')
                    location_1 = self.__symbol_table[cur_block][symbol_1] \
                        if symbol_1 in self.__symbol_table[cur_block] else 0
                    location_2 = self.__symbol_table[cur_block][symbol_2] \
                        if symbol_2 in self.__symbol_table[cur_block] else 0
                    instr['opcode'] = [
                        ((location_1 - location_2) & (0xff << i)) >> i
                        for i in range(16, -1, -8)
                    ]
                elif '+' in instr['operand']:
                    symbol_1, symbol_2 = instr['operand'].split('+')
                    location_1 = self.__symbol_table[cur_block][symbol_1] \
                        if symbol_1 in self.__symbol_table[cur_block] else 0
                    location_2 = self.__symbol_table[cur_block][symbol_2] \
                        if symbol_2 in self.__symbol_table[cur_block] else 0
                    instr['opcode'] = [
                        ((location_1 + location_2) & (0xff << i)) >> i
                        for i in range(16, -1, -8)
                    ]
                else:
                    data = list(instr['operand'][2:].split('\''))[0]
                    if instr['mnemonic'][0] == 'C':
                        opcode = []
                        for c in data:
                            opcode.append(ord(c))
                        instr['opcode'] = opcode
                    elif instr['mnemonic'][0] == 'X':
                        opcode = []
                        for i in range(0, len(data), 2):
                            opcode.append(int(data[i : i + 2], base=16))
                        instr['opcode'] = opcode
            elif instr['mnemonic'] == 'BYTE':
                data = list(instr['operand'][2:].split('\''))[0]
                if instr['operand'][0] == 'C':
                    opcode = []
                    for c in data:
                        opcode.append(ord(c))
                    instr['opcode'] = opcode
                elif instr['operand'][0] == 'X':
                    opcode = []
                    for i in range(0, len(data), 2):
                        opcode.append(int(data[i : i + 2], base=16))
                    instr['opcode'] = opcode
            else:
                # register coresponding code
                register_cord = {'A': 0, 'X': 1, 'L': 2, 'B': 3, 'S': 4, 'T': 5, 'F': 6,}
                # format 2
                format2_list = ['ADDR', 'CLEAR', 'COMPR', 'DIVR', 'MULR', 'RMO' 'SHIFTL', 'SHIFTR', 'SVC', 'TIXR']
                for mnemonic in format2_list:
                    if instr['mnemonic'] == mnemonic:
                        if len(instr['operand']) == 2:
                            instr['opcode'] = [
                                self.__opcode[mnemonic]['code'],
                                register_cord[instr['operand'][0]] << 4 | register_cord[instr['operand'][1]]
                            ]
                        elif len(instr['operand']) == 1:
                            instr['opcode'] = [
                                self.__opcode[mnemonic]['code'],
                                register_cord[instr['operand'][0]] << 4
                            ]
                if 'opcode' in instr:
                    continue
                elif instr['mnemonic'] == 'RSUB':
                    instr['opcode'] = self.__gen_code_list('RSUB', 3, 0, 0)
                else:
                    # immediate format (n: 0, i: 1)
                    if instr['operand'][0] == '#':
                        token = instr['operand'][1:]
                        # operand is symbol
                        if token in self.__symbol_table[cur_block]:
                            symbol_loc = self.__symbol_table[cur_block][token]
                            offset = symbol_loc - instr['location'] - 3
                            # format 3 (PC)
                            if offset >= -2048 and offset <= 2047:
                                instr['opcode'] = self.__gen_code_list(instr['mnemonic'], 1, 2, offset)
                            else:
                                offset = symbol_loc - b_loc
                                # format 3 (B)
                                if offset >= 0 and offset <= 4095:
                                    instr['opcode'] = self.__gen_code_list(instr['mnemonic'], 1, 4, offset)
                                # format 4
                                else:
                                    instr['opcode'] = self.__gen_code_list(instr['mnemonic'][1:], 1, 1, symbol_loc)
                        # operand is number
                        else:
                            # this does not memory, so do not consider PC and B
                            offset = int(token)
                            # format 4
                            if offset > 4095:
                                instr['opcode'] = self.__gen_code_list(instr['mnemonic'][1:], 1, 1, offset)
                            # format 3
                            else:
                                instr['opcode'] = self.__gen_code_list(instr['mnemonic'], 1, 0, offset)
                    # indirect format (n: 1, i: 0)
                    elif instr['operand'][0] == '@':
                        symbol = instr['operand'][1:]
                        symbol_loc = self.__symbol_table[cur_block][symbol] \
                            if symbol in self.__symbol_table[cur_block] else None
                        # symbol not defined
                        if symbol_loc == None:
                            print(f'Syntax Error, line {index + 1}: symbol not defined')
                            return False
                        else:
                            # calculate offset
                            offset = symbol_loc - instr['location'] - 3
                            # format 3 (PC)
                            if offset >= -2048 and offset <= 2047:
                                instr['opcode'] = self.__gen_code_list(instr['mnemonic'], 2, 2, offset)
                            else:
                                offset = symbol_loc - b_loc
                                # format 3 (B)
                                if offset >= 0 and offset <= 4095:
                                    instr['opcode'] = self.__gen_code_list(instr['mnemonic'], 2, 4, offset)
                                # format 4
                                else:
                                    instr['opcode'] = self.__gen_code_list(instr['mnemonic'], 2, 1, symbol_loc)
                    # direct format (n: 1, i: 1)
                    else:
                        format_num = 0  # x, b, p, e
                        # x label
                        if isinstance(instr['operand'], list) and 'X' in instr['operand']:
                            format_num |= 8
                        # format 4
                        if instr['mnemonic'][0] == '+':
                            format_num |= 1
                            symbol_loc = None
                            mnemonic = instr['mnemonic'][1:]
                            # get first element
                            first_element = instr['operand'][0] if isinstance(instr['operand'], list) else instr['operand']
                            # get symbol location
                            try:
                                symbol_loc = self.__symbol_table[cur_block][first_element]
                            except:
                                symbol_loc = None
                            # symbol nodefined (EXTREF)
                            if symbol_loc == None:
                                # by default, EXTREF memory reference is 0
                                instr['opcode'] = self.__gen_code_list(mnemonic, 3, format_num, 0)
                            else:
                                instr['opcode'] = self.__gen_code_list(mnemonic, 3, format_num, symbol_loc)
                        else:
                            symbol_loc = None
                            # get first element
                            first_element = instr['operand'][0] if isinstance(instr['operand'], list) else instr['operand']
                            # get symbol location
                            try:
                                symbol_loc = self.__symbol_table[cur_block][first_element]
                            except:
                                symbol_loc = None
                            # symbol nodefined (EXTREF)
                            if symbol_loc == None:
                                # by default, EXTREF memory reference is 0
                                instr['opcode'] = self.__gen_code_list(instr['mnemonic'], 3, format_num, 0)
                            else:
                                offset = symbol_loc - instr['location'] - 3
                                # format 3 (PC)
                                if offset >= -2048 and offset <= 2047:
                                    format_num |= 2
                                    instr['opcode'] = self.__gen_code_list(instr['mnemonic'], 3, format_num, offset)
                                # format 3 (B)
                                else:
                                    format_num |= 4
                                    offset = symbol_loc - b_loc
                                    instr['opcode'] = self.__gen_code_list(instr['mnemonic'], 3, format_num, offset)

    def write_file(self, file_name) -> None:
        with open(file_name, mode='w') as f:
            for instr in self.instruction:
                if 'opcode' in instr:
                    opcode_str = ''
                    for opc in instr['opcode']:
                        opcode_str += '{:02X}'.format(opc)
                    f.write(opcode_str + '\n')


if __name__ == "__main__":
    # initial class
    asm = Assembler()
    # get options
    opts, args = getopt(sys.argv[1:], 'o:')
    # default set the output file is output.txt
    file_name = 'output.txt'
    try:
        file_name = [arg for opt, arg in opts if opt == '-o'][0]
    except:
        file_name = 'output.txt'
    # read and parse file
    asm.read_file(args[0])
    # pass one
    asm.pass_one()
    # pass two
    asm.pass_two()
    # write file
    asm.write_file(file_name)