import numpy as np


class ComponentReader:
    @staticmethod
    def read(input_file, step):
        resistances = []
        voltage_sources = []
        current_sources = []
        voltage_sources_types = {}
        vsrc_counter = 0  # Used in printing the component current result
        i_vsrc_counter = 0  # Used in printing the component current result
        v_number = 0  # Used as a counter for voltage sources.
        n = 0
        m = 0
        l = 0

        with open(input_file, "r") as lines:
            for line in lines:
                line = line.replace("\n", "")
                line = line.lower()

                # Get component data.
                component = line.split(" ")
                component_type = component[0]
                component_dst = int(component[1])
                component_src = int(component[2])
                component_value = float(component[3])
                component_initial_value = float(component[4])

                n = np.max((n, component_dst, component_src))

                # For resistances: (value, dst, src)
                # For current sources: (is_final, value, initial_value, dst, src))
                # For voltage sources: (is_final, value, initial_value, dst, src, v_number))
                if component_type == 'r':
                    resistances.append((1 / component_value, component_dst, component_src))

                elif component_type == 'vsrc':
                    voltage_sources.append(
                        (True, component_value, component_initial_value, component_dst, component_src, v_number))
                    voltage_sources_types[v_number] = 'vsrc'
                    if v_number > 0:
                        voltage_sources_types[v_number] += str(vsrc_counter)
                    vsrc_counter += 1
                    v_number += 1
                    m += 1

                elif component_type == 'isrc':
                    current_sources.append(
                        (True, component_value, component_initial_value, component_dst, component_src))

                elif component_type == 'c':  # Convert it to current source and resistance.
                    # Resistance.
                    resistance_value = component_value / step
                    resistances.append((resistance_value, component_dst, component_src))
                    # Current source.
                    current_sources.append(
                        (False, component_value / step, component_initial_value, component_dst, component_src))

                elif component_type == 'i':  # Convert it to voltage source.
                    # Voltage source.
                    voltage_sources.append(
                        (
                            False, component_value / step, component_initial_value, component_dst, component_src,
                            v_number))
                    voltage_sources_types[v_number] = '_L' + str(i_vsrc_counter)
                    i_vsrc_counter += 1
                    v_number += 1
                    l += 1

        return {'r': resistances, 'v': voltage_sources, 'c': current_sources, 'n': n + 1,  # +1 for node zero
                'm': m + l, 'vstype': voltage_sources_types}
