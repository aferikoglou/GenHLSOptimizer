import numpy as np

class Preprocessor():
    """
    Parses input source information and generates directive search spaces 
    for high-level synthesis (HLS) optimization.
    """

    def __init__(self, input_src_info_path):
        """
        Initialize the Preprocessor with the path to the input source info file.

        Args:
            input_src_info_path (str): Path to the file containing source-level HLS metadata.
        """
        self.input_src_info_path = input_src_info_path

        self.n_var = -1
        self.top_level_func = ""
        self.directives = []
        self.xl = None
        self.xu = None

    def _get_var_domains(self, directives):
        """
        Derives the lower and upper bounds (xl, xu) for each variable 
        based on the number of available directives.

        Args:
            directives (list): List of directive options for each design variable.
        """
        directives_len = len(directives)

        # Lower bounds are zero for all variables
        self.xl = np.zeros(directives_len, dtype=int)

        # Upper bounds depend on the number of options for each directive
        xu_list = []

        cnt = 0
        for i in directives:
            length = len(i)
            xu_list.insert(cnt, length - 1)
            cnt += 1

        self.xu = np.asarray(xu_list)
        
    def preprocess(self):
        """
        Main preprocessing method that parses the source info file,
        generates optimization directives per action point (loops/arrays),
        and computes domain boundaries.

        Returns:
            tuple: (n_var, xl, xu, top_level_func, directives)
                - n_var (int): Number of variables (action points).
                - xl (np.array): Lower bounds for each variable.
                - xu (np.array): Upper bounds for each variable.
                - top_level_func (str): Name of the top-level function.
                - directives (list): List of lists containing directive options for each action point.
        """
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

                for i in range(3, parts_len, 2):
                    array_dim = parts[i]
                    size = int(parts[i + 1])

                    if size < 128:  # apply complete partition for small arrays
                        directive = "#pragma HLS array_partition variable=" + array_name + " complete dim=" + array_dim
                        output.insert(cnt, directive)
                        cnt += 1

                    for t in ['block', 'cyclic']:
                        max_factor = 0
                        if size > 128:
                            max_factor = 128
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
