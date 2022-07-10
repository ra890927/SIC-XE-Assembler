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

        self.__extdef_table = {}
        self.__extref_table = {}
        self.__symbol_table = {}
        self.__modified_record = {}
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
    def read_file(self, file_name) -> None:
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
                        raise SyntaxError(f'line {index + 1}: "EXTDEF can not have symbol"')
                    
                    instruct_set = {
                        'mnemonic': instruction_arr[0],
                        'operand': instruction_arr[1:],
                    }
                # special process EXTREF
                elif 'EXTREF' in instruction_arr:
                    if instruction_arr.index('EXTREF') != 0:
                        raise SyntaxError(f'line {index + 1}: "EXTREF can not have symbol"')
                    
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
                        raise SyntaxError(f'line {index + 1}: nonexistent symbol')
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
                                raise SyntaxError(f'line {index + 1}: format error')
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
                        raise SyntaxError(f'line {index + 1}: nonexistent symbol')
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
                                raise SyntaxError(f'line {index + 1}: format error')
                    # instruct has set and continue
                    if len(instruct_set):
                        self.instruction.append(instruct_set)
                        continue
                    
                    if instruction_arr[0] == 'EQU':
                        raise SyntaxError(f'line {index + 1}: EQU must have symbol')
                    elif self.__check_mnemonic(instruction_arr[0]):
                        instruct_set = {
                            'mnemonic': instruction_arr[0],
                            'operand': instruction_arr[1],
                        }
                    else:
                        raise SyntaxError(f'line {index + 1}: nonexistent symbol')
                else:
                    if self.__check_mnemonic(instruction_arr[0]):
                        instruct_set = {
                            'mnemonic': instruction_arr[0],
                        }
                    else:
                        raise SyntaxError(f'line {index + 1}: nonexistent symbol')

                self.instruction.append(instruct_set)
    
    # pass one
    def pass_one(self) -> None:
        cur_block = None        # record current program block
        cur_location = None     # record memory location
        cur_symbol_table = {}   # record current symbol table
        cur_extref_table = []   # record current extref table

        for index, instr in enumerate(self.instruction):
            # add literal
            if 'operand' in instr and instr['operand'][0] == '=':
                if instr['operand'] not in self.__literal_table:
                    self.__literal_table.append(instr['operand'])
            
            # directive operation
            if instr['mnemonic'] == 'START':
                cur_block = instr['symbol']     # update current program block
                cur_symbol_table.clear()        # reset symbol table
                cur_extref_table.clear()        # reset extref table
                self.__literal_table.clear()    # reset literal table
                self.__extdef_table.clear()     # reset extdef table
                self.__extref_table.clear()     # reset extref table
                cur_location = 0                # for relocation program, start with 0
                instr['location'] = cur_location
                self.__extdef_table[cur_block] = {}     # init dict
            # add extdef symbol
            elif instr['mnemonic'] == 'EXTDEF':
                for ext_def in instr['operand']:
                    self.__extdef_table[cur_block][ext_def] = None
            # add extref symbol
            elif instr['mnemonic'] == 'EXTREF':
                cur_extref_table += instr['operand']
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
                self.__literal_table.clear()
                # update symbol table
                if instr['mnemonic'] == 'END':
                    # [notice]: must use copy before reset
                    self.__symbol_table[cur_block] = cur_symbol_table.copy()
                    self.__extref_table[cur_block] = cur_extref_table.copy()
                    cur_symbol_table.clear()
                    cur_extref_table.clear()
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
                self.__extref_table[cur_block] = cur_extref_table.copy()
                cur_block = instr['symbol']
                self.__extdef_table[cur_block] = {}
                self.__extref_table[cur_block] = []
                cur_symbol_table.clear()
                cur_extref_table.clear()
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

            if 'symbol' in instr:
                if instr['symbol'] in self.__extdef_table[cur_block]:
                    self.__extdef_table[cur_block][instr['symbol']] = instr['location']
            
    # pass two
    def pass_two(self) -> None:
        b_loc = None            # rocord register BASE
        cur_block = None        # specify current program block
        cur_modified_list = []  # record current program block M records
        # these has processed in pass one, skip
        skip_instr = ['EXTDEF', 'EXTREF', 'RESW', 'RESB', 'LTORG', 'EQU']
        for index, instr in enumerate(self.instruction):
            if instr['mnemonic'] in skip_instr:
                continue
            # update program block
            elif instr['mnemonic'] == 'START':
                cur_block = instr['symbol']
                cur_modified_list = []
            elif instr['mnemonic'] == 'END':
                self.__modified_record[cur_block] = cur_modified_list.copy()
                cur_modified_list.clear()
            elif instr['mnemonic'] == 'CSECT':
                # update program block M records
                self.__modified_record[cur_block] = cur_modified_list.copy()
                cur_modified_list.clear()
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
                    if location_1 == 0:
                        cur_modified_list.append({
                            'location': instr['location'],
                            'byte': 6,
                            'offset': '+' + symbol_1,
                        })
                    location_2 = self.__symbol_table[cur_block][symbol_2] \
                        if symbol_2 in self.__symbol_table[cur_block] else 0
                    if location_2 == 0:
                        cur_modified_list.append({
                            'location': instr['location'],
                            'byte': 6,
                            'offset': '-' + symbol_2,
                        })
                    instr['opcode'] = [
                        ((location_1 - location_2) & (0xff << i)) >> i
                        for i in range(16, -1, -8)
                    ]
                elif '+' in instr['operand']:
                    symbol_1, symbol_2 = instr['operand'].split('+')
                    location_1 = self.__symbol_table[cur_block][symbol_1] \
                        if symbol_1 in self.__symbol_table[cur_block] else 0
                    if location_1 == 0:
                        cur_modified_list.append({
                            'location': instr['location'],
                            'byte': 6,
                            'offset': '+' + symbol_1,
                        })
                    location_2 = self.__symbol_table[cur_block][symbol_2] \
                        if symbol_2 in self.__symbol_table[cur_block] else 0
                    if location_2 == 0:
                        cur_modified_list.append({
                            'location': instr['location'],
                            'byte': 6,
                            'offset': '+' + symbol_2,
                        })
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
                            raise SyntaxError(f'line {index + 1}: symbol has not been defined')
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
                                cur_modified_list.append({
                                    'location': instr['location'] + 1,
                                    'byte': 5,
                                    'offset': '+' + first_element,
                                })
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
        
    # write file
    def write_file(self, file_name) -> None:
        # record program block length and start position
        cur_block = {}
        cur_opcode_list = []
        cur_position_list = []
        program_info = {}
        end_position = ()

        def gen_extref_str(ext_info: list) -> str:
            ext_str = 'R'
            for label in ext_info:
                ext_str += '{:<6s}'.format(label)
            return ext_str.strip()

        def gen_extdef_str(ext_info: dict) -> str:
            ext_str = 'D'
            for label, value in ext_info.items():
                ext_str += '{:<6s}{:06X}'.format(label, value)
            return ext_str.strip()

        def gen_modified_list(modified_info: list) -> list:
            modified_list = []
            for info in modified_info:
                modified_str = 'M{:06X}{:02X}{:<7s}'.format(
                    info['location'], info['byte'], info['offset'])
                modified_list.append(modified_str.strip())
            return modified_list

        def gen_block_info(symbol_info: dict) -> dict:
            block_info = {
                'name': symbol_info['symbol'],
                'length': 0,
                'start': instr['location'],
            }

            extdef_info = self.__extdef_table[symbol_info['symbol']]
            if extdef_info:
                block_info['extdef'] = gen_extdef_str(extdef_info)
            else:
                block_info['extdef'] = ''

            extref_info = self.__extref_table[symbol_info['symbol']]
            if extref_info:
                block_info['extref'] = gen_extref_str(extref_info)
            else:
                block_info['extref'] = ''

            modified_info = self.__modified_record[symbol_info['symbol']]
            if modified_info:
                block_info['modified'] = gen_modified_list(modified_info)
            else:
                block_info['modified'] = []

            return block_info

        for instr in self.instruction:
            if instr['mnemonic'] == 'START':
                cur_opcode_list.clear()
                cur_position_list.clear()
                cur_block = gen_block_info(instr)                
            elif instr['mnemonic'] == 'CSECT':
                name = cur_block['name']
                del cur_block['name']
                program_info[name] = cur_block
                
                # merge this block opcode
                program_info[name]['opcode'] = {}
                for index, pos in enumerate(cur_position_list):
                    program_info[name]['opcode'][pos] = cur_opcode_list[index]
                
                # define new block info
                cur_opcode_list.clear()
                cur_position_list.clear()
                cur_block = gen_block_info(instr)
            elif instr['mnemonic'] == 'END':
                name = cur_block['name']
                del cur_block['name']
                program_info[name] = cur_block

                # merge this block opcode
                program_info[name]['opcode'] = {}
                for index, pos in enumerate(cur_position_list):
                    program_info[name]['opcode'][pos] = cur_opcode_list[index]

                # END symbol will record start code position
                for block in self.__symbol_table.keys():
                    if instr['operand'] in self.__symbol_table[block]:
                        end_position = (block, self.__symbol_table[block][instr['operand']])
            elif 'location' in instr:
                length = instr['location']
                if 'opcode' in instr:
                    length += len(instr['opcode'])
                cur_block['length'] = max(cur_block['length'], length)
            if 'opcode' in instr:
                opcode_str = ''
                for opc in instr['opcode']:
                    opcode_str += '{:02X}'.format(opc)
                instr['opcode'] = opcode_str

                if len(cur_opcode_list):
                    if len(cur_opcode_list[-1]) + len(opcode_str) // 2 > 60:
                        cur_position_list.append(instr['location'])
                        cur_opcode_list.append(opcode_str)
                    else:
                        cur_opcode_list[-1] += opcode_str
                else:
                    cur_position_list.append(instr['location'])
                    cur_opcode_list.append(opcode_str)

        with open(file_name, mode = 'w') as f:
            for symbol, info in program_info.items():
                # header
                f.write('H{:<6s}{:06X}{:06X}\n'.format(
                    symbol, info['start'], info['length']
                ))

                # external define
                if info['extdef']:
                    f.write(info['extdef'] + '\n')
                
                # external reference
                if info['extref']:
                    f.write(info['extref'] + '\n')
                
                # opcode
                for offset, content in info['opcode'].items():
                    f.write('T{:06X}{:02X}{}\n'.format(offset, len(content) // 2, content))

                # modified record
                for modified in info['modified']:
                    f.write(modified + '\n')

                # END record
                if symbol == end_position[0]:
                    f.write('E{:06X}\n'.format(end_position[1]))
                else:
                    f.write('E\n')
                
                f.write('\n')

    def execute(self, read_file, write_file) -> None:
        self.read_file(read_file)
        self.pass_one()
        self.pass_two()
        self.write_file(write_file)

OPTION_CONFIG = ['-o', '-a']

if __name__ == "__main__":
    # initial class
    asm = Assembler()
    # get options
    sorted_opt = []
    temp_opt = None
    # sort and classify option
    for opt in sys.argv[1:]:
        if temp_opt != None:
            sorted_opt = [temp_opt, opt] + sorted_opt
            temp_opt = None
        elif opt in OPTION_CONFIG:
            temp_opt = opt
        else:
            sorted_opt.append(opt)

    opts, args = getopt(sorted_opt, 'a:o:')
    
    read_file = args[0]
    # default set the output file is output.txt
    write_file = 'output.txt'
    try:
        write_file = [arg for opt, arg in opts if opt == '-o'][0]
    except:
        write_file = 'output.txt'

    asm.execute(read_file, write_file)
    