print("running main.py")

import matplotlib.pyplot as plt


from files import load_edf, example_file_path

signals = load_edf(example_file_path)
signal = signals['C3']



# plt.subplot(2, 1, 2)
plt.plot(signal.data, 'b-', label='data')
plt.xlabel('T')
plt.grid()
plt.legend()

# plt.subplots_adjust(hspace=0.35)
plt.show()