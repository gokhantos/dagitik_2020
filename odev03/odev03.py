import numpy as np
import matplotlib.pyplot as plt

class RSSI():
    def __init__(self):
        self.data = self.read_data()

    def read_data(self):
        sensor_mac = []
        rssi = []
        timestamps = []
        #reading data into arrays
        with open('data/lab8_2.10-2.22-1.52.mbd','r') as f:
            for line in f:
                current_line = line.split(",")
                timestamps.append(float(current_line[0]))
                sensor_mac.append(current_line[1] +", "+ current_line[2])
                rssi.append(int(current_line[3].replace('\n', '')))
            
        #converting arrays to numpy arrays
        timestamps_arr = np.asarray(timestamps)
        rssi_arr = np.asarray(rssi)
        sensor_mac_arr = np.asarray(sensor_mac)
        mac_list = np.unique(sensor_mac_arr)
        
        #creating dictionary with mac addresses and storing rssi values
        data_dict = {}
        for index in range(len(sensor_mac_arr)):
            for mac in mac_list:
                if mac == sensor_mac_arr[index]:
                    data_dict.setdefault(mac, []).append(rssi_arr[index])
        
        #creating dictionary with mac addresses and storing timestamp values
        time_dict = {}
        for index in range(len(sensor_mac_arr)):
            for mac in mac_list:
                if mac == sensor_mac_arr[index]:
                    time_dict.setdefault(mac, []).append(timestamps_arr[index])

        #creating dictionary with mac addresses and storing frequencies
        my_dict = {}
        for mac in mac_list:
            freq_dict = []
            for index in range(len(time_dict[mac])):
                if index < 100:
                    freq_dict.append(time_dict[mac][index])
                else:
                    my_dict.setdefault(mac, []).append((self.formula(freq_dict)))
                    freq_dict.pop(0)
                    freq_dict.append(time_dict[mac][index])

        #updating dictionary
        updated_dict = {}
        for x in data_dict.copy():
            updated_dict.update({x: {'min': min(data_dict[x]), 'max': max(data_dict[x]), 'length': len(data_dict[x]), 'rssi': np.sort(data_dict[x])}})

        #counting rssi values into a dictionary
        rssi_dict = {}
        count_dict = {}
        for mac in mac_list:
            unique_rssi = np.unique(updated_dict[mac]['rssi'])
            count_arr = np.zeros(len(unique_rssi), dtype= int)
            for rssi_value in updated_dict[mac]['rssi']:
                index = np.where(unique_rssi == rssi_value)
                count_arr[index] = count_arr[index] + 1
                count_dict.update({rssi_value: int(count_arr[index])})
            rssi_dict.setdefault(mac, {}).update(count_dict)

        #calculating frequence distribution
        freq_distribution = {}
        count_dict = {}
        for mac in mac_list:
            step_arr = np.linspace(1.5,2.50,21)
            count_arr = np.zeros(len(step_arr), dtype= int)
            for index in range(len(step_arr)):
                for index2 in range(len(my_dict[mac])):
                    if my_dict[mac][index2] > step_arr[index] and my_dict[mac][index2] < step_arr[index+1]:
                        count_arr[index] = count_arr[index] + 1
                        count_dict.update({step_arr[index]: count_arr[index]})
            count_dict = {k: v for k, v in sorted(count_dict.items(), key=lambda item: item[0])}
            freq_distribution.setdefault(mac, {}).update(count_dict)
        
        #updating our dictionary last time
        for x in data_dict.copy():
            updated_dict.update({x: {'min': min(data_dict[x]), 'max': max(data_dict[x]), 'length': len(data_dict[x]), 'rssi': np.sort(data_dict[x]), 'histo': rssi_dict, 'timestamps': np.sort(time_dict[x]), 'frequences': my_dict, 'freq_dist': freq_distribution}})

        return updated_dict

    def formula(self, timestamps):
        w = 100
        freq = w / (timestamps[len(timestamps)-1] - timestamps[len(timestamps)-w])
        return freq

    def plot_histograms(self):
        for data in self.data:
            rssi_count = []
            rssi_value = []
            for rssi in self.data[data]['histo'][data]:
                rssi_value.append(rssi)
                rssi_count.append(self.data[data]['histo'][data][rssi])
            plt.title(data)
            plt.bar(rssi_value, rssi_count)
            plt.show()

    def plot_frequences(self):
        for data in self.data:
            frequences = []
            for freq_val in self.data[data]['frequences'][data]:
                frequences.append(freq_val)
            plt.plot(frequences)
            plt.show()

    def instant_histo(self):
        for data in self.data:
            frequences = []
            freq_count = []
            for freq_val in self.data[data]['freq_dist'][data]:
                frequences.append(str(freq_val))
                freq_count.append(self.data[data]['freq_dist'][data][freq_val])
            plt.bar(frequences, freq_count)
            plt.show()

def main():
    my_rssi = RSSI()
    my_rssi.plot_histograms()
    my_rssi.plot_frequences()
    my_rssi.instant_histo()


if __name__ == "__main__":
    main()