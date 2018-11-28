import numpy as np
import matplotlib.pyplot as plt
from ComponentReader import ComponentReader

INPUT_FILE = "TestCases/2/input.txt"
STEP = 0.1
ITERATIONS = 20

# Constants
DST = 3
SRC = 4
VOLTAGE_SOURCE_NUMBER = 5


class Simulator:
    # For resistances: (value, dst, src)
    # For current sources: (is_final, value, initial_value, dst, src))
    # For voltage sources: (is_final, value, initial_value, dst, src, i_number))
    def __init__(self, ip, iterations, step):
        self.input_file = ip
        self.step = step
        self.iterations = iterations

        self.resistances = []
        self.voltage_sources = []
        self.current_sources = []
        self.voltage_sources_types = {}
        self.res = {}  # For saving the final results.

        self.n = 0
        self.m = 0

        # Get components.
        self.get_components()

        # Initialize matrices and vectors.
        self.x = np.zeros((self.n + self.m, 1))
        self.z = np.zeros((self.n + self.m, 1))
        self.a = np.zeros((self.n + self.m, self.n + self.m))
        self.g = np.zeros((self.n, self.n))
        self.b = np.zeros((self.n, self.m))
        self.c = np.zeros((self.m, self.n))
        self.d = np.zeros((self.m, self.m))

        self.get_z(True)
        self.get_a()

    def get_components(self):
        components = ComponentReader.read(input_file=self.input_file, step=self.step)
        self.resistances = components['r']
        self.voltage_sources = components['v']
        self.current_sources = components['c']
        self.n = components['n']
        self.m = components['m']
        self.voltage_sources_types = components['vstype']

    def get_a(self):
        # Get g.
        for r in self.resistances:
            self.g[r[1], r[1]] += r[0]
            self.g[r[2], r[2]] += r[0]
            self.g[r[1], r[2]] += -r[0]
            self.g[r[2], r[1]] += -r[0]

        # Get b and c.
        for vs in self.voltage_sources:
            self.b[vs[3], vs[5]] = 1
            self.b[vs[4], vs[5]] = -1
        self.c = np.transpose(self.b)

        # Get d.
        for vs in self.voltage_sources:
            if vs[0]:
                continue
            self.d[vs[5], vs[5]] = - vs[1]

        self.a[0:self.n, 0:self.n] = self.g
        self.a[0:self.n, self.n:self.n + self.m] = self.b
        self.a[self.n:self.n + self.m, 0:self.n] = self.c
        self.a[self.n:self.n + self.m, self.n:self.n + self.m] = self.d

    def get_z(self, is_init):
        self.z = np.zeros((self.n + self.m, 1))
        for cs in self.current_sources:
            if cs[0]:  # Is final.
                self.z[cs[DST]] += cs[1]
                self.z[cs[SRC]] += -cs[1]
            else:
                if is_init:
                    self.z[cs[DST]] += cs[1] * cs[2]
                    self.z[cs[SRC]] -= cs[1] * cs[2]
                else:
                    self.z[cs[DST]] += cs[1] * (self.x[cs[DST]] - self.x[cs[SRC]])
                    self.z[cs[SRC]] -= cs[1] * (self.x[cs[DST]] - self.x[cs[SRC]])

        for vs in self.voltage_sources:
            if vs[0]:  # Is final.
                self.z[vs[VOLTAGE_SOURCE_NUMBER] + self.n] += vs[1]
            else:
                if is_init:
                    self.z[vs[VOLTAGE_SOURCE_NUMBER] + self.n] += vs[1] * - vs[2]
                else:
                    dst = self.x[vs[VOLTAGE_SOURCE_NUMBER] + self.n]
                    if vs[DST] == 0:
                        dst = 0
                    self.z[vs[VOLTAGE_SOURCE_NUMBER] + self.n] -= vs[1] * dst

    def simulate(self):
        for i in range(1, self.n + self.m + 1):
            self.res[i] = []

        for i in range(self.iterations):
            a = self.a[1:, 1:]
            z = self.z[1:]
            x = np.matmul(np.linalg.inv(a), z)

            self.x[1:] = x

            # Saving the output.
            j = 1
            for el in x:
                self.res[j].append(el)
                j += 1

            # Update z.
            self.get_z(False)

        # Print Results.
        self.print()

        # Plot Table and WaveForms
        self.plot()

    def print(self):
        # Print Volts for each node
        for i in range(1, self.n):
            s = self.step
            print('V' + str(i))
            for el in self.res[i]:
                if round(s * 10) % 10 == 0:
                    print("%.0f" % s, "%.10f" % el[0])
                else:
                    print("%.1f" % s, "%.10f" % el[0])
                s += self.step
            print('')
        # Print Currents for each voltage source.
        for i in range(self.n, self.n + self.m):
            s = self.step
            print('I' + self.voltage_sources_types[i - self.n])
            for el in self.res[i]:
                if round(s * 10) % 10 == 0:
                    print("%.0f" % s, "%.10f" % el[0])
                else:
                    print("%.1f" % s, "%.10f" % el[0])
                s += self.step
            print('')

    def plot(self):
        # Prepare data for plotting.
        table_headers = ['Time']
        data = np.zeros((self.iterations, self.x.shape[0]))

        for i in range(1, self.n):
            table_headers.append('V' + str(i))
            data[:, i] = ["%.10f" % el[0] for el in self.res[i]]
        for i in range(self.n, self.x.shape[0]):
            table_headers.append('I' + self.voltage_sources_types[i - self.n])
            data[:, i] = ["%.10f" % el[0] for el in self.res[i]]

        s = self.step
        for i in range(self.iterations):
            data[i, 0] = "%.1f" % s
            s += self.step

        # Plot Table.
        plt.figure(self.n + self.m + 1)
        ax = plt.subplot(111, frame_on=False)
        the_table = plt.table(cellText=data,
                              colLabels=table_headers, loc="upper center")

        # Wave Forms.
        for i in range(data.shape[1] - 1):
            plt.figure(i)
            plt.plot(data[:, 0], data[:, i + 1])
            if i + 1 < self.n:
                plt.title('V' + str(i + 1))
            else:
                plt.title('I' + self.voltage_sources_types[i + 1 - self.n])
        plt.show()


simulator = Simulator(INPUT_FILE, ITERATIONS, STEP)
simulator.simulate()
