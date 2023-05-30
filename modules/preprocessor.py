import numpy as np

class Preprocessor():
    def __init__(self, input_src_info_path):
        self.input_src_info_path = input_src_info_path

        self.n_var = -1
        self.top_level_func = ""
        self.directives = []
        self.xl = None
        self.xu = None

    def _get_var_domains(self, directives):
        # xl generation
        directives_len = len(directives)

        self.xl = np.zeros(directives_len, dtype=int)

        # xu generation
        xu_list = []

        cnt = 0
        for i in directives:
            length = len(i)
            xu_list.insert(cnt, length - 1)
            cnt += 1

        self.xu = np.asarray(xu_list)
        
    def preprocess(self):
        f = open(self.input_src_info_path, 'r')
        lines = f.readlines()

        lines_num = len(lines)
        self.n_var = lines_num - 1
        self.top_level_func = lines[0].strip('\n').strip('\t')

        action_point_cnt = 0
        for i in range(1, lines_num):
            stripped_line = lines[i].strip('\n').strip('\t')
            parts = stripped_line.split(',')
            parts_len = len(parts)
            
            # Get the type of the action point
            action_point_type = parts[1]

            output = []
            cnt = 0
            if action_point_type == "loop":
                loop_iter = int(parts[2])

                ############################
                # Generate loop directives #
                ############################

                # PIPELINE
                directive = "#pragma HLS pipeline"
                output.insert(cnt, directive)
                cnt += 1

                directive = "#pragma HLS pipeline II=1"
                output.insert(cnt, directive)
                cnt += 1

                if loop_iter != -1:
                    # UNROLL
                    max_factor = 0
                    if loop_iter <= 64:
                        max_factor = loop_iter / 2 if (loop_iter % 2 == 0) else (loop_iter / 2) - 1

                        directive = "#pragma HLS unroll"
                        output.insert(cnt, directive)
                        cnt += 1
                    else:
                        max_factor = 64

                    factor = 2
                    while (factor <= max_factor):
                        directive = "#pragma HLS unroll factor=" + str(factor)
                        output.insert(cnt, directive)
                        cnt += 1

                        factor *= 2

            elif action_point_type == "array":
                array_name = parts[2]

                #############################
                # Generate array directives #
                #############################

                for i in range(3, parts_len, 2):
                    array_dim = parts[i]
                    size = int(parts[i + 1])

                    if size < 128: # 1024
                        directive = "#pragma HLS array_partition variable=" + array_name + " complete dim=" + array_dim
                        output.insert(cnt, directive)
                        cnt += 1

                    for t in ['block', 'cyclic']:
                        max_factor = 0
                        if size > 128: # 1024
                            max_factor = 128 # 1024
                        else:
                            max_factor = size / 2 if (size % 2 == 0) else (size / 2) - 1

                        factor = 2
                        while (factor <= max_factor):
                            directive = "#pragma HLS array_partition variable=" + array_name + " " + t + " factor=" + str(factor) + " dim=" + array_dim
                            output.insert(cnt, directive)
                            cnt += 1

                            factor *= 2

            self.directives.insert(action_point_cnt, output)
            action_point_cnt += 1

        f.close()

        self._get_var_domains(self.directives)

        return(self.n_var, self.xl, self.xu, self.top_level_func, self.directives)
